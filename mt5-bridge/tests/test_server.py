import unittest

from forex_intelligence_bridge.server import MAX_BODY_BYTES


class BridgeConfigurationTests(unittest.TestCase):
    def test_body_limit_is_bounded(self) -> None:
        self.assertEqual(64 * 1024, MAX_BODY_BYTES)


if __name__ == "__main__":
    unittest.main()
