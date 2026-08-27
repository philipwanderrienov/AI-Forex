import copy
import unittest

from forex_intelligence_bridge.contracts import (
    MAX_RECORDS_PER_BATCH,
    ContractValidationError,
    records_checksum,
    validate_candle_envelope,
    validate_heartbeat,
)


def valid_envelope():
    payload = {
        "schemaVersion": "mt5-envelope.v1",
        "batchId": "01J5J5Y22B8NKZ4M6KW7MPNN6C",
        "sourceInstanceId": "lubuntu-mt5-primary",
        "brokerServerAlias": "primary-demo",
        "sequence": 18442,
        "sentAt": "2026-08-17T08:15:04.200Z",
        "payloadType": "CANDLES",
        "records": [
            {
                "schemaVersion": "candle.v1",
                "source": "MT5",
                "brokerServerAlias": "primary-demo",
                "brokerSymbol": "EURUSD.a",
                "instrument": "EURUSD",
                "timeframe": "H1",
                "openTime": "2026-08-17T07:00:00Z",
                "closeTime": "2026-08-17T08:00:00Z",
                "open": "1.17010",
                "high": "1.17220",
                "low": "1.16980",
                "close": "1.17160",
                "tickVolume": 1842,
                "status": "FINAL",
                "receivedAt": "2026-08-17T08:00:01.120Z",
                "dataQuality": "GOOD",
            }
        ],
        "checksum": "",
    }
    payload["checksum"] = records_checksum(payload["records"])
    return payload


def refresh_checksum(payload):
    payload["checksum"] = records_checksum(payload["records"])
    return payload


class CandleEnvelopeTests(unittest.TestCase):
    def test_valid_fixture_is_accepted(self):
        payload = valid_envelope()
        self.assertIs(payload, validate_candle_envelope(payload))

    def test_mt5_legacy_utc_timestamps_are_accepted(self):
        payload = valid_envelope()
        payload["sentAt"] = "2026.08.17 08:15:04"
        payload["records"][0]["openTime"] = "2026.08.17 07:00:00"
        payload["records"][0]["closeTime"] = "2026.08.17 08:00:00"
        payload["records"][0]["receivedAt"] = "2026.08.17 08:00:01"
        refresh_checksum(payload)
        self.assertIs(payload, validate_candle_envelope(payload))

    def test_multiple_valid_records_are_accepted_in_original_order(self):
        payload = valid_envelope()
        second = copy.deepcopy(payload["records"][0])
        second["instrument"] = "GBPUSD"
        second["brokerSymbol"] = "GBPUSD.a"
        second["open"] = "1.35000"
        second["high"] = "1.35200"
        second["low"] = "1.34900"
        second["close"] = "1.35100"
        payload["records"].append(second)
        refresh_checksum(payload)

        validated = validate_candle_envelope(payload)

        self.assertEqual(["EURUSD", "GBPUSD"], [r["instrument"] for r in validated["records"]])

    def test_missing_required_field_is_rejected(self):
        payload = valid_envelope()
        del payload["batchId"]
        self._assert_error(payload, "missing_required_field")

    def test_empty_records_are_rejected(self):
        payload = valid_envelope()
        payload["records"] = []
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_record_count")

    def test_record_limit_overflow_is_rejected(self):
        payload = valid_envelope()
        payload["records"] = [copy.deepcopy(payload["records"][0]) for _ in range(MAX_RECORDS_PER_BATCH + 1)]
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_record_count")

    def test_unsupported_payload_type_is_rejected(self):
        payload = valid_envelope()
        payload["payloadType"] = "TICKS"
        self._assert_error(payload, "unsupported_payload_type")

    def test_invalid_instrument_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["instrument"] = "USDIDR"
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_instrument")

    def test_invalid_enum_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["timeframe"] = "M5"
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_timeframe")

    def test_invalid_decimal_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["open"] = "NaN"
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_decimal")

    def test_non_positive_prices_are_rejected(self):
        for field in ("open", "high", "low", "close"):
            with self.subTest(field=field):
                payload = valid_envelope()
                payload["records"][0][field] = "0"
                refresh_checksum(payload)
                self._assert_error(payload, "invalid_decimal")

    def test_broker_alias_mismatch_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["brokerServerAlias"] = "other-demo"
        refresh_checksum(payload)
        self._assert_error(payload, "broker_alias_mismatch")

    def test_changed_record_checksum_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["close"] = "1.17161"
        self._assert_error(payload, "checksum_mismatch")

    def test_non_utc_boundary_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["closeTime"] = "2026-08-17T15:00:00+07:00"
        refresh_checksum(payload)
        self._assert_error(payload, "invalid_close_time")

    def test_timeframe_interval_mismatch_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["closeTime"] = "2026-08-17T07:15:00Z"
        refresh_checksum(payload)
        self._assert_error(payload, "timeframe_interval_mismatch")

    def test_future_final_candle_is_rejected(self):
        payload = valid_envelope()
        payload["sentAt"] = "2026-08-17T07:59:59Z"
        self._assert_error(payload, "candle_not_final")

    def test_negative_sequence_is_rejected(self):
        payload = valid_envelope()
        payload["sequence"] = -1
        self._assert_error(payload, "invalid_sequence")

    def _assert_error(self, payload, code):
        with self.assertRaises(ContractValidationError) as context:
            validate_candle_envelope(payload)
        self.assertEqual(code, context.exception.code)


class HeartbeatTests(unittest.TestCase):
    def test_valid_heartbeat_is_accepted(self):
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v1",
            "sourceInstanceId": "lubuntu-mt5-primary",
            "sentAt": "2026-08-20T01:00:00Z",
        }
        self.assertIs(heartbeat, validate_heartbeat(heartbeat))

    def test_mt5_legacy_utc_heartbeat_is_accepted(self):
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v1",
            "sourceInstanceId": "lubuntu-mt5-primary",
            "sentAt": "2026.08.20 01:00:00",
        }
        self.assertIs(heartbeat, validate_heartbeat(heartbeat))

    def test_wrong_schema_version_is_rejected(self):
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v2",
            "sourceInstanceId": "lubuntu-mt5-primary",
            "sentAt": "2026-08-20T01:00:00Z",
        }
        with self.assertRaises(ContractValidationError) as context:
            validate_heartbeat(heartbeat)
        self.assertEqual("unsupported_heartbeat_schema_version", context.exception.code)

    def test_non_utc_timestamp_is_rejected(self):
        heartbeat = {
            "schemaVersion": "mt5-heartbeat.v1",
            "sourceInstanceId": "lubuntu-mt5-primary",
            "sentAt": "2026-08-20T08:00:00+07:00",
        }
        with self.assertRaises(ContractValidationError) as context:
            validate_heartbeat(heartbeat)
        self.assertEqual("invalid_sent_at", context.exception.code)

    def test_invalid_shape_and_identity_are_rejected(self):
        cases = [
            ([], "invalid_heartbeat"),
            ({"schemaVersion": "mt5-heartbeat.v1"}, "missing_heartbeat_field"),
            (
                {
                    "schemaVersion": "mt5-heartbeat.v1",
                    "sourceInstanceId": "   ",
                    "sentAt": "2026-08-20T01:00:00Z",
                },
                "invalid_source_instance_id",
            ),
        ]
        for payload, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(ContractValidationError) as context:
                    validate_heartbeat(payload)
                self.assertEqual(expected_code, context.exception.code)


if __name__ == "__main__":
    unittest.main()
