"""Kontrak dan validasi envelope data pasar yang dikirim dari MT5.

Modul ini memastikan struktur batch candle dari MT5 sesuai kontrak kanonis
sebelum data diproses oleh komponen lain. Validasi sengaja tidak mengubah
payload agar nilai yang diperiksa sama persis dengan nilai yang dikirim.
"""

from __future__ import annotations

import re
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

MAX_RECORDS_PER_BATCH = 100
# Pola dan daftar nilai yang diizinkan oleh kontrak versi saat ini.
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
_MT5_UTC_TIMESTAMP_FORMAT = "%Y.%m.%d %H:%M:%S"


class ContractValidationError(ValueError):
    """Kesalahan yang menandakan payload melanggar kontrak bridge.

    Atribut ``code`` berisi kode stabil yang dapat dipakai pemanggil untuk
    logging, pemetaan respons, atau pengujian tanpa bergantung pada pesan bebas.
    """

    def __init__(self, code: str) -> None:
        """Buat kesalahan validasi dengan kode penyebab yang spesifik."""

        super().__init__(code)
        self.code = code


def validate_heartbeat(payload: Any) -> dict[str, Any]:
    """Validasi heartbeat starter yang dikirim berkala oleh EA MT5.

    Heartbeat membuktikan instance EA masih dapat menjangkau bridge. Versi
    schema, identitas instance, dan timestamp UTC diperiksa, kemudian payload
    asli dikembalikan tanpa modifikasi.
    """

    if not isinstance(payload, dict):
        raise ContractValidationError("invalid_heartbeat")

    required = {"schemaVersion", "sourceInstanceId", "sentAt"}
    if not required.issubset(payload):
        raise ContractValidationError("missing_heartbeat_field")
    if payload["schemaVersion"] != "mt5-heartbeat.v1":
        raise ContractValidationError("unsupported_heartbeat_schema_version")
    if not _bounded_text(payload["sourceInstanceId"], 128):
        raise ContractValidationError("invalid_source_instance_id")
    _parse_utc_timestamp(payload["sentAt"], "invalid_sent_at")

    return payload


def validate_candle_envelope(payload: Any) -> dict[str, Any]:
    """Validasi satu batch ``CANDLES`` berformat ``mt5-envelope.v1``.

    Pemeriksaan mencakup metadata envelope, jumlah dan isi record, hubungan
    waktu candle, serta checksum. Payload asli dikembalikan tanpa modifikasi
    ketika valid; pelanggaran pertama menghasilkan ``ContractValidationError``.
    """

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
    """Hitung checksum SHA-256 dari representasi JSON kanonis kumpulan record.

    Pengurutan key dan separator yang konsisten membuat checksum deterministik:
    data yang sama menghasilkan checksum yang sama meski urutan key input beda.
    """

    canonical_json = json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical_json).hexdigest()


def _validate_candle(record: Any, broker_server_alias: str, sent_at: datetime) -> None:
    """Validasi satu entity candle beserta konsistensinya terhadap envelope.

    Selain field wajib, fungsi ini memeriksa instrumen/timeframe yang didukung,
    durasi interval, aturan OHLC, volume, status final, dan kualitas data.
    ``broker_server_alias`` serta ``sent_at`` berasal dari envelope induk dan
    dipakai untuk memastikan record tidak bertentangan dengan batch-nya.
    """

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
    """Periksa bahwa nilai adalah teks non-kosong dalam batas panjang kontrak."""

    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum_length


def _parse_utc_timestamp(value: Any, error_code: str) -> datetime:
    """Parse timestamp UTC dari format kanonis atau format native MT5 lama.

    Format kanonis tetap ISO-8601 berakhiran ``Z``. Bridge juga menerima
    ``YYYY.MM.DD HH:MM:SS`` sebagai format kompatibilitas untuk terminal MT5/Wine
    yang masih mengirim hasil ``TimeToString``. Nilai kompatibilitas diperlakukan
    sebagai UTC hanya untuk validasi; payload asli tidak dimodifikasi.
    """

    if not isinstance(value, str) or not value:
        raise ContractValidationError(error_code)

    if value.endswith("Z"):
        try:
            return datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as error:
            raise ContractValidationError(error_code) from error

    try:
        return datetime.strptime(value, _MT5_UTC_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ContractValidationError(error_code) from error


def _positive_decimal(value: Any) -> Decimal:
    """Ubah string harga menjadi Decimal positif dan bernilai terbatas.

    String diwajibkan agar presisi nilai finansial tetap terjaga dan tidak
    terkena pembulatan bawaan floating-point.
    """

    if not isinstance(value, str):
        raise ContractValidationError("invalid_decimal")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ContractValidationError("invalid_decimal") from error
    if not number.is_finite() or number <= 0:
        raise ContractValidationError("invalid_decimal")
    return number
