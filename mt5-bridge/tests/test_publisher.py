import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from forex_intelligence_bridge.publisher import (
    BackendPublisher,
    PublishDisposition,
    PublishResult,
    SpoolReplayer,
)
from forex_intelligence_bridge.spool import EnvelopeSpool
from test_contracts import valid_envelope


class ScriptedPublisher:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = 0

    def publish(self, envelope):
        self.calls += 1
        return self.results.pop(0)


class SpoolReplayerTests(unittest.TestCase):
    def test_ack_removes_pending_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            spool.enqueue(valid_envelope())
            publisher = ScriptedPublisher(PublishResult(PublishDisposition.ACK, 202))

            result = SpoolReplayer(spool, publisher).replay_one()

            self.assertEqual(PublishDisposition.ACK, result.disposition)
            self.assertEqual(0, spool.status()["depth"])
            self.assertEqual(0, spool.status()["quarantineDepth"])

    def test_transient_failure_retries_then_acknowledges(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            spool.enqueue(valid_envelope())
            publisher = ScriptedPublisher(
                PublishResult(PublishDisposition.RETRY, 503),
                PublishResult(PublishDisposition.RETRY, 429),
                PublishResult(PublishDisposition.ACK, 202),
            )
            delays = []

            result = SpoolReplayer(
                spool,
                publisher,
                max_attempts=3,
                base_delay_seconds=1,
                max_delay_seconds=10,
                sleep=delays.append,
                random_value=lambda: 0.5,
            ).replay_one()

            self.assertEqual(PublishDisposition.ACK, result.disposition)
            self.assertEqual(3, publisher.calls)
            self.assertEqual([0.5, 1.0], delays)
            self.assertEqual(0, spool.status()["depth"])

    def test_exhausted_transient_failure_keeps_envelope_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            spool.enqueue(valid_envelope())
            publisher = ScriptedPublisher(
                PublishResult(PublishDisposition.RETRY, 503),
                PublishResult(PublishDisposition.RETRY, 503),
            )

            result = SpoolReplayer(
                spool,
                publisher,
                max_attempts=2,
                sleep=lambda _: None,
            ).replay_one()

            self.assertEqual(PublishDisposition.RETRY, result.disposition)
            self.assertEqual(1, spool.status()["depth"])
            self.assertEqual(0, spool.status()["quarantineDepth"])

    def test_permanent_failure_is_quarantined_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            spool.enqueue(valid_envelope())
            publisher = ScriptedPublisher(
                PublishResult(PublishDisposition.PERMANENT_FAILURE, 400, "invalid envelope")
            )

            result = SpoolReplayer(spool, publisher, max_attempts=5).replay_one()

            self.assertEqual(PublishDisposition.PERMANENT_FAILURE, result.disposition)
            self.assertEqual(1, publisher.calls)
            self.assertEqual(0, spool.status()["depth"])
            self.assertEqual(1, spool.status()["quarantineDepth"])
            quarantined = spool.quarantined_items()[0]
            metadata = json.loads(
                quarantined.with_name(quarantined.stem + ".meta.json").read_text(encoding="utf-8")
            )
            self.assertEqual("permanent_backend_rejection", metadata["reason"])
            self.assertIn("HTTP 400", metadata["detail"])
            self.assertIn("invalid envelope", metadata["detail"])

    def test_permanent_failure_does_not_block_next_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            first = valid_envelope()
            second = valid_envelope()
            second["sequence"] += 1
            second["batchId"] = "01J5J5Y22B8NKZ4M6KW7MPNN6D"
            spool.enqueue(first)
            spool.enqueue(second)
            publisher = ScriptedPublisher(
                PublishResult(PublishDisposition.PERMANENT_FAILURE, 400, "bad first"),
                PublishResult(PublishDisposition.ACK, 202),
            )
            replayer = SpoolReplayer(spool, publisher)

            first_result = replayer.replay_one()
            second_result = replayer.replay_one()

            self.assertEqual(PublishDisposition.PERMANENT_FAILURE, first_result.disposition)
            self.assertEqual(PublishDisposition.ACK, second_result.disposition)
            self.assertEqual(2, publisher.calls)
            self.assertEqual(0, spool.status()["depth"])
            self.assertEqual(1, spool.status()["quarantineDepth"])

    def test_empty_spool_does_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            publisher = ScriptedPublisher()

            self.assertIsNone(SpoolReplayer(spool, publisher).replay_one())
            self.assertEqual(0, publisher.calls)


class BackendPublisherTests(unittest.TestCase):
    def test_publish_sends_machine_api_key_and_acknowledges_success(self):
        response = MagicMock()
        response.status = 202
        response.__enter__.return_value = response
        api_key = "test-bridge-api-key-at-least-32-bytes"

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = BackendPublisher("http://127.0.0.1:5000/ingest", api_key).publish(
                valid_envelope()
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(api_key, request.get_header("X-bridge-api-key"))
        self.assertEqual(PublishDisposition.ACK, result.disposition)

    def test_api_key_must_be_at_least_32_bytes(self):
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            BackendPublisher("http://127.0.0.1:5000/ingest", "too-short")


if __name__ == "__main__":
    unittest.main()
