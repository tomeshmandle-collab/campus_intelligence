"""
Automated Test Suite for Issue P1-2: Automated Text Extraction & OCR Benchmark Evaluation
CAI Campus Intelligence — P1 Quality & Test Assets (M12)
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = TESTS_DIR / "scripts"
REPORTS_DIR = TESTS_DIR / "reports"
EVAL_SCRIPT_PATH = SCRIPTS_DIR / "eval_extraction.py"
REPORT_PATH = REPORTS_DIR / "extraction_benchmark.json"


class TestExtractionBenchmark(unittest.TestCase):
    """Test suite verifying text extraction evaluation and benchmark reporting."""

    @classmethod
    def setUpClass(cls):
        # Ensure benchmark script has run and report exists
        if not REPORT_PATH.is_file():
            subprocess.run([sys.executable, str(EVAL_SCRIPT_PATH)], check=True)
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            cls.report = json.load(f)

    def test_eval_extraction_script_exists(self):
        """Assert that tests/scripts/eval_extraction.py exists."""
        self.assertTrue(EVAL_SCRIPT_PATH.is_file(), f"eval_extraction.py not found at {EVAL_SCRIPT_PATH}")

    def test_eval_extraction_script_execution(self):
        """Assert that eval_extraction.py executes with exit code 0."""
        result = subprocess.run(
            [sys.executable, str(EVAL_SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"eval_extraction.py failed with code {result.returncode}:\n{result.stdout}\n{result.stderr}",
        )

    def test_benchmark_report_structure(self):
        """Assert extraction_benchmark.json contains required summary keys and results."""
        self.assertIn("benchmark_timestamp", self.report)
        self.assertIn("extractor_source", self.report)
        self.assertIn("summary", self.report)
        self.assertIn("robustness_simulations", self.report)
        self.assertIn("notice_results", self.report)

        summary = self.report["summary"]
        self.assertIn("total_notices", summary)
        self.assertIn("page_preservation_accuracy_pct", summary)
        self.assertIn("scanned_detection_accuracy_pct", summary)
        self.assertIn("average_keyword_recall_pct", summary)
        self.assertIn("overall_benchmark_passed", summary)

    def test_page_preservation_accuracy_threshold(self):
        """Assert that page boundary preservation accuracy meets or exceeds 90%."""
        page_acc = self.report["summary"]["page_preservation_accuracy_pct"]
        self.assertGreaterEqual(page_acc, 90.0, f"Page preservation accuracy {page_acc}% < 90.0%")

    def test_scanned_notice_detection_accuracy(self):
        """Assert that scanned notice detection accuracy meets or exceeds 90%."""
        scanned_acc = self.report["summary"]["scanned_detection_accuracy_pct"]
        self.assertGreaterEqual(scanned_acc, 90.0, f"Scanned detection accuracy {scanned_acc}% < 90.0%")

    def test_average_keyword_recall_threshold(self):
        """Assert that average title keyword recall meets or exceeds 80%."""
        recall = self.report["summary"]["average_keyword_recall_pct"]
        self.assertGreaterEqual(recall, 80.0, f"Average keyword recall {recall}% < 80.0%")

    def test_robustness_failure_simulations(self):
        """Assert that malformed and empty files are handled gracefully without unhandled exceptions."""
        robustness = self.report["robustness_simulations"]
        self.assertTrue(
            robustness["empty_file_handled_gracefully"],
            "Empty PDF was not handled gracefully!",
        )
        self.assertTrue(
            robustness["corrupt_file_handled_gracefully"],
            "Corrupt PDF was not handled gracefully!",
        )

    def test_all_16_notices_evaluated(self):
        """Assert that all 16 benchmark notice fixtures were evaluated."""
        results = self.report["notice_results"]
        self.assertEqual(len(results), 16, f"Expected 16 evaluated notice records, got {len(results)}")


if __name__ == "__main__":
    unittest.main()
