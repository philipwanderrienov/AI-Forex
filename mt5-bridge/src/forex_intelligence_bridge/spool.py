"""Bounded, durable FIFO spool for validated MT5 envelopes."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
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


class EnvelopeSpool:
    """Antrean file FIFO terbatas untuk envelope yang menunggu dipublikasikan."""

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
        self._max_items = max_items
        self._max_bytes = max_bytes
        self._lock = RLock()
        self._directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def enqueue(self, envelope: dict[str, Any]) -> Path:
        batch_id = envelope["batchId"]
        destination = self._directory / f"{batch_id}.json"
        data = self._canonical_json(envelope)
        data_size = len(data.encode("utf-8"))

        with self._lock:
            items = self.items()

            if destination.exists():
                existing = self._read(destination)
                if self._canonical_json(existing) == data:
                    return destination
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

        return destination

    def items(self) -> list[Path]:
        """Daftar item spool dalam urutan source, sequence, lalu batch ID."""

        def replay_order(path: Path) -> tuple[str, int, str]:
            envelope = self._read(path)
            return (
                str(envelope["sourceInstanceId"]),
                int(envelope["sequence"]),
                str(envelope["batchId"]),
            )

        with self._lock:
            return sorted(self._directory.glob("*.json"), key=replay_order)

    def status(self) -> dict[str, float | int | str]:
        """Ringkasan kapasitas spool yang aman ditampilkan melalui health check."""

        with self._lock:
            items = self.items()
            depth = len(items)
            used_bytes = self._used_bytes(items)
            disk_free_bytes = shutil.disk_usage(self._directory).free
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
            }

    def peek(self) -> tuple[Path, dict[str, Any]] | None:
        """Lihat envelope pertama tanpa menghapusnya dari antrean."""

        items = self.items()
        if not items:
            return None
        path = items[0]
        return path, self._read(path)

    def acknowledge(self, path: Path) -> None:
        """Hapus item spool yang telah berhasil diproses oleh pemanggil."""

        with self._lock:
            resolved_directory = self._directory.resolve()
            resolved_path = path.resolve()
            if resolved_path.parent != resolved_directory or resolved_path.suffix != ".json":
                raise ValueError("path is outside the spool")
            resolved_path.unlink()

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
