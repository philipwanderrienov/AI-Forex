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
CANONICAL_INSTRUMENTS = ("EURUSD", "GBPUSD", "EURGBP", "EURCHF", "XAUUSD")
TIMEFRAME_MINUTES = {"M15": 15, "H1": 60, "H4": 240}
PRICE_FIXTURES = {
    "EURUSD": ("1.17000", "1.17250", "1.16950", "1.17180"),
    "GBPUSD": ("1.35000", "1.35400", "1.34800", "1.35250"),
    "EURGBP": ("0.86500", "0.86700", "0.86400", "0.86620"),
    "EURCHF": ("0.93000", "0.93200", "0.92900", "0.93120"),
    "XAUUSD": ("3400.00", "3412.50", "3395.00", "3408.20"),
}


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


def final_candle_record(
    instrument: str = "EURUSD",
    timeframe: str = "H1",
    *,
    invalid_ohlc: bool = False,
) -> dict[str, object]:
    if instrument not in CANONICAL_INSTRUMENTS:
        raise ValueError(f"unsupported canonical instrument: {instrument}")
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported canonical timeframe: {timeframe}")

    duration_minutes = TIMEFRAME_MINUTES[timeframe]
    duration = timedelta(minutes=duration_minutes)
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    boundary_seconds = duration_minutes * 60
    close_time = datetime.fromtimestamp(
        int(now.timestamp()) // boundary_seconds * boundary_seconds,
        timezone.utc,
    )
    open_time = close_time - duration
    open_price, high_price, low_price, close_price = PRICE_FIXTURES[instrument]
    record: dict[str, object] = {
        "schemaVersion": "candle.v1",
        "source": "MT5",
        "brokerServerAlias": BROKER_SERVER_ALIAS,
        "brokerSymbol": instrument,
        "instrument": instrument,
        "timeframe": timeframe,
        "openTime": utc_iso(open_time),
        "closeTime": utc_iso(close_time),
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "tickVolume": 1524,
        "status": "FINAL",
        "receivedAt": utc_iso(datetime.now(timezone.utc)),
        "dataQuality": "GOOD",
    }
    if invalid_ohlc:
        record["high"] = "1.16000"
    return record


def final_h1_record(*, invalid_ohlc: bool = False) -> dict[str, object]:
    return final_candle_record(invalid_ohlc=invalid_ohlc)


def candle_envelope(
    sequence: int,
    *,
    instrument: str = "EURUSD",
    timeframe: str = "H1",
    invalid_ohlc: bool = False,
    batch_id: str | None = None,
) -> dict[str, object]:
    record = final_candle_record(instrument, timeframe, invalid_ohlc=invalid_ohlc)
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


def run_once(sequence_start: int = 1) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    send("EURUSD H1 FINAL", "/v1/mt5/envelopes", candle_envelope(sequence_start))


def run_matrix(sequence_start: int = 1) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    sequence = sequence_start
    for instrument in CANONICAL_INSTRUMENTS:
        for timeframe in TIMEFRAME_MINUTES:
            send(
                f"{instrument} {timeframe} FINAL",
                "/v1/mt5/envelopes",
                candle_envelope(sequence, instrument=instrument, timeframe=timeframe),
            )
            sequence += 1


def run_duplicate(sequence_start: int = 1) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    batch_id = random_ulid()
    envelope = candle_envelope(sequence_start, batch_id=batch_id)
    send("CANDLE FIRST", "/v1/mt5/envelopes", envelope)
    send("CANDLE DUPLICATE", "/v1/mt5/envelopes", envelope)


def run_invalid_ohlc(sequence_start: int = 1) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    send(
        "INVALID OHLC",
        "/v1/mt5/envelopes",
        candle_envelope(sequence_start, invalid_ohlc=True),
    )


def run_disconnect(seconds: int) -> None:
    send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
    print(f"Stopping heartbeat for {seconds}s to simulate terminal disconnect...")
    time.sleep(seconds)
    print("Disconnect simulation finished. Check GET /health.")


def run_continuous(interval: int, sequence_start: int = 1) -> None:
    sequence = sequence_start
    print(f"MT5 simulator -> {BRIDGE_URL}. Ctrl+C to stop.")
    try:
        while True:
            send("HEARTBEAT", "/v1/mt5/heartbeat", heartbeat())
            if sequence == sequence_start:
                send("EURUSD H1 FINAL", "/v1/mt5/envelopes", candle_envelope(sequence))
                sequence += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMT5 simulator stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate MT5 heartbeat and EURUSD H1 candle delivery.")
    parser.add_argument("--once", action="store_true", help="Send one heartbeat and one valid final H1 candle.")
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Send one valid FINAL candle for all five instruments and three timeframes.",
    )
    parser.add_argument(
        "--scenario",
        choices=("duplicate", "invalid-ohlc", "disconnect"),
        help="Run a focused failure/recovery scenario.",
    )
    parser.add_argument("--interval", type=int, default=1, help="Heartbeat interval for continuous mode (seconds).")
    parser.add_argument("--disconnect-seconds", type=int, default=15, help="Pause duration for disconnect scenario.")
    parser.add_argument(
        "--sequence-start",
        type=int,
        default=1,
        help="First source sequence to send; increase it when reusing a persistent backend ledger.",
    )
    args = parser.parse_args()

    if args.interval < 1 or args.disconnect_seconds < 1 or args.sequence_start < 1:
        parser.error("interval and sequence values must be at least 1")

    try:
        if args.once:
            run_once(args.sequence_start)
        elif args.matrix:
            run_matrix(args.sequence_start)
        elif args.scenario == "duplicate":
            run_duplicate(args.sequence_start)
        elif args.scenario == "invalid-ohlc":
            run_invalid_ohlc(args.sequence_start)
        elif args.scenario == "disconnect":
            run_disconnect(args.disconnect_seconds)
        else:
            run_continuous(args.interval, args.sequence_start)
    except RuntimeError as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
