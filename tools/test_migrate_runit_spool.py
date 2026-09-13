import tempfile
import unittest
from pathlib import Path
from migrate_runit_spool import manifest, verified_copy


class MigrationTests(unittest.TestCase):
    def test_copy_preserves_pending_quarantine_and_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"
            (source / "quarantine").mkdir(parents=True)
            (source / "pending.json").write_text("pending")
            (source / "quarantine/item.json").write_text("payload")
            (source / "quarantine/item.meta.json").write_text("metadata")
            expected = manifest(source)
            self.assertEqual(expected, verified_copy(source, target))
            self.assertEqual(expected, manifest(source))
            self.assertEqual(expected, manifest(target))
            with self.assertRaises(ValueError):
                verified_copy(source, target)

    def test_symlink_and_missing_source_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            with self.assertRaises(ValueError):
                manifest(source)
            source.mkdir()
            (source / "link").symlink_to("/tmp")
            with self.assertRaises(ValueError):
                verified_copy(source, Path(tmp) / "target")
