import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("verify_market_data_status.py")
SPEC = importlib.util.spec_from_file_location("verify_market_data_status", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyMarketDataStatusTests(unittest.TestCase):
    def test_valid_snapshot_has_no_errors(self):
        snapshot = self._snapshot()

        self.assertEqual([], MODULE.validate_snapshot(snapshot))

    def test_missing_duplicate_and_invalid_values_are_reported(self):
        snapshot = self._snapshot()
        snapshot["series"].pop()
        snapshot["series"].append(dict(snapshot["series"][0]))
        snapshot["series"][0]["status"] = "BROKEN"
        snapshot["series"][0]["gapCount"] = -1

        errors = MODULE.validate_snapshot(snapshot)

        self.assertTrue(any("Missing canonical series" in error for error in errors))
        self.assertTrue(any("Duplicate series" in error for error in errors))
        self.assertTrue(any("invalid status" in error for error in errors))
        self.assertTrue(any("invalid gapCount" in error for error in errors))

    @staticmethod
    def _snapshot():
        return {
            "status": "Fresh",
            "evaluatedAt": "2026-09-01T10:00:00Z",
            "marketOpen": True,
            "series": [
                {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "Fresh",
                    "lastOpenTime": "2026-09-01T09:45:00Z",
                    "lastCloseTime": "2026-09-01T10:00:00Z",
                    "ageMinutes": 0,
                    "gapCount": 0,
                }
                for instrument in MODULE.EXPECTED_INSTRUMENTS
                for timeframe in MODULE.EXPECTED_TIMEFRAMES
            ],
        }


if __name__ == "__main__":
    unittest.main()
