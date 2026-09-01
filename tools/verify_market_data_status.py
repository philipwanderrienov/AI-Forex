#!/usr/bin/env python3
"""Verify the authenticated market-data status contract against a running API."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


EXPECTED_INSTRUMENTS = ("EURUSD", "GBPUSD", "EURGBP", "EURCHF", "XAUUSD")
EXPECTED_TIMEFRAMES = ("M15", "H1", "H4")
EXPECTED_SERIES = {
    (instrument, timeframe)
    for instrument in EXPECTED_INSTRUMENTS
    for timeframe in EXPECTED_TIMEFRAMES
}
VALID_STATUSES = {"Unknown", "Fresh", "Stale", "GapDetected", "MarketClosed"}


def request_json(url: str, *, payload: dict | None = None, token: str | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} from {url}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Cannot reach {url}: {error.reason}") from error


def validate_snapshot(snapshot: dict) -> list[str]:
    errors: list[str] = []
    series = snapshot.get("series")
    if not isinstance(series, list):
        return ["Response field 'series' must be an array."]

    observed: list[tuple[str, str]] = []
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            errors.append(f"series[{index}] must be an object.")
            continue
        key = (item.get("instrument"), item.get("timeframe"))
        observed.append(key)
        if item.get("status") not in VALID_STATUSES:
            errors.append(f"{key[0]} {key[1]} has invalid status {item.get('status')!r}.")
        gap_count = item.get("gapCount")
        if not isinstance(gap_count, int) or gap_count < 0:
            errors.append(f"{key[0]} {key[1]} has invalid gapCount {gap_count!r}.")

    observed_set = set(observed)
    missing = sorted(EXPECTED_SERIES - observed_set)
    unexpected = sorted(observed_set - EXPECTED_SERIES)
    duplicates = sorted({key for key in observed if observed.count(key) > 1})
    if missing:
        errors.append(f"Missing canonical series: {missing}")
    if unexpected:
        errors.append(f"Unexpected series: {unexpected}")
    if duplicates:
        errors.append(f"Duplicate series: {duplicates}")
    if len(series) != len(EXPECTED_SERIES):
        errors.append(f"Expected 15 series, received {len(series)}.")
    if snapshot.get("status") not in VALID_STATUSES:
        errors.append(f"Invalid overall status {snapshot.get('status')!r}.")
    if not isinstance(snapshot.get("marketOpen"), bool):
        errors.append("Response field 'marketOpen' must be boolean.")
    if not snapshot.get("evaluatedAt"):
        errors.append("Response field 'evaluatedAt' is missing.")
    return errors


def print_snapshot(snapshot: dict) -> None:
    print(
        f"evaluatedAt={snapshot.get('evaluatedAt')} "
        f"marketOpen={snapshot.get('marketOpen')} status={snapshot.get('status')}"
    )
    print("instrument timeframe status        lastCloseTime                 ageMinutes gaps")
    for item in sorted(snapshot["series"], key=lambda value: (value["instrument"], value["timeframe"])):
        print(
            f"{item['instrument']:<10} {item['timeframe']:<9} {item['status']:<13} "
            f"{str(item.get('lastCloseTime')):<29} {str(item.get('ageMinutes')):<10} "
            f"{item.get('gapCount')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="API origin, for example http://127.0.0.1:5000")
    parser.add_argument("--username", default="admin", help="Bootstrap username (default: admin)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    parsed_url = urllib.parse.urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        print("--base-url must be an absolute HTTP(S) URL.", file=sys.stderr)
        return 2

    password = getpass.getpass("Bootstrap password: ")
    try:
        tokens = request_json(
            f"{base_url}/api/auth/login",
            payload={"username": args.username, "password": password},
        )
        password = ""
        access_token = tokens.get("accessToken")
        if not access_token:
            raise RuntimeError("Login response did not contain accessToken.")
        snapshot = request_json(f"{base_url}/api/market-data/status", token=access_token)
        access_token = ""
    except RuntimeError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1

    errors = validate_snapshot(snapshot)
    print_snapshot(snapshot)
    if errors:
        print("\nContract verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("\nPASS: authenticated response contains all 15 canonical series.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
