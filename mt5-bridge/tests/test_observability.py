import io
import json
import logging
import unittest

from forex_intelligence_bridge.observability import JsonEventFormatter, configure_logging


class ObservabilityTests(unittest.TestCase):
    def tearDown(self):
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_formatter_outputs_valid_json_with_core_fields(self):
        formatter = JsonEventFormatter()
        record = logging.LogRecord(
            name="forex_intelligence_bridge.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="envelope_accepted",
            args=(),
            exc_info=None,
        )
        record.batchId = "01J5J5Y22B8NKZ4M6KW7MPNN6C"
        record.sequence = 42

        payload = json.loads(formatter.format(record))

        self.assertEqual("INFO", payload["level"])
        self.assertEqual("forex_intelligence_bridge.test", payload["logger"])
        self.assertEqual("envelope_accepted", payload["event"])
        self.assertEqual("01J5J5Y22B8NKZ4M6KW7MPNN6C", payload["batchId"])
        self.assertEqual(42, payload["sequence"])
        self.assertTrue(payload["timestamp"].endswith("Z"))

    def test_sensitive_fields_are_redacted_recursively(self):
        formatter = JsonEventFormatter()
        record = logging.LogRecord(
            name="forex_intelligence_bridge.test",
            level=logging.WARNING,
            pathname=__file__,
            lineno=20,
            msg="security_probe",
            args=(),
            exc_info=None,
        )
        record.api_key = "sk-do-not-log"
        record.Authorization = "Bearer secret-value"
        record.database = {
            "password": "db-secret",
            "host": "localhost",
            "nested": {"refreshToken": "refresh-secret"},
        }
        record.items = [{"secret": "one"}, {"value": "safe"}]

        payload = json.loads(formatter.format(record))

        self.assertEqual("[REDACTED]", payload["api_key"])
        self.assertEqual("[REDACTED]", payload["Authorization"])
        self.assertEqual("[REDACTED]", payload["database"]["password"])
        self.assertEqual("localhost", payload["database"]["host"])
        self.assertEqual("[REDACTED]", payload["database"]["nested"]["refreshToken"])
        self.assertEqual("[REDACTED]", payload["items"][0]["secret"])
        self.assertEqual("safe", payload["items"][1]["value"])

    def test_configure_logging_writes_one_json_event_per_line(self):
        stream = io.StringIO()
        configure_logging("INFO")
        root = logging.getLogger()
        self.assertEqual(1, len(root.handlers))
        root.handlers[0].stream = stream

        logger = logging.getLogger("forex_intelligence_bridge.test")
        logger.info("bridge_started", extra={"host": "127.0.0.1", "port": 8001})

        lines = [line for line in stream.getvalue().splitlines() if line.strip()]
        self.assertEqual(1, len(lines))
        payload = json.loads(lines[0])
        self.assertEqual("bridge_started", payload["event"])
        self.assertEqual("127.0.0.1", payload["host"])
        self.assertEqual(8001, payload["port"])

    def test_configure_logging_rejects_invalid_level(self):
        with self.assertRaises(ValueError):
            configure_logging("LOUD")

    def test_exception_logs_type_without_dumping_message_field_as_secret(self):
        formatter = JsonEventFormatter()
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="forex_intelligence_bridge.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=30,
            msg="publisher_failed",
            args=(),
            exc_info=exc_info,
        )

        payload = json.loads(formatter.format(record))

        self.assertEqual("RuntimeError", payload["exceptionType"])
        self.assertEqual("publisher_failed", payload["event"])


if __name__ == "__main__":
    unittest.main()
