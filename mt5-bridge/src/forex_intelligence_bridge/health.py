"""Thread-safe runtime health state for the local MT5 bridge."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from threading import Lock
from typing import Any

HEARTBEAT_WARNING_SECONDS = 10.0
HEARTBEAT_STALE_SECONDS = 20.0


class HeartbeatMonitor:
    """Catat heartbeat terakhir dan hitung freshness terminal/EA.

    Waktu monotonic dipakai untuk menghitung usia agar perubahan jam sistem tidak
    membuat heartbeat tiba-tiba tampak lebih tua atau lebih muda. Lock diperlukan
    karena ``ThreadingHTTPServer`` dapat membaca dan menulis state secara paralel.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = Lock()
        self._last_received_monotonic: float | None = None
        self._source_instance_id: str | None = None
        self._source_sent_at: str | None = None
        self._bridge_received_at: str | None = None

    def record(self, heartbeat: dict[str, Any]) -> None:
        """Simpan identitas dan waktu heartbeat valid terbaru."""

        with self._lock:
            self._last_received_monotonic = self._clock()
            self._source_instance_id = heartbeat["sourceInstanceId"]
            self._source_sent_at = heartbeat["sentAt"]
            self._bridge_received_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def snapshot(self) -> dict[str, Any]:
        """Kembalikan status terkini tanpa mengekspos state internal yang mutable."""

        with self._lock:
            if self._last_received_monotonic is None:
                return {"status": "UNKNOWN"}

            age_seconds = max(0.0, self._clock() - self._last_received_monotonic)
            if age_seconds <= HEARTBEAT_WARNING_SECONDS:
                status = "HEALTHY"
            elif age_seconds <= HEARTBEAT_STALE_SECONDS:
                status = "WARNING"
            else:
                status = "STALE"

            return {
                "status": status,
                "ageSeconds": round(age_seconds, 3),
                "sourceInstanceId": self._source_instance_id,
                "sourceSentAt": self._source_sent_at,
                "bridgeReceivedAt": self._bridge_received_at,
            }
