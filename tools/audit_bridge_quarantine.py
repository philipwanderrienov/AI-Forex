#!/usr/bin/env python3
"""Summarize MT5 bridge quarantine entries without exposing envelope records."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SAFE_ENVELOPE_FIELDS = ("batchId", "sourceInstanceId", "sequence", "checksum")


def classify_detail(detail: object) -> str:
    value = str(detail or "")
    if "HTTP 401" in value:
        return "http_401"
    if "HTTP 409" in value:
        return "http_409"
    if value.startswith("HTTP "):
        status = value.removeprefix("HTTP ").split(":", 1)[0].strip()
        return f"http_{status}" if status.isdigit() else "http_other"
    return "non_http"


def audit_quarantine(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ValueError(f"quarantine directory does not exist: {directory}")

    counts: Counter[str] = Counter()
    conflicts: list[dict[str, Any]] = []
    errors: list[str] = []
    metadata_paths = sorted(directory.glob("*.meta.json"))

    for metadata_path in metadata_paths:
        try:
            metadata = _read_object(metadata_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{metadata_path.name}: invalid metadata ({error})")
            continue

        classification = classify_detail(metadata.get("detail"))
        counts[classification] += 1
        payload_path = metadata_path.with_name(
            metadata_path.name.removesuffix(".meta.json") + ".json"
        )
        if not payload_path.is_file():
            errors.append(f"{metadata_path.name}: paired payload is missing")
            continue

        if classification == "http_409":
            try:
                payload = _read_object(payload_path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"{payload_path.name}: invalid payload ({error})")
                continue
            conflicts.append(
                {
                    "payloadFile": payload_path.name,
                    **{field: payload.get(field) for field in SAFE_ENVELOPE_FIELDS},
                }
            )

    payload_count = len(
        [path for path in directory.glob("*.json") if not path.name.endswith(".meta.json")]
    )
    if payload_count != len(metadata_paths):
        errors.append(
            f"payload/metadata count mismatch: {payload_count} payloads, "
            f"{len(metadata_paths)} metadata files"
        )

    return {
        "directory": str(directory),
        "total": len(metadata_paths),
        "counts": dict(sorted(counts.items())),
        "http409Entries": conflicts,
        "errors": errors,
    }


def _read_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"Quarantine: {report['directory']}",
        f"Total: {report['total']}",
    ]
    for name, count in report["counts"].items():
        lines.append(f"  {name}: {count}")
    if report["http409Entries"]:
        lines.append("HTTP 409 entries (do not replay without ledger review):")
        for item in report["http409Entries"]:
            lines.append(
                "  "
                f"batchId={item['batchId']} sourceInstanceId={item['sourceInstanceId']} "
                f"sequence={item['sequence']} checksum={item['checksum']}"
            )
    if report["errors"]:
        lines.append("Errors:")
        for error in report["errors"]:
            lines.append(f"  {error}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=Path("mt5-bridge/spool/quarantine"),
        help="quarantine directory (default: mt5-bridge/spool/quarantine)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    try:
        report = audit_quarantine(args.quarantine_dir)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
