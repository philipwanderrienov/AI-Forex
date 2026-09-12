"""Execute actual exporter guard functions with simulated MQL platform adapters.

This checks algorithm behavior using C++; it is not a MetaEditor compile or Wine test.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ExporterGuardTests(unittest.TestCase):
    def test_state_loss_conflicts_disk_failure_and_clock_readiness(self):
        compiler = shutil.which("c++")
        if compiler is None:
            self.skipTest("C++ compiler required for exporter guard harness")
        source = (ROOT / "mt5-exporter/ForexIntelligenceDataExporter.mq5").read_text()
        functions = source[source.index("bool ValidSequenceValue("):source.index("string BuildCheckpointStorageKey(")]
        harness = (ROOT / "mt5-exporter/tests/guard_harness.cpp").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "guards.cpp"
            binary = Path(tmp) / "guards"
            cpp.write_text(harness.replace("// EXPORTER_GUARD_FUNCTIONS", functions))
            build = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(0, build.returncode, build.stderr)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
            self.assertIn("guard scenarios passed", result.stdout)


    def test_unconfigured_attachment_cannot_publish_or_touch_state(self):
        compiler = shutil.which("c++")
        if compiler is None:
            self.skipTest("C++ compiler required for exporter lifecycle harness")
        source = (ROOT / "mt5-exporter/ForexIntelligenceDataExporter.mq5").read_text()
        callbacks = source[source.index("int AwaitConfiguration("):]
        harness = (ROOT / "mt5-exporter/tests/startup_harness.cpp").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "startup.cpp"
            binary = Path(tmp) / "startup"
            cpp.write_text(harness.replace("// EXPORTER_LIFECYCLE", callbacks))
            build = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
                capture_output=True, text=True)
            self.assertEqual(0, build.returncode, build.stderr)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
            self.assertIn("startup scenarios passed", result.stdout)
