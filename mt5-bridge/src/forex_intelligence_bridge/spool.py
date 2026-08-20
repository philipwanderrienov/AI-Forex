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
        data = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        data_size = len(data.encode("utf-8"))

        with self._lock:
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
            except FileExistsError as error:
                raise ValueError("batch already exists in spool") from error
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

        return destination

    def items(self) -> list[Path]:
        """Daftar item spool dalam urutan replay sequence lalu batch ID."""

        def replay_order(path: Path) -> tuple[int, str]:
            with path.open(encoding="utf-8") as spool_file:
                envelope = json.load(spool_file)
            return int(envelope["sequence"]), str(envelope["batchId"])

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
        with path.open(encoding="utf-8") as spool_file:
            return path, json.load(spool_file)

    def acknowledge(self, path: Path) -> None:
        """Hapus item spool yang telah berhasil diproses oleh pemanggil."""

        with self._lock:
            resolved_directory = self._directory.resolve()
            resolved_path = path.resolve()
            if resolved_path.parent != resolved_directory or resolved_path.suffix != ".json":
                raise ValueError("path is outside the spool")
            resolved_path.unlink()

    @staticmethod
    def _used_bytes(items: list[Path]) -> int:
        return sum(path.stat().st_size for path in items)
