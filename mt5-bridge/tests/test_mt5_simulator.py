import re
import unittest

from forex_intelligence_bridge.contracts import (
    ContractValidationError,
    records_checksum,
    validate_candle_envelope,
    validate_heartbeat,
)
from tools import mt5_simulator


class Mt5SimulatorPayloadTests(unittest.TestCase):
    def test_heartbeat_uses_bridge_contract(self) -> None:
        payload = mt5_simulator.heartbeat()

        self.assertIs(payload, validate_heartbeat(payload))
        self.assertEqual(mt5_simulator.SOURCE_INSTANCE_ID, payload["sourceInstanceId"])

    def test_valid_h1_envelope_uses_bridge_contract(self) -> None:
        payload = mt5_simulator.candle_envelope(7)

        self.assertIs(payload, validate_candle_envelope(payload))
        self.assertEqual(7, payload["sequence"])
        self.assertEqual("EURUSD", payload["records"][0]["instrument"])
        self.assertEqual("H1", payload["records"][0]["timeframe"])
        self.assertEqual("FINAL", payload["records"][0]["status"])

    def test_batch_id_is_a_valid_ulid_shape(self) -> None:
        batch_id = mt5_simulator.random_ulid()

        self.assertRegex(batch_id, re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$"))

    def test_explicit_batch_id_can_be_reused_for_duplicate_scenario(self) -> None:
        batch_id = "01J5J5Y22B8NKZ4M6KW7MPNN6C"

        first = mt5_simulator.candle_envelope(1, batch_id=batch_id)
        duplicate = mt5_simulator.candle_envelope(1, batch_id=batch_id)

        self.assertEqual(batch_id, first["batchId"])
        self.assertEqual(batch_id, duplicate["batchId"])

    def test_invalid_ohlc_scenario_has_valid_checksum_and_fails_ohlc_rule(self) -> None:
        payload = mt5_simulator.candle_envelope(1, invalid_ohlc=True)

        self.assertEqual(records_checksum(payload["records"]), payload["checksum"])
        with self.assertRaises(ContractValidationError) as context:
            validate_candle_envelope(payload)
        self.assertEqual("invalid_ohlc", context.exception.code)


if __name__ == "__main__":
    unittest.main()
