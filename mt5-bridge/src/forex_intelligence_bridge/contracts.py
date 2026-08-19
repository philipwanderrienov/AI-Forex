"""Validation for versioned MT5 market-data envelopes."""

from __future__ import annotations

import re
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

MAX_RECORDS_PER_BATCH = 100
_ULID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
_CHECKSUM_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_INSTRUMENTS = {"EURUSD", "GBPUSD", "EURGBP", "EURCHF", "XAUUSD"}
_TIMEFRAMES = {"M15", "H1", "H4"}
_TIMEFRAME_DURATIONS = {
    "M15": timedelta(minutes=15),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
}
_CANDLE_STATUSES = {"PARTIAL", "FINAL"}


class ContractValidationError(ValueError):
    """Raised when an envelope violates the canonical bridge contract."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def validate_candle_envelope(payload: Any) -> dict[str, Any]:
    """Validate an mt5-envelope.v1 CANDLES batch without changing its values."""

    if not isinstance(payload, dict):
        raise ContractValidationError("invalid_envelope")

    required = {
        "schemaVersion",
        "batchId",
        "sourceInstanceId",
        "brokerServerAlias",
        "sequence",
        "sentAt",
        "payloadType",
        "records",
        "checksum",
    }
    if not required.issubset(payload):
        raise ContractValidationError("missing_required_field")
    if payload["schemaVersion"] != "mt5-envelope.v1":
        raise ContractValidationError("unsupported_schema_version")
    if payload["payloadType"] != "CANDLES":
        raise ContractValidationError("unsupported_payload_type")
    if not isinstance(payload["batchId"], str) or not _ULID_PATTERN.fullmatch(payload["batchId"]):
        raise ContractValidationError("invalid_batch_id")
    if not _bounded_text(payload["sourceInstanceId"], 128):
        raise ContractValidationError("invalid_source_instance_id")
    if not _bounded_text(payload["brokerServerAlias"], 128):
        raise ContractValidationError("invalid_broker_server_alias")
    if isinstance(payload["sequence"], bool) or not isinstance(payload["sequence"], int) or payload["sequence"] < 0:
        raise ContractValidationError("invalid_sequence")
    sent_at = _parse_utc_timestamp(payload["sentAt"], "invalid_sent_at")
    if not isinstance(payload["checksum"], str) or not _CHECKSUM_PATTERN.fullmatch(payload["checksum"]):
        raise ContractValidationError("invalid_checksum")

    records = payload["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS_PER_BATCH:
        raise ContractValidationError("invalid_record_count")
    for record in records:
        _validate_candle(record, payload["brokerServerAlias"], sent_at)
    if payload["checksum"] != records_checksum(records):
        raise ContractValidationError("checksum_mismatch")

    return payload


def records_checksum(records: list[dict[str, Any]]) -> str:
    """Return SHA-256 for canonical UTF-8 JSON of the records array."""

    canonical_json = json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical_json).hexdigest()


def _validate_candle(record: Any, broker_server_alias: str, sent_at: datetime) -> None:
    if not isinstance(record, dict):
        raise ContractValidationError("invalid_candle")
    required = {
        "schemaVersion",
        "source",
        "brokerServerAlias",
        "brokerSymbol",
        "instrument",
        "timeframe",
        "openTime",
        "closeTime",
        "open",
        "high",
        "low",
        "close",
        "tickVolume",
        "status",
        "receivedAt",
        "dataQuality",
    }
    if not required.issubset(record):
        raise ContractValidationError("missing_candle_field")
    if record["schemaVersion"] != "candle.v1" or record["source"] != "MT5":
        raise ContractValidationError("invalid_candle_source")
    if record["brokerServerAlias"] != broker_server_alias:
        raise ContractValidationError("broker_alias_mismatch")
    if not _bounded_text(record["brokerSymbol"], 32):
        raise ContractValidationError("invalid_broker_symbol")
    if record["instrument"] not in _INSTRUMENTS:
        raise ContractValidationError("invalid_instrument")
    if record["timeframe"] not in _TIMEFRAMES:
        raise ContractValidationError("invalid_timeframe")
    open_time = _parse_utc_timestamp(record["openTime"], "invalid_open_time")
    close_time = _parse_utc_timestamp(record["closeTime"], "invalid_close_time")
    _parse_utc_timestamp(record["receivedAt"], "invalid_received_at")
    if close_time <= open_time:
        raise ContractValidationError("invalid_candle_interval")
    if close_time - open_time != _TIMEFRAME_DURATIONS[record["timeframe"]]:
        raise ContractValidationError("timeframe_interval_mismatch")

    open_price = _positive_decimal(record["open"])
    high_price = _positive_decimal(record["high"])
    low_price = _positive_decimal(record["low"])
    close_price = _positive_decimal(record["close"])
    if high_price < max(open_price, close_price) or low_price > min(open_price, close_price):
        raise ContractValidationError("invalid_ohlc")
    if isinstance(record["tickVolume"], bool) or not isinstance(record["tickVolume"], int) or record["tickVolume"] < 0:
        raise ContractValidationError("invalid_tick_volume")
    if record["status"] not in _CANDLE_STATUSES:
        raise ContractValidationError("invalid_candle_status")
    if record["status"] == "FINAL" and close_time > sent_at:
        raise ContractValidationError("candle_not_final")
    if record["dataQuality"] != "GOOD":
        raise ContractValidationError("unsupported_data_quality")


def _bounded_text(value: Any, maximum_length: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum_length


def _parse_utc_timestamp(value: Any, error_code: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractValidationError(error_code)
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ContractValidationError(error_code) from error


def _positive_decimal(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise ContractValidationError("invalid_decimal")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ContractValidationError("invalid_decimal") from error
    if not number.is_finite() or number <= 0:
        raise ContractValidationError("invalid_decimal")
    return number
