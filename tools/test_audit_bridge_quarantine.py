import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("audit_bridge_quarantine.py")
SPEC = importlib.util.spec_from_file_location("audit_bridge_quarantine", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuditBridgeQuarantineTests(unittest.TestCase):
    def test_counts_rejections_and_exposes_only_safe_conflict_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            quarantine = Path(temporary_directory)
            self._write_pair(quarantine, "one", "HTTP 401: Unauthorized", sequence=10)
            self._write_pair(quarantine, "two", "HTTP 409: Conflict", sequence=11)

            report = MODULE.audit_quarantine(quarantine)

            self.assertEqual(2, report["total"])
            self.assertEqual({"http_401": 1, "http_409": 1}, report["counts"])
            self.assertEqual([], report["errors"])
            self.assertEqual(1, len(report["http409Entries"]))
            conflict = report["http409Entries"][0]
            self.assertEqual(11, conflict["sequence"])
            self.assertNotIn("records", conflict)
            self.assertNotIn("apiKey", conflict)

    def test_reports_missing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            quarantine = Path(temporary_directory)
            (quarantine / "orphan.meta.json").write_text(
                json.dumps({"detail": "HTTP 409: Conflict"}), encoding="utf-8"
            )

            report = MODULE.audit_quarantine(quarantine)

            self.assertEqual(2, len(report["errors"]))
            self.assertIn("paired payload is missing", report["errors"][0])
            self.assertIn("count mismatch", report["errors"][1])

    @staticmethod
    def _write_pair(directory: Path, stem: str, detail: str, sequence: int) -> None:
        metadata = {
            "detail": detail,
            "originalName": f"batch-{sequence}.json",
            "quarantinedAt": "2026-09-03T00:00:00Z",
            "reason": "permanent_backend_rejection",
        }
        payload = {
            "batchId": f"batch-{sequence}",
            "sourceInstanceId": "test-source",
            "sequence": sequence,
            "checksum": "sha256:" + ("a" * 64),
            "records": [{"secret": "not printed"}],
            "apiKey": "not printed",
        }
        (directory / f"{stem}.meta.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
        (directory / f"{stem}.json").write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
