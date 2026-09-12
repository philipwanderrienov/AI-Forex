import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import inspect_quarantine_candles as inspector

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("inventory_simulator", ROOT / "mt5-bridge/tools/mt5_simulator.py")
simulator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = simulator
SPEC.loader.exec_module(simulator)


class QuarantineInventoryTests(unittest.TestCase):
    def test_validates_checksum_converts_wib_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            envelope = simulator.candle_envelope(118, instrument="XAUUSD", timeframe="H1")
            self.write_pair(directory, "good", envelope)
            broken = simulator.candle_envelope(119, instrument="XAUUSD", timeframe="H1")
            broken["records"][0]["close"] = "9999.00"
            self.write_pair(directory, "broken", broken)
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            report = inspector.inventory(directory, "XAUUSD", "H1")
            self.assertEqual(2, report["payloadFiles"])
            self.assertEqual(1, report["validatedPayloads"])
            self.assertEqual(1, report["selectedRecords"])
            self.assertEqual(1, len(report["errors"]))
            row = report["records"][0]
            self.assertEqual(118, row["sequence"])
            self.assertEqual("http_409", row["rejection"])
            self.assertTrue(row["openTimeWib"].endswith("+07:00"))
            self.assertNotIn("not-for-output", json.dumps(report))
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_accepts_legacy_timestamp_without_modifying_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            envelope = simulator.candle_envelope(2, instrument="XAUUSD", timeframe="H1")
            record = envelope["records"][0]
            from datetime import datetime
            from forex_intelligence_bridge.contracts import records_checksum
            original = record["openTime"]
            record["openTime"] = datetime.fromisoformat(original.replace("Z", "+00:00")).strftime("%Y.%m.%d %H:%M:%S")
            envelope["checksum"] = records_checksum(envelope["records"])
            self.write_pair(Path(tmp), "legacy", envelope)
            report = inspector.inventory(Path(tmp), "XAUUSD", "H1")
            self.assertEqual([], report["errors"])
            self.assertEqual(original, report["records"][0]["openTimeUtc"])
            self.assertEqual(record["openTime"], report["records"][0]["originalOpenTime"])

    def test_reports_missing_pairs_and_nonexistent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.write_pair(directory, "one", simulator.candle_envelope(1))
            (directory / "one.meta.json").unlink()
            (directory / "orphan.meta.json").write_text("{}")
            report = inspector.inventory(directory, "XAUUSD", "H1")
            self.assertEqual(2, len(report["errors"]))
            self.assertEqual(0, report["selectedRecords"])
            with self.assertRaises(ValueError):
                inspector.inventory(directory / "absent", "XAUUSD", "H1")

    @staticmethod
    def write_pair(directory, stem, envelope):
        (directory / f"{stem}.json").write_text(json.dumps(envelope))
        (directory / f"{stem}.meta.json").write_text(json.dumps({"detail": "HTTP 409: not-for-output"}))
