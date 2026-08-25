import tempfile
import unittest
from pathlib import Path

from forex_intelligence_bridge.publisher import (
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

    def test_permanent_failure_does_not_retry_or_acknowledge(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            spool.enqueue(valid_envelope())
            publisher = ScriptedPublisher(PublishResult(PublishDisposition.PERMANENT_FAILURE, 400))

            result = SpoolReplayer(spool, publisher, max_attempts=5).replay_one()

            self.assertEqual(PublishDisposition.PERMANENT_FAILURE, result.disposition)
            self.assertEqual(1, publisher.calls)
            self.assertEqual(1, spool.status()["depth"])

    def test_empty_spool_does_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = EnvelopeSpool(Path(directory))
            publisher = ScriptedPublisher()

            self.assertIsNone(SpoolReplayer(spool, publisher).replay_one())
            self.assertEqual(0, publisher.calls)


if __name__ == "__main__":
    unittest.main()
