import copy
import tempfile
import unittest
from pathlib import Path

from forex_intelligence_bridge.spool import (
    DuplicateBatchError,
    EnvelopeSpool,
    SequenceConflictError,
    SpoolFullError,
)
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

    def test_restart_recovers_pending_items_in_replay_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_process = EnvelopeSpool(root)
            second = valid_envelope()
            second["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
            second["sequence"] = 2
            first = valid_envelope()
            first["sequence"] = 1
            first_process.enqueue(second)
            first_process.enqueue(first)

            restarted_process = EnvelopeSpool(root)

            self.assertEqual([1, 2], [restarted_process._read(path)["sequence"] for path in restarted_process.items()])

    def test_exact_duplicate_batch_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            envelope = valid_envelope()
            first_path = spool.enqueue(envelope)
            duplicate_path = spool.enqueue(copy.deepcopy(envelope))

            self.assertEqual(first_path, duplicate_path)
            self.assertEqual(1, len(spool.items()))

    def test_conflicting_duplicate_batch_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            original = valid_envelope()
            spool.enqueue(original)
            changed = copy.deepcopy(original)
            changed["sequence"] = original["sequence"] + 1
            changed["sentAt"] = "2026-08-17T09:00:00Z"

            with self.assertRaises(DuplicateBatchError):
                spool.enqueue(changed)

            self.assertEqual(original, (spool.peek() or self.fail("expected original"))[1])

    def test_same_source_sequence_with_different_batch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            original = valid_envelope()
            spool.enqueue(original)
            conflict = copy.deepcopy(original)
            conflict["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"

            with self.assertRaises(SequenceConflictError):
                spool.enqueue(conflict)

            self.assertEqual(1, len(spool.items()))

    def test_same_sequence_is_allowed_for_different_source_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            first = valid_envelope()
            second = copy.deepcopy(first)
            second["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
            second["sourceInstanceId"] = "lubuntu-mt5-secondary"

            spool.enqueue(first)
            spool.enqueue(second)

            self.assertEqual(2, len(spool.items()))

    def test_full_spool_rejects_new_data_without_deleting_existing_item(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_items=1)
            spool.enqueue(valid_envelope())
            second = valid_envelope()
            second["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
            second["sequence"] += 1

            with self.assertRaises(SpoolFullError):
                spool.enqueue(second)

            self.assertEqual(1, len(spool.items()))

    def test_acknowledge_rejects_path_outside_spool(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory) / "spool")
            outside = Path(directory) / "outside.json"
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(ValueError):
                spool.acknowledge(outside)

    def test_status_reports_depth_capacity_and_full_state(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_items=1)
            empty_status = spool.status()
            self.assertEqual("AVAILABLE", empty_status["status"])
            self.assertEqual(0, empty_status["depth"])
            self.assertEqual(0, empty_status["usedBytes"])
            self.assertEqual(0.0, empty_status["utilizationPercent"])

            spool.enqueue(valid_envelope())
            full_status = spool.status()
            self.assertEqual("FULL", full_status["status"])
            self.assertEqual(1, full_status["depth"])
            self.assertGreater(full_status["usedBytes"], 0)
            self.assertGreater(full_status["utilizationPercent"], 0)

    def test_byte_capacity_rejects_item_that_would_exceed_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_bytes=1)
            with self.assertRaises(SpoolFullError):
                spool.enqueue(valid_envelope())
            self.assertEqual(0, spool.status()["depth"])


if __name__ == "__main__":
    unittest.main()
