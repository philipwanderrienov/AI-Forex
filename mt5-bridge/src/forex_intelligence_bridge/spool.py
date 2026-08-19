"""Bounded, durable FIFO spool for validated MT5 envelopes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class SpoolFullError(RuntimeError):
    """Raised instead of silently deleting market data when the spool is full."""


class EnvelopeSpool:
    def __init__(self, directory: Path, max_items: int = 10_000) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        self._directory = directory
        self._max_items = max_items
        self._directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def enqueue(self, envelope: dict[str, Any]) -> Path:
        items = self.items()
        if len(items) >= self._max_items:
            raise SpoolFullError("bridge spool capacity reached")

        batch_id = envelope["batchId"]
        destination = self._directory / f"{batch_id}.json"
        data = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

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
        def replay_order(path: Path) -> tuple[int, str]:
            with path.open(encoding="utf-8") as spool_file:
                envelope = json.load(spool_file)
            return int(envelope["sequence"]), str(envelope["batchId"])

        return sorted(self._directory.glob("*.json"), key=replay_order)

    def peek(self) -> tuple[Path, dict[str, Any]] | None:
        items = self.items()
        if not items:
            return None
        path = items[0]
        with path.open(encoding="utf-8") as spool_file:
            return path, json.load(spool_file)

    def acknowledge(self, path: Path) -> None:
        resolved_directory = self._directory.resolve()
        resolved_path = path.resolve()
        if resolved_path.parent != resolved_directory or resolved_path.suffix != ".json":
            raise ValueError("path is outside the spool")
        resolved_path.unlink()
