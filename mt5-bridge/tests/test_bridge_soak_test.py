import unittest

from tools.bridge_soak_test import run_soak


class BridgeSoakTestToolTests(unittest.TestCase):
    def test_small_run_verifies_restart_replay_and_quarantine(self) -> None:
        result = run_soak(envelope_count=5, duplicate_every=2)

        self.assertEqual(5, result["envelopesAccepted"])
        self.assertEqual(2, result["duplicatesVerified"])
        self.assertEqual(4, result["acknowledged"])
        self.assertEqual(1, result["quarantined"])
        self.assertEqual(0, result["pendingAfterReplay"])


if __name__ == "__main__":
    unittest.main()
