import tempfile
import unittest
from pathlib import Path

from forex_intelligence_bridge.spool import EnvelopeSpool, SpoolFullError
from test_contracts import valid_envelope


class EnvelopeSpoolTests(unittest.TestCase):
    def test_items_are_replayed_in_sequence_order(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            later = valid_envelope()
            later["sequence"] = 2
            later["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
            earlier = valid_envelope()
            earlier["sequence"] = 1

            spool.enqueue(later)
            spool.enqueue(earlier)

            path, envelope = spool.peek() or self.fail("expected queued envelope")
            self.assertEqual(1, envelope["sequence"])
            spool.acknowledge(path)
            self.assertEqual(2, (spool.peek() or self.fail("expected second envelope"))[1]["sequence"])

    def test_full_spool_rejects_new_data_without_deleting_existing_item(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_items=1)
            spool.enqueue(valid_envelope())

            with self.assertRaises(SpoolFullError):
                spool.enqueue(valid_envelope())

            self.assertEqual(1, len(spool.items()))

    def test_duplicate_batch_does_not_overwrite_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            original = valid_envelope()
            spool.enqueue(original)
            changed = valid_envelope()
            changed["sequence"] = original["sequence"] + 1
            changed["sentAt"] = "2026-08-17T09:00:00Z"

            with self.assertRaises(ValueError):
                spool.enqueue(changed)

            self.assertEqual(original, (spool.peek() or self.fail("expected original"))[1])

    def test_acknowledge_rejects_path_outside_spool(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory) / "spool")
            outside = Path(directory) / "outside.json"
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(ValueError):
                spool.acknowledge(outside)


if __name__ == "__main__":
    unittest.main()
