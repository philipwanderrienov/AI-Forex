import copy
import json
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

    def test_enqueue_result_distinguishes_new_item_from_exact_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            envelope = valid_envelope()

            created = spool.enqueue_with_result(envelope)
            duplicate = spool.enqueue_with_result(copy.deepcopy(envelope))

            self.assertFalse(created.duplicate)
            self.assertTrue(duplicate.duplicate)
            self.assertEqual(created.path, duplicate.path)

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

    def test_corrupt_json_is_quarantined_and_does_not_block_healthy_item(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spool = EnvelopeSpool(root)
            corrupt = root / "corrupt.json"
            corrupt.write_text("{not-json", encoding="utf-8")
            healthy = valid_envelope()
            healthy_path = spool.enqueue(healthy)

            items = spool.items()

            self.assertEqual([healthy_path], items)
            self.assertFalse(corrupt.exists())
            self.assertEqual(1, len(spool.quarantined_items()))
            self.assertEqual(1, spool.status()["quarantineDepth"])

    def test_invalid_spool_shape_is_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spool = EnvelopeSpool(root)
            invalid = root / "invalid.json"
            invalid.write_text("[]", encoding="utf-8")

            self.assertEqual([], spool.items())
            self.assertFalse(invalid.exists())
            self.assertEqual(1, len(spool.quarantined_items()))

    def test_manual_quarantine_moves_payload_and_writes_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            pending = spool.enqueue(valid_envelope())

            quarantined = spool.quarantine(pending, "test_reason", "diagnostic detail")

            self.assertFalse(pending.exists())
            self.assertTrue(quarantined.exists())
            self.assertEqual(0, spool.status()["depth"])
            self.assertEqual(1, spool.status()["quarantineDepth"])
            metadata_path = quarantined.with_name(quarantined.stem + ".meta.json")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual("test_reason", metadata["reason"])
            self.assertEqual("diagnostic detail", metadata["detail"])
            self.assertEqual(pending.name, metadata["originalName"])
            self.assertTrue(metadata["quarantinedAt"].endswith("Z"))

    def test_quarantine_rejects_path_outside_spool(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory) / "spool")
            outside = Path(directory) / "outside.json"
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(ValueError):
                spool.quarantine(outside, "outside")

    def test_quarantine_requires_non_empty_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            pending = spool.enqueue(valid_envelope())

            with self.assertRaises(ValueError):
                spool.quarantine(pending, "   ")
            self.assertTrue(pending.exists())

    def test_status_reports_depth_capacity_full_and_quarantine_state(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_items=1)
            empty_status = spool.status()
            self.assertEqual("AVAILABLE", empty_status["status"])
            self.assertEqual(0, empty_status["depth"])
            self.assertEqual(0, empty_status["usedBytes"])
            self.assertEqual(0.0, empty_status["utilizationPercent"])
            self.assertEqual(0, empty_status["quarantineDepth"])

            path = spool.enqueue(valid_envelope())
            full_status = spool.status()
            self.assertEqual("FULL", full_status["status"])
            self.assertEqual(1, full_status["depth"])
            self.assertGreater(full_status["usedBytes"], 0)
            self.assertGreater(full_status["utilizationPercent"], 0)

            spool.quarantine(path, "test")
            quarantined_status = spool.status()
            self.assertEqual("AVAILABLE", quarantined_status["status"])
            self.assertEqual(0, quarantined_status["depth"])
            self.assertEqual(1, quarantined_status["quarantineDepth"])

    def test_byte_capacity_rejects_item_that_would_exceed_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory), max_bytes=1)
            with self.assertRaises(SpoolFullError):
                spool.enqueue(valid_envelope())
            self.assertEqual(0, spool.status()["depth"])


if __name__ == "__main__":
    unittest.main()
