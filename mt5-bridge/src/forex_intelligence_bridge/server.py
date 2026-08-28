"""Local HTTP receiver used by the read-only MQL5 exporter."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from forex_intelligence_bridge.contracts import (
    ContractValidationError,
    validate_candle_envelope,
    validate_heartbeat,
)
from forex_intelligence_bridge.health import HeartbeatMonitor
from forex_intelligence_bridge.observability import configure_logging, get_logger
from forex_intelligence_bridge.publisher import BackendPublisher, PublishDisposition, SpoolReplayer
from forex_intelligence_bridge.spool import (
    DEFAULT_MAX_BYTES,
    DuplicateBatchError,
    EnvelopeSpool,
    SequenceConflictError,
    SpoolFullError,
)

MAX_BODY_BYTES = 64 * 1024
LOGGER = get_logger("forex_intelligence_bridge.server")


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """Accept health checks and bounded MT5 heartbeat payloads."""

    server_version = "ForexIntelligenceBridge/0.1"
    protocol_version = "HTTP/1.1"
    spool: EnvelopeSpool | None = None
    heartbeat_monitor = HeartbeatMonitor()

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/health":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "status": "HEALTHY",
                "terminal": self.heartbeat_monitor.snapshot(),
                "spool": self.spool.status() if self.spool is not None else {"status": "UNAVAILABLE"},
            },
        )

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/v1/mt5/envelopes":
            self._receive_envelope()
            return

        if self.path != "/v1/mt5/heartbeat":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        content_length = self._content_length()
        if content_length is None:
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            LOGGER.warning("heartbeat_rejected", extra={"reason": "invalid_json"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        try:
            heartbeat = validate_heartbeat(payload)
        except ContractValidationError as error:
            LOGGER.warning("heartbeat_rejected", extra={"reason": error.code})
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": error.code})
            return

        self.heartbeat_monitor.record(heartbeat)
        LOGGER.info(
            "heartbeat_accepted",
            extra={
                "sourceInstanceId": heartbeat.get("sourceInstanceId"),
                "terminalConnected": heartbeat.get("terminalConnected"),
            },
        )
        self._send_json(HTTPStatus.ACCEPTED, {"status": "accepted"})

    def _receive_envelope(self) -> None:
        content_length = self._content_length()
        if content_length is None:
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            LOGGER.warning("envelope_rejected", extra={"reason": "invalid_json"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        try:
            envelope = validate_candle_envelope(payload)
        except ContractValidationError as error:
            LOGGER.warning("envelope_rejected", extra={"reason": error.code})
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": error.code})
            return

        if self.spool is None:
            LOGGER.error("envelope_rejected", extra={"reason": "spool_unavailable", "batchId": envelope["batchId"]})
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "spool_unavailable"})
            return
        try:
            enqueue_result = self.spool.enqueue_with_result(envelope)
        except SpoolFullError:
            LOGGER.error("envelope_rejected", extra={"reason": "spool_full", "batchId": envelope["batchId"]})
            self._send_json(HTTPStatus.INSUFFICIENT_STORAGE, {"error": "spool_full"})
            return
        except DuplicateBatchError:
            LOGGER.warning("envelope_rejected", extra={"reason": "batch_id_conflict", "batchId": envelope["batchId"]})
            self._send_json(HTTPStatus.CONFLICT, {"error": "batch_id_conflict"})
            return
        except SequenceConflictError:
            LOGGER.warning("envelope_rejected", extra={"reason": "sequence_conflict", "batchId": envelope["batchId"]})
            self._send_json(HTTPStatus.CONFLICT, {"error": "sequence_conflict"})
            return

        if enqueue_result.duplicate:
            LOGGER.info("envelope_duplicate", extra={"batchId": envelope["batchId"]})
            self._send_json(HTTPStatus.ACCEPTED, {"status": "duplicate", "batchId": envelope["batchId"]})
            return

        LOGGER.info(
            "envelope_accepted",
            extra={
                "batchId": envelope["batchId"],
                "sourceInstanceId": envelope["sourceInstanceId"],
                "sequence": envelope["sequence"],
                "spoolDepth": self.spool.status()["depth"],
            },
        )
        self._send_json(HTTPStatus.ACCEPTED, {"status": "accepted", "batchId": envelope["batchId"]})

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress BaseHTTPRequestHandler's unstructured access log."""

    def _content_length(self) -> int | None:
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return None

        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid_body_size"})
            return None

        return content_length

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    """Run a localhost-only development receiver."""

    configure_logging(os.environ.get("MT5_BRIDGE_LOG_LEVEL", "INFO"))
    host = os.environ.get("MT5_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("MT5_BRIDGE_PORT", "8001"))
    spool_directory = Path(os.environ.get("MT5_BRIDGE_SPOOL_PATH", "spool"))
    spool_max_items = int(os.environ.get("MT5_BRIDGE_SPOOL_MAX_ITEMS", "10000"))
    spool_max_bytes = int(os.environ.get("MT5_BRIDGE_SPOOL_MAX_BYTES", str(DEFAULT_MAX_BYTES)))

    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Starter bridge hanya boleh bind ke localhost.")

    BridgeRequestHandler.spool = EnvelopeSpool(spool_directory, spool_max_items, spool_max_bytes)
    backend_url = os.environ.get("MT5_BRIDGE_BACKEND_URL", "")
    backend_api_key = os.environ.get("MT5_BRIDGE_BACKEND_API_KEY", "")
    replay_interval = float(os.environ.get("MT5_BRIDGE_REPLAY_INTERVAL_SECONDS", "1"))
    if bool(backend_url) != bool(backend_api_key):
        raise ValueError("Backend URL dan API key harus dikonfigurasi bersama.")
    if replay_interval <= 0:
        raise ValueError("Replay interval harus positif.")

    if backend_url:
        replayer = SpoolReplayer(
            BridgeRequestHandler.spool,
            BackendPublisher(backend_url, backend_api_key),
        )
        threading.Thread(
            target=_run_publisher,
            args=(replayer, replay_interval),
            name="backend-publisher",
            daemon=True,
        ).start()
    server = ThreadingHTTPServer((host, port), BridgeRequestHandler)
    LOGGER.info(
        "bridge_started",
        extra={"host": host, "port": port, "spoolPath": str(spool_directory)},
    )
    server.serve_forever()


def _run_publisher(replayer: SpoolReplayer, interval_seconds: float) -> None:
    LOGGER.info("backend_publisher_started")
    while True:
        result = replayer.replay_one()
        if result is None:
            threading.Event().wait(interval_seconds)
        elif result.disposition is PublishDisposition.RETRY:
            LOGGER.warning("backend_publish_retry_exhausted", extra={"statusCode": result.status_code})
            threading.Event().wait(interval_seconds)
        elif result.disposition is PublishDisposition.PERMANENT_FAILURE:
            LOGGER.error("backend_envelope_quarantined", extra={"statusCode": result.status_code})


if __name__ == "__main__":
    run()
