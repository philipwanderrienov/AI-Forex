import unittest

from forex_intelligence_bridge.health import HeartbeatMonitor


class AdjustableClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class HeartbeatMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = AdjustableClock()
        self.monitor = HeartbeatMonitor(self.clock)
        self.heartbeat = {
            "schemaVersion": "mt5-heartbeat.v1",
            "sourceInstanceId": "terminal-demo",
            "sentAt": "2026-08-20T01:00:00Z",
        }

    def test_status_is_unknown_before_first_heartbeat(self) -> None:
        self.assertEqual({"status": "UNKNOWN"}, self.monitor.snapshot())

    def test_freshness_follows_canonical_thresholds(self) -> None:
        self.monitor.record(self.heartbeat)

        cases = [(10.0, "HEALTHY"), (10.001, "WARNING"), (20.001, "STALE")]
        for age_seconds, expected_status in cases:
            with self.subTest(age_seconds=age_seconds):
                self.clock.value = age_seconds
                snapshot = self.monitor.snapshot()
                self.assertEqual(expected_status, snapshot["status"])
                self.assertEqual(age_seconds, snapshot["ageSeconds"])

    def test_latest_heartbeat_replaces_previous_source_details(self) -> None:
        self.monitor.record(self.heartbeat)
        replacement = dict(self.heartbeat)
        replacement["sourceInstanceId"] = "terminal-reconnected"
        replacement["sentAt"] = "2026-08-20T01:00:05Z"
        self.clock.value = 5.0

        self.monitor.record(replacement)

        snapshot = self.monitor.snapshot()
        self.assertEqual("terminal-reconnected", snapshot["sourceInstanceId"])
        self.assertEqual("2026-08-20T01:00:05Z", snapshot["sourceSentAt"])
        self.assertEqual(0.0, snapshot["ageSeconds"])
