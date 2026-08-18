"""Local HTTP receiver used by the read-only MQL5 exporter."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

MAX_BODY_BYTES = 64 * 1024


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """Accept health checks and bounded MT5 heartbeat payloads."""

    server_version = "ForexIntelligenceBridge/0.1"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/health":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        self._send_json(HTTPStatus.OK, {"status": "healthy"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/v1/mt5/heartbeat":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        content_length = self._content_length()
        if content_length is None:
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        required_fields = {"schemaVersion", "sourceInstanceId", "sentAt"}
        if not isinstance(payload, dict) or not required_fields.issubset(payload):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_heartbeat"})
            return

        self._send_json(HTTPStatus.ACCEPTED, {"status": "accepted"})

    def log_message(self, format: str, *args: Any) -> None:
        """Use structured logging later; avoid default request data logging now."""

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

    def _send_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    """Run a localhost-only development receiver."""

    host = os.environ.get("MT5_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("MT5_BRIDGE_PORT", "8001"))

    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Starter bridge hanya boleh bind ke localhost.")

    server = ThreadingHTTPServer((host, port), BridgeRequestHandler)
    print(f"MT5 bridge listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
