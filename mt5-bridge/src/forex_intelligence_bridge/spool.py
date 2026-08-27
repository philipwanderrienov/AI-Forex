"""Bounded, durable FIFO spool for validated MT5 envelopes."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

DEFAULT_MAX_BYTES = 256 * 1024 * 1024


class SpoolFullError(RuntimeError):
    """Raised instead of silently deleting market data when the spool is full."""


class DuplicateBatchError(ValueError):
    """Raised when an existing batch ID is reused with different content."""


class SequenceConflictError(ValueError):
    """Raised when a source reuses a pending sequence for different content."""


@dataclass(frozen=True)
class EnqueueResult:
    """Describe whether enqueue created a new durable item or found an exact retry."""

    path: Path
    duplicate: bool


class EnvelopeSpool:
    """Bounded durable queue with quarantine for unreplayable envelopes."""

    def __init__(
        self,
        directory: Path,
        max_items: int = 10_000,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self._directory = directory
        self._quarantine_directory = directory / "quarantine"
        self._max_items = max_items
        self._max_bytes = max_bytes
        self._lock = RLock()
        self._directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._quarantine_directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def enqueue(self, envelope: dict[str, Any]) -> Path:
        """Enqueue an envelope and return its durable path.

        Call ``enqueue_with_result`` when the caller must distinguish a newly
        stored envelope from an idempotent retry.
        """

        return self.enqueue_with_result(envelope).path

    def enqueue_with_result(self, envelope: dict[str, Any]) -> EnqueueResult:
        """Atomically enqueue an envelope and report exact duplicate retries."""

        batch_id = envelope["batchId"]
        destination = self._directory / f"{batch_id}.json"
        data = self._canonical_json(envelope)
        data_size = len(data.encode("utf-8"))

        with self._lock:
            items = self.items()

            if destination.exists():
                try:
                    existing = self._read(destination)
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    self._quarantine_unlocked(destination, "corrupt_spool_entry", str(error))
                else:
                    if self._canonical_json(existing) == data:
                        return EnqueueResult(destination, duplicate=True)
                    raise DuplicateBatchError("batch ID already exists with different content")

            source_instance_id = str(envelope["sourceInstanceId"])
            sequence = int(envelope["sequence"])
            for path in items:
                existing = self._read(path)
                if (
                    str(existing.get("sourceInstanceId")) == source_instance_id
                    and int(existing.get("sequence", -1)) == sequence
                ):
                    raise SequenceConflictError("source sequence already exists in spool")

            items = self.items()
            used_bytes = self._used_bytes(items)
            if len(items) >= self._max_items or used_bytes + data_size > self._max_bytes:
                raise SpoolFullError("bridge spool capacity reached")

            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="x",
                    encoding="utf-8",
                    dir=self._directory,
                    prefix=".pending-",
                    delete=False,
                ) as spool_file:
                    temporary = Path(spool_file.name)
                    os.chmod(temporary, 0o600)
                    spool_file.write(data)
                    spool_file.flush()
                    os.fsync(spool_file.fileno())
                os.link(temporary, destination)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

        return EnqueueResult(destination, duplicate=False)

    def items(self) -> list[Path]:
        """Return healthy pending items in source/sequence/batch replay order.

        Corrupt files are moved to quarantine so one bad entry cannot block the
        entire FIFO after a crash, partial write, or manual file modification.
        """

        healthy: list[tuple[tuple[str, int, str], Path]] = []
        with self._lock:
            for path in list(self._directory.glob("*.json")):
                try:
                    envelope = self._read(path)
                    replay_order = (
                        str(envelope["sourceInstanceId"]),
                        int(envelope["sequence"]),
                        str(envelope["batchId"]),
                    )
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                    self._quarantine_unlocked(path, "corrupt_spool_entry", str(error))
                    continue
                healthy.append((replay_order, path))
            return [path for _, path in sorted(healthy, key=lambda item: item[0])]

    def status(self) -> dict[str, float | int | str]:
        """Return capacity and quarantine counters safe for health reporting."""

        with self._lock:
            items = self.items()
            depth = len(items)
            used_bytes = self._used_bytes(items)
            disk_free_bytes = shutil.disk_usage(self._directory).free
            quarantine_depth = len(list(self._quarantine_directory.glob("*.json"))) // 2
            return {
                "status": (
                    "FULL"
                    if depth >= self._max_items or used_bytes >= self._max_bytes
                    else "AVAILABLE"
                ),
                "depth": depth,
                "capacity": self._max_items,
                "usedBytes": used_bytes,
                "maxBytes": self._max_bytes,
                "utilizationPercent": round((used_bytes / self._max_bytes) * 100, 4),
                "diskFreeBytes": disk_free_bytes,
                "quarantineDepth": quarantine_depth,
            }

    def peek(self) -> tuple[Path, dict[str, Any]] | None:
        """Return the oldest healthy envelope without removing it."""

        items = self.items()
        if not items:
            return None
        path = items[0]
        return path, self._read(path)

    def acknowledge(self, path: Path) -> None:
        """Delete one item only after downstream acknowledgement."""

        with self._lock:
            resolved_path = self._validate_pending_path(path)
            resolved_path.unlink()

    def quarantine(self, path: Path, reason: str, detail: str = "") -> Path:
        """Move an unreplayable pending item aside with durable diagnostic metadata."""

        if not reason.strip():
            raise ValueError("quarantine reason must not be empty")
        with self._lock:
            resolved_path = self._validate_pending_path(path)
            return self._quarantine_unlocked(resolved_path, reason, detail)

    def quarantined_items(self) -> list[Path]:
        """Return quarantined payload files, excluding their metadata sidecars."""

        with self._lock:
            return sorted(
                path
                for path in self._quarantine_directory.glob("*.json")
                if not path.name.endswith(".meta.json")
            )

    def _quarantine_unlocked(self, path: Path, reason: str, detail: str) -> Path:
        if not path.exists():
            raise FileNotFoundError(path)
        unique = time.time_ns()
        destination = self._quarantine_directory / f"{path.stem}-{unique}.json"
        metadata_path = self._quarantine_directory / f"{path.stem}-{unique}.meta.json"
        os.replace(path, destination)
        metadata = {
            "originalName": path.name,
            "reason": reason,
            "detail": detail[:2048],
            "quarantinedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        with metadata_path.open("x", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            metadata_file.flush()
            os.fsync(metadata_file.fileno())
        return destination

    def _validate_pending_path(self, path: Path) -> Path:
        resolved_directory = self._directory.resolve()
        resolved_path = path.resolve()
        if resolved_path.parent != resolved_directory or resolved_path.suffix != ".json":
            raise ValueError("path is outside the spool")
        return resolved_path

    @staticmethod
    def _canonical_json(envelope: dict[str, Any]) -> str:
        return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as spool_file:
            payload = json.load(spool_file)
        if not isinstance(payload, dict):
            raise ValueError("invalid spool envelope")
        return payload

    @staticmethod
    def _used_bytes(items: list[Path]) -> int:
        return sum(path.stat().st_size for path in items)
