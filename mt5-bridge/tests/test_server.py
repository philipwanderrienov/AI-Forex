import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any

from forex_intelligence_bridge.server import (
    MAX_BODY_BYTES,
    BridgeRequestHandler,
    ThreadingHTTPServer,
)
from forex_intelligence_bridge.health import HeartbeatMonitor
from forex_intelligence_bridge.spool import EnvelopeSpool
from test_contracts import valid_envelope


class BridgeConfigurationTests(unittest.TestCase):
    def test_body_limit_is_bounded(self) -> None:
        self.assertEqual(64 * 1024, MAX_BODY_BYTES)

    def test_receiver_uses_http_1_1_for_expect_continue_clients(self) -> None:
        self.assertEqual("HTTP/1.1", BridgeRequestHandler.protocol_version)


class BridgeHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        BridgeRequestHandler.spool = EnvelopeSpool(Path(self.temporary_directory.name))
        BridgeRequestHandler.heartbeat_monitor = HeartbeatMonitor()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), BridgeRequestHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        BridgeRequestHandler.spool = None
        BridgeRequestHandler.heartbeat_monitor = HeartbeatMonitor()
        self.temporary_directory.cleanup()

    def test_health_endpoint_reports_healthy(self) -> None:
        status, payload = self._request("GET", "/health")

        self.assertEqual(200, status)
        self.assertEqual("HEALTHY", payload["status"])
        self.assertEqual({"status": "UNKNOWN"}, payload["terminal"])
        self.assertEqual(
            "AVAILABLE",
            payload["spool"]["status"],
        )
        self.assertEqual(0, payload["spool"]["depth"])
        self.assertEqual(10_000, payload["spool"]["capacity"])
        self.assertEqual(0, payload["spool"]["usedBytes"])
        self.assertEqual(256 * 1024 * 1024, payload["spool"]["maxBytes"])
        self.assertEqual(0.0, payload["spool"]["utilizationPercent"])
        self.assertGreater(payload["spool"]["diskFreeBytes"], 0)

    def test_unknown_endpoint_is_not_found(self) -> None:
        status, payload = self._request("GET", "/unknown")

        self.assertEqual(404, status)
        self.assertEqual({"error": "not_found"}, payload)

    def test_valid_heartbeat_is_accepted(self) -> None:
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v1",
            "sourceInstanceId": "terminal-demo",
            "sentAt": "2026-08-20T01:00:00Z",
        }

        status, payload = self._request("POST", "/v1/mt5/heartbeat", heartbeat)

        self.assertEqual(202, status)
        self.assertEqual({"status": "accepted"}, payload)

        health_status, health = self._request("GET", "/health")
        self.assertEqual(200, health_status)
        self.assertEqual("HEALTHY", health["terminal"]["status"])
        self.assertEqual("terminal-demo", health["terminal"]["sourceInstanceId"])

    def test_invalid_heartbeat_schema_is_rejected(self) -> None:
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v2",
            "sourceInstanceId": "terminal-demo",
            "sentAt": "2026-08-20T01:00:00Z",
        }

        status, payload = self._request("POST", "/v1/mt5/heartbeat", heartbeat)

        self.assertEqual(400, status)
        self.assertEqual({"error": "unsupported_heartbeat_schema_version"}, payload)

    def test_invalid_json_is_rejected(self) -> None:
        status, payload = self._request(
            "POST",
            "/v1/mt5/heartbeat",
            body=b"{invalid",
        )

        self.assertEqual(400, status)
        self.assertEqual({"error": "invalid_json"}, payload)

    def test_oversized_body_is_rejected_before_reading(self) -> None:
        status, payload = self._request(
            "POST",
            "/v1/mt5/heartbeat",
            body=b"",
            headers={"Content-Length": str(MAX_BODY_BYTES + 1)},
        )

        self.assertEqual(413, status)
        self.assertEqual({"error": "invalid_body_size"}, payload)

    def test_valid_envelope_is_stored_in_spool(self) -> None:
        envelope = valid_envelope()

        status, payload = self._request("POST", "/v1/mt5/envelopes", envelope)

        self.assertEqual(202, status)
        self.assertEqual({"status": "accepted", "batchId": envelope["batchId"]}, payload)
        queued = BridgeRequestHandler.spool.peek() if BridgeRequestHandler.spool else None
        self.assertIsNotNone(queued)
        self.assertEqual(envelope, queued[1] if queued else None)

        _, health = self._request("GET", "/health")
        self.assertEqual(1, health["spool"]["depth"])
        self.assertGreater(health["spool"]["usedBytes"], 0)
        self.assertGreater(health["spool"]["utilizationPercent"], 0)

    def test_invalid_envelope_is_rejected(self) -> None:
        envelope = valid_envelope()
        envelope["checksum"] = "sha256:" + ("0" * 64)

        status, payload = self._request("POST", "/v1/mt5/envelopes", envelope)

        self.assertEqual(400, status)
        self.assertEqual({"error": "checksum_mismatch"}, payload)

    def test_duplicate_envelope_is_reported_without_overwrite(self) -> None:
        envelope = valid_envelope()
        self._request("POST", "/v1/mt5/envelopes", envelope)

        status, payload = self._request("POST", "/v1/mt5/envelopes", envelope)

        self.assertEqual(202, status)
        self.assertEqual({"status": "duplicate", "batchId": envelope["batchId"]}, payload)

    def test_full_spool_rejects_new_envelope(self) -> None:
        BridgeRequestHandler.spool = EnvelopeSpool(
            Path(self.temporary_directory.name),
            max_items=1,
        )
        first = valid_envelope()
        BridgeRequestHandler.spool.enqueue(first)
        second = valid_envelope()
        second["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
        second["sequence"] += 1

        status, payload = self._request("POST", "/v1/mt5/envelopes", second)

        self.assertEqual(507, status)
        self.assertEqual({"error": "spool_full"}, payload)

    def test_conflicting_batch_id_is_rejected(self) -> None:
        first = valid_envelope()
        BridgeRequestHandler.spool.enqueue(first)
        conflict = valid_envelope()
        conflict["sequence"] += 1
        conflict["sentAt"] = "2026-08-17T09:00:00Z"

        status, payload = self._request("POST", "/v1/mt5/envelopes", conflict)

        self.assertEqual(409, status)
        self.assertEqual({"error": "batch_id_conflict"}, payload)

    def test_conflicting_sequence_is_rejected(self) -> None:
        first = valid_envelope()
        BridgeRequestHandler.spool.enqueue(first)
        conflict = valid_envelope()
        conflict["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"

        status, payload = self._request("POST", "/v1/mt5/envelopes", conflict)

        self.assertEqual(409, status)
        self.assertEqual({"error": "sequence_conflict"}, payload)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        request_body = body if body is not None else (
            json.dumps(payload).encode("utf-8") if payload is not None else None
        )
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        connection = http.client.HTTPConnection(*self.server.server_address, timeout=2)
        try:
            connection.request(method, path, body=request_body, headers=request_headers)
            response = connection.getresponse()
            response_payload = json.loads(response.read().decode("utf-8"))
            return response.status, response_payload
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
