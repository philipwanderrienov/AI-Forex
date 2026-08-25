"""Development-only simulator for the MT5 read-only exporter.

Run the real bridge first, then execute this script to send heartbeat and
candle payloads using the same HTTP contracts expected from the MQL5 exporter.
Only Python standard-library modules are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BRIDGE_URL = "http://127.0.0.1:8001"
SOURCE_INSTANCE_ID = "mt5-simulator-local"
BROKER_SERVER_ALIAS = "demo-simulator"


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_checksum(records: list[dict[str, object]]) -> str:
    raw = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def random_ulid() -> str:
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return "".join(random.choice(alphabet) for _ in range(26))


def post_json(path: str, payload: dict[str, object]) -> tuple[int, str]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        BRIDGE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")
    except urllib.error.URLError as error:
        raise RuntimeError(f"Bridge is unreachable at {BRIDGE_URL}: {error.reason}") from error


def heartbeat() -> dict[str, object]:
    return {
        "schemaVersion": "mt5-heartbeat.v1",
        "sourceInstanceId": SOURCE_INSTANCE_ID,
        "sentAt": utc_iso(datetime.now(timezone.utc)),
    }


def final_h1_record(*, invalid_ohlc: bool = False) -> dict[str, object]:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    open_time = now - timedelta(hours=1)
    close_time = now
    record: dict[str, object] = {
        "schemaVersion": "candle.v1",
        "source": "MT5",
        "brokerServerAlias": BROKER_SERVER_ALIAS,
        "brokerSymbol": "EURUSD",
        "instrument": "EURUSD",
        "timeframe": "H1",
        "openTime": utc_iso(open_time),
        "closeTime": utc_iso(close_time),
        "open": "1.17000",
        "high": "1.17250",
        "low": "1.16950",
        "close": "1.17180",
        "tickVolume": 1524,
        "status": "FINAL",
        "receivedAt": utc_iso(datetime.now(timezone.utc)),
        "dataQuality": "GOOD",
    }
    if invalid_ohlc:
        record["high"] = "1.16000"
    return record


def candle_envelope(sequence: int, *, invalid_ohlc: bool = False, batch_id: str | None = None) -> dict[str, object]:
    record = final_h1_record(invalid_ohlc=invalid_ohlc)
    records = [record]
    return {
        "schemaVersion": "mt5-envelope.v1",
        "batchId": batch_id or random_ulid(),
        "sourceInstanceId": SOURCE_INSTANCE_ID,
        "brokerServerAlias": BROKER_SERVER_ALIAS,
        "sequence": sequence,
        "sentAt": utc_iso(datetime.now(timezone.utc)),
        "payloadType": "CANDLES",
        "records": records,
        "checksum": canonical_checksum(records),
    }


def send(label: str, path: str, payload: dict[str, object]) -> int:
    status, response = post_json(path, payload)
    print(f"{label:<18} -> HTTP {status} {response}")
    return status


def run_once() -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    send("EURUSD H1 FINAL", "/v1/mt5/envelopes", candle_envelope(1))


def run_duplicate() -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    batch_id = random_ulid()
    envelope = candle_envelope(1, batch_id=batch_id)
    send("CANDLE FIRST", "/v1/mt5/envelopes", envelope)
    send("CANDLE DUPLICATE", "/v1/mt5/envelopes", envelope)


def run_invalid_ohlc() -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    send("INVALID OHLC", "/v1/mt5/envelopes", candle_envelope(1, invalid_ohlc=True))


def run_disconnect(seconds: int) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    print(f"Stopping heartbeat for {seconds}s to simulate terminal disconnect...")
    time.sleep(seconds)
    print("Disconnect simulation finished. Check GET /health.")


def run_continuous(interval: int) -> None:
    sequence = 0
    print(f"MT5 simulator -> {BRIDGE_URL}. Ctrl+C to stop.")
    try:
        while True:
            send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
            if sequence == 0:
                sequence += 1
                send("EURUSD H1 FINAL", "/v1/mt5/envelopes", candle_envelope(sequence))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMT5 simulator stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate MT5 heartbeat and EURUSD H1 candle delivery.")
    parser.add_argument("--once", action="store_true", help="Send one heartbeat and one valid final H1 candle.")
    parser.add_argument(
        "--scenario",
        choices=("duplicate", "invalid-ohlc", "disconnect"),
        help="Run a focused failure/recovery scenario.",
    )
    parser.add_argument("--interval", type=int, default=1, help="Heartbeat interval for continuous mode (seconds).")
    parser.add_argument("--disconnect-seconds", type=int, default=15, help="Pause duration for disconnect scenario.")
    args = parser.parse_args()

    if args.interval < 1 or args.disconnect_seconds < 1:
        parser.error("interval values must be at least 1 second")

    try:
        if args.once:
            run_once()
        elif args.scenario == "duplicate":
            run_duplicate()
        elif args.scenario == "invalid-ohlc":
            run_invalid_ohlc()
        elif args.scenario == "disconnect":
            run_disconnect(args.disconnect_seconds)
        else:
            run_continuous(args.interval)
    except RuntimeError as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
