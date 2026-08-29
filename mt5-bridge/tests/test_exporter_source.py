import re
import unittest
from pathlib import Path


EXPORTER_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "mt5-exporter"
    / "ForexIntelligenceDataExporter.mq5"
)


class ExporterSourcePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = EXPORTER_SOURCE.read_text(encoding="utf-8")

    def test_exporter_remains_read_only(self) -> None:
        forbidden_calls = (
            "OrderSend",
            "OrderSendAsync",
            "PositionClose",
            "PositionModify",
        )
        for call in forbidden_calls:
            with self.subTest(call=call):
                self.assertIsNone(re.search(rf"\b{call}\s*\(", self.source))

    def test_backfill_is_bounded_by_contract_batch_limit(self) -> None:
        self.assertIn("MaxBackfillBarsPerSeries<1 || MaxBackfillBarsPerSeries>100", self.source)
        self.assertIn("missing_count=available_count<MaxBackfillBarsPerSeries", self.source)

    def test_checkpoint_advances_only_after_bridge_ack(self) -> None:
        acknowledgement = self.source.index("if(status==202)")
        checkpoint_save = self.source.index("if(!SaveCheckpoint(", acknowledgement)
        self.assertGreater(checkpoint_save, acknowledgement)

    def test_historical_candles_are_read_in_chronological_order(self) -> None:
        self.assertIn("shift=checkpoint_shift-1", self.source)
        self.assertIn("shift--", self.source)
        self.assertIn("CopyRates(broker_symbol,timeframe,shift,1,rates)", self.source)

    def test_offset_change_pauses_backfill(self) -> None:
        self.assertIn("Backfill paused because broker UTC offset changed", self.source)


if __name__ == "__main__":
    unittest.main()
