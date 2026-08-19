import unittest

from forex_intelligence_bridge.contracts import (
    ContractValidationError,
    records_checksum,
    validate_candle_envelope,
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


class CandleEnvelopeTests(unittest.TestCase):
    def test_valid_fixture_is_accepted(self):
        payload = valid_envelope()

        self.assertIs(payload, validate_candle_envelope(payload))

    def test_missing_required_field_is_rejected(self):
        payload = valid_envelope()
        del payload["batchId"]

        self._assert_error(payload, "missing_required_field")

    def test_invalid_enum_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["timeframe"] = "M5"

        self._assert_error(payload, "invalid_timeframe")

    def test_invalid_decimal_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["open"] = "NaN"

        self._assert_error(payload, "invalid_decimal")

    def test_changed_record_checksum_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["close"] = "1.17161"

        self._assert_error(payload, "checksum_mismatch")

    def test_non_utc_boundary_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["closeTime"] = "2026-08-17T15:00:00+07:00"

        self._assert_error(payload, "invalid_close_time")

    def test_timeframe_interval_mismatch_is_rejected(self):
        payload = valid_envelope()
        payload["records"][0]["closeTime"] = "2026-08-17T07:15:00Z"

        self._assert_error(payload, "timeframe_interval_mismatch")

    def test_future_final_candle_is_rejected(self):
        payload = valid_envelope()
        payload["sentAt"] = "2026-08-17T07:59:59Z"

        self._assert_error(payload, "candle_not_final")

    def _assert_error(self, payload, code):
        with self.assertRaises(ContractValidationError) as context:
            validate_candle_envelope(payload)
        self.assertEqual(code, context.exception.code)


if __name__ == "__main__":
    unittest.main()
