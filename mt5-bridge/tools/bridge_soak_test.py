"""Bounded local soak/load verification for the MT5 bridge reliability path."""

from __future__ import annotations

import argparse
import http.client
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from forex_intelligence_bridge.health import HeartbeatMonitor
from forex_intelligence_bridge.publisher import PublishDisposition, PublishResult, SpoolReplayer
from forex_intelligence_bridge.server import BridgeRequestHandler, ThreadingHTTPServer
from forex_intelligence_bridge.spool import EnvelopeSpool
if __package__:
    from tools.mt5_simulator import candle_envelope, heartbeat
else:
    from mt5_simulator import candle_envelope, heartbeat


class SoakPublisher:
    """Deterministic backend double with one retry and one permanent rejection."""

    def __init__(self, permanent_failure_sequence: int) -> None:
        self.permanent_failure_sequence = permanent_failure_sequence
        self.calls = 0
        self._retried_sequences: set[int] = set()

    def publish(self, envelope: dict[str, Any]) -> PublishResult:
        self.calls += 1
        sequence = int(envelope["sequence"])
        if sequence == self.permanent_failure_sequence:
            return PublishResult(PublishDisposition.PERMANENT_FAILURE, 400, "soak fixture rejection")
        if sequence == 1 and sequence not in self._retried_sequences:
            self._retried_sequences.add(sequence)
            return PublishResult(PublishDisposition.RETRY, 503, "soak fixture outage")
        return PublishResult(PublishDisposition.ACK, 202)


def request_json(
    address: tuple[str, int],
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
    connection = http.client.HTTPConnection(*address, timeout=5)
    try:
        connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


def run_soak(envelope_count: int, duplicate_every: int) -> dict[str, int | float]:
    if envelope_count < 3:
        raise ValueError("envelope_count must be at least 3")
    if duplicate_every < 1:
        raise ValueError("duplicate_every must be positive")

    started_at = time.monotonic()
    duplicate_count = 0
    with tempfile.TemporaryDirectory(prefix="mt5-bridge-soak-") as directory:
        spool_path = Path(directory) / "spool"
        BridgeRequestHandler.spool = EnvelopeSpool(spool_path, max_items=envelope_count + 1)
        BridgeRequestHandler.heartbeat_monitor = HeartbeatMonitor()
        server = ThreadingHTTPServer(("127.0.0.1", 0), BridgeRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            status, _ = request_json(server.server_address, "POST", "/v1/mt5/heartbeat", heartbeat())
            if status != 202:
                raise RuntimeError(f"heartbeat returned HTTP {status}")

            for sequence in range(1, envelope_count + 1):
                envelope = candle_envelope(sequence)
                status, response = request_json(server.server_address, "POST", "/v1/mt5/envelopes", envelope)
                if status != 202 or response.get("status") != "accepted":
                    raise RuntimeError(f"sequence {sequence} was not accepted: HTTP {status} {response}")
                if sequence % duplicate_every == 0:
                    status, response = request_json(
                        server.server_address,
                        "POST",
                        "/v1/mt5/envelopes",
                        envelope,
                    )
                    if status != 202 or response.get("status") != "duplicate":
                        raise RuntimeError(f"sequence {sequence} duplicate was not idempotent")
                    duplicate_count += 1

            _, health = request_json(server.server_address, "GET", "/health")
            if health["spool"]["depth"] != envelope_count:
                raise RuntimeError("receiver spool depth does not match accepted envelope count")
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join()
            BridgeRequestHandler.spool = None
            BridgeRequestHandler.heartbeat_monitor = HeartbeatMonitor()

        recovered_spool = EnvelopeSpool(spool_path, max_items=envelope_count + 1)
        if recovered_spool.status()["depth"] != envelope_count:
            raise RuntimeError("restart recovery did not preserve every pending envelope")

        permanent_failure_sequence = envelope_count // 2
        publisher = SoakPublisher(permanent_failure_sequence)
        replayer = SpoolReplayer(
            recovered_spool,
            publisher,
            max_attempts=3,
            sleep=lambda _: None,
            random_value=lambda: 0.5,
        )
        while recovered_spool.peek() is not None:
            replayer.replay_one()

        final_status = recovered_spool.status()
        if final_status["depth"] != 0 or final_status["quarantineDepth"] != 1:
            raise RuntimeError("replay did not drain healthy entries and quarantine one rejection")

    elapsed = time.monotonic() - started_at
    return {
        "envelopesAccepted": envelope_count,
        "duplicatesVerified": duplicate_count,
        "publisherCalls": publisher.calls,
        "acknowledged": envelope_count - 1,
        "quarantined": 1,
        "pendingAfterReplay": 0,
        "elapsedSeconds": round(elapsed, 3),
        "requestsPerSecond": round((envelope_count + duplicate_count + 1) / elapsed, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelopes", type=int, default=500)
    parser.add_argument("--duplicate-every", type=int, default=10)
    args = parser.parse_args()
    result = run_soak(args.envelopes, args.duplicate_every)
    print(json.dumps({"status": "PASS", **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
