from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.scripts.product_report.build_report import (
    ReportInputs,
    build_report,
    load_gates,
    load_jsonl,
)
from src.scripts.product_report.check_gates import check_summary


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "rag_quality"


class ProductReportTests(unittest.TestCase):
    def test_load_jsonl(self) -> None:
        rows = load_jsonl(DEMO / "questions.jsonl")
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["question_id"], "qst_demo_001")

    def test_build_report_outputs_artifacts_and_passes_demo_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            summary = build_report(
                ReportInputs(
                    questions=DEMO / "questions.jsonl",
                    answers=DEMO / "answers.jsonl",
                    results=DEMO / "results.json",
                    gates=ROOT / "quality_gates.yaml",
                    output=output,
                    comparative_results=DEMO / "results-comparative.json",
                )
            )

            self.assertEqual(summary["launch_status"], "pass")
            self.assertEqual(summary["aggregate"]["completed_questions"], 5)
            self.assertEqual(summary["failures_by_risk"]["high"], 1)
            self.assertIsNotNone(summary["comparative"])
            self.assertTrue((output / "summary.json").exists())
            self.assertTrue((output / "failure_cases.csv").exists())
            self.assertTrue((output / "report" / "index.html").exists())
            self.assertIn(
                "qst_demo_005",
                (output / "failure_cases.csv").read_text(),
            )
            self.assertTrue(check_summary(summary))

    def test_strict_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            gates_path = tmp_path / "strict.yaml"
            gates_path.write_text(
                "launch_thresholds:\n"
                "  min_correctness_pct: 95\n"
                "  min_completeness_pct: 95\n"
                "  min_document_recall_pct: 95\n"
                "  max_invalid_extra_docs_avg: 0\n"
                "  max_launch_blocking_failures: 0\n"
            )
            gates = load_gates(gates_path)
            self.assertEqual(gates["launch_thresholds"]["min_correctness_pct"], 95)

            summary = build_report(
                ReportInputs(
                    questions=DEMO / "questions.jsonl",
                    answers=DEMO / "answers.jsonl",
                    results=DEMO / "results.json",
                    gates=gates_path,
                    output=tmp_path / "out",
                )
            )
            self.assertEqual(summary["launch_status"], "fail")
            self.assertFalse(check_summary(summary))


if __name__ == "__main__":
    unittest.main()

