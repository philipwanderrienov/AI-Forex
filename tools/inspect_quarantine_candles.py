#!/usr/bin/env python3
"""Read-only, contract-validated candle inventory for recovery review; never replay."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mt5-bridge" / "src"))
from forex_intelligence_bridge.contracts import (  # noqa: E402
    ContractValidationError,
    validate_candle_envelope,
)
from audit_bridge_quarantine import classify_detail  # noqa: E402


def inventory(directory: Path, instrument: str, timeframe: str) -> dict:
    if not directory.is_dir():
        raise ValueError("quarantine directory does not exist")
    paths = sorted(p for p in directory.glob("*.json") if not p.name.endswith(".meta.json"))
    rows, errors = [], []
    maxima: dict[str, int] = {}
    validated = 0
    for path in paths:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            validate_candle_envelope(envelope)
            validated += 1
            source = envelope["sourceInstanceId"]
            maxima[source] = max(maxima.get(source, 0), envelope["sequence"])
            meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                raise ValueError("invalid metadata")
            rejection = classify_detail(meta.get("detail"))
            for record in envelope["records"]:
                if (record["instrument"], record["timeframe"]) != (instrument, timeframe):
                    continue
                original_time = record["openTime"]
                parsed_time = (datetime.fromisoformat(original_time[:-1] + "+00:00")
                               if original_time.endswith("Z") else
                               datetime.strptime(original_time, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc))
                rows.append({
                    "payloadFile": path.name,
                    "sourceInstanceId": source,
                    "sequence": envelope["sequence"],
                    "batchId": envelope["batchId"],
                    "checksum": envelope["checksum"],
                    "rejection": rejection,
                    "originalOpenTime": original_time,
                    "openTimeUtc": parsed_time.isoformat().replace("+00:00", "Z"),
                    "openTimeWib": parsed_time.astimezone(ZoneInfo("Asia/Jakarta")).isoformat(),
                    **{k: record[k] for k in ("brokerServerAlias", "brokerSymbol", "status",
                                             "open", "high", "low", "close", "tickVolume")},
                })
        except (OSError, ValueError, TypeError, KeyError) as error:
            # Do not echo arbitrary payloads, metadata details or credentials.
            code = error.code if isinstance(error, ContractValidationError) else type(error).__name__
            errors.append({"file": path.name, "error": code})
    payload_stems = {p.stem for p in paths}
    for meta in sorted(directory.glob("*.meta.json")):
        if meta.name.removesuffix(".meta.json") not in payload_stems:
            errors.append({"file": meta.name, "error": "missing_payload"})
    rows.sort(key=lambda r: (r["openTimeUtc"], r["sourceInstanceId"], r["sequence"]))
    counts = Counter(row["rejection"] for row in rows)
    return {
        "mode": "READ_ONLY_INVENTORY_NOT_REPLAY_APPROVAL",
        "instrument": instrument, "timeframe": timeframe,
        "payloadFiles": len(paths), "validatedPayloads": validated,
        "selectedRecords": len(rows), "rejectionRecordCounts": dict(sorted(counts.items())),
        "quarantineSequenceMaxima": maxima,
        "limitations": ["No database or broker comparison performed.",
                        "Contract validation does not prove historical UTC offset correctness.",
                        "Quarantine maxima are not a complete source sequence floor.",
                        "Preserved HTTP 401 payloads may already have been replayed."],
        "records": rows, "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarantine-dir", type=Path, default=Path("mt5-bridge/spool/quarantine"))
    parser.add_argument("--instrument", choices=["EURUSD", "GBPUSD", "EURGBP", "EURCHF", "XAUUSD"], default="XAUUSD")
    parser.add_argument("--timeframe", choices=["M15", "H1", "H4"], default="H1")
    args = parser.parse_args()
    try:
        report = inventory(args.quarantine_dir, args.instrument, args.timeframe)
    except ValueError as error:
        parser.exit(2, f"ERROR: {error}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
