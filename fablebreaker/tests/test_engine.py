"""Tests for the FableBreaker Analysis Engine."""

from __future__ import annotations

import unittest

from fablebreaker.engine import (
    AnalysisEngine,
    AnalysisReport,
    classify_family,
)
from fablebreaker.tokenomics.runtime_loop import TaskComplexity, TaskRisk


class TestClassifyFamily(unittest.TestCase):
    def test_known_family(self) -> None:
        c = classify_family("overflow_corridor")
        self.assertEqual(c.task_type, "overflow_corridor")
        self.assertEqual(c.complexity, TaskComplexity.HIGH)
        self.assertEqual(c.risk, TaskRisk.HIGH)
        self.assertIn("astlang", c.modules_needed)

    def test_unknown_family_defaults(self) -> None:
        c = classify_family("unknown_family")
        self.assertEqual(c.task_type, "unknown_family")
        self.assertEqual(c.complexity, TaskComplexity.MEDIUM)
        self.assertEqual(c.risk, TaskRisk.MODERATE)

    def test_critical_family(self) -> None:
        c = classify_family("nested_conditional_cascade")
        self.assertEqual(c.complexity, TaskComplexity.CRITICAL)
        self.assertEqual(c.risk, TaskRisk.CRITICAL)


class TestAnalysisReport(unittest.TestCase):
    def test_report_creation(self) -> None:
        report = AnalysisReport(
            candidate="test_candidate",
            dataset="test_dataset",
            cases=100,
            correct=95,
            failed=5,
            certified=False,
        )
        self.assertEqual(report.candidate, "test_candidate")
        self.assertFalse(report.certified)
        self.assertTrue(report.timestamp_utc)

    def test_report_to_dict(self) -> None:
        report = AnalysisReport(
            candidate="test",
            dataset="dataset/public.jsonl",
        )
        d = report.to_dict()
        self.assertIn("candidate", d)
        self.assertIn("evaluation", d)
        self.assertIn("tokenomics", d)
        self.assertIn("salience", d)
        self.assertIn("family_analyses", d)
        self.assertIn("evaluation_criteria", d)

    def test_report_hash_deterministic(self) -> None:
        report = AnalysisReport(
            candidate="test",
            dataset="test",
            timestamp_utc="2026-01-01T00:00:00Z",
        )
        h1 = report.compute_report_hash()
        h2 = report.compute_report_hash()
        self.assertEqual(h1, h2)
        self.assertTrue(len(h1) == 64)  # SHA-256 hex


class TestAnalysisEngine(unittest.TestCase):
    def test_analyze_scoring_result(self) -> None:
        engine = AnalysisEngine()
        scoring_result = {
            "candidate": "candidates.baseline_candidate",
            "dataset": "dataset/public.jsonl",
            "cases": 10,
            "correct": 10,
            "failed": 0,
            "certified": True,
            "speedup_vs_reference": 1.5,
            "family_breakdown": {
                "overflow_corridor": {
                    "count": 5,
                    "correct": 5,
                    "pass_rate": 1.0,
                    "speedup": 1.5,
                    "candidate_median_ms": 0.5,
                    "candidate_p95_ms": 0.8,
                    "candidate_p99_ms": 1.0,
                    "ci_95_ms": [0.3, 0.7],
                },
                "del_erasure_trap": {
                    "count": 5,
                    "correct": 5,
                    "pass_rate": 1.0,
                    "speedup": 2.0,
                    "candidate_median_ms": 0.3,
                    "candidate_p95_ms": 0.5,
                    "candidate_p99_ms": 0.6,
                    "ci_95_ms": [0.2, 0.4],
                },
            },
        }
        report = engine.analyze_scoring_result(scoring_result)

        self.assertEqual(report.candidate, "candidates.baseline_candidate")
        self.assertTrue(report.certified)
        self.assertEqual(report.cases, 10)
        self.assertEqual(len(report.family_analyses), 2)
        self.assertIn("overflow_corridor", report.family_analyses)
        self.assertIn("del_erasure_trap", report.family_analyses)

        # Check CRPT is computed
        self.assertGreater(report.aggregate_crpt, 0)

        # Check evaluation criteria are computed
        self.assertIn("cognitive_return_per_token", report.evaluation_criteria)
        self.assertIn("error_avoidance", report.evaluation_criteria)
        self.assertEqual(report.evaluation_criteria["error_avoidance"], 1.0)

        # Check report hash
        self.assertTrue(len(report.report_hash) == 64)

        # Check salience ranking
        self.assertEqual(len(report.salience_ranking), 2)

    def test_analyze_with_failures(self) -> None:
        engine = AnalysisEngine()
        scoring_result = {
            "candidate": "bad_candidate",
            "dataset": "dataset/public.jsonl",
            "cases": 10,
            "correct": 7,
            "failed": 3,
            "certified": False,
            "speedup_vs_reference": 0.0,
            "family_breakdown": {
                "overflow_corridor": {
                    "count": 5,
                    "correct": 2,
                    "pass_rate": 0.4,
                    "speedup": 0.0,
                    "candidate_median_ms": 1.0,
                },
                "branch_balance": {
                    "count": 5,
                    "correct": 5,
                    "pass_rate": 1.0,
                    "speedup": 1.2,
                    "candidate_median_ms": 0.4,
                },
            },
        }
        report = engine.analyze_scoring_result(scoring_result)

        self.assertFalse(report.certified)
        # Failing family should get higher urgency in salience ranking
        ranked_ids = [f for f, _ in report.salience_ranking]
        # overflow_corridor should rank higher (it failed)
        self.assertEqual(ranked_ids[0], "overflow_corridor")

    def test_analyze_empty_breakdown(self) -> None:
        engine = AnalysisEngine()
        report = engine.analyze_scoring_result({
            "candidate": "empty",
            "dataset": "none",
            "cases": 0,
            "correct": 0,
            "failed": 0,
            "certified": True,
            "family_breakdown": {},
        })
        self.assertEqual(report.aggregate_crpt, 0.0)
        self.assertEqual(len(report.evaluation_criteria), 0)

    def test_analyze_families_standalone(self) -> None:
        engine = AnalysisEngine()
        families_data = {
            "overflow_corridor": {
                "count": 5,
                "correct": 5,
                "pass_rate": 1.0,
                "speedup": 2.0,
                "candidate_median_ms": 0.5,
            },
        }
        results = engine.analyze_families(families_data)
        self.assertIn("overflow_corridor", results)
        self.assertGreater(results["overflow_corridor"]["crpt"], 0)
        self.assertGreater(results["overflow_corridor"]["cognitive_return"], 0)

    def test_family_analysis_structure(self) -> None:
        engine = AnalysisEngine()
        scoring_result = {
            "candidate": "test",
            "dataset": "test",
            "cases": 5,
            "correct": 5,
            "failed": 0,
            "certified": True,
            "speedup_vs_reference": 1.0,
            "family_breakdown": {
                "modular_arithmetic_net": {
                    "count": 5,
                    "correct": 5,
                    "pass_rate": 1.0,
                    "speedup": 1.0,
                    "candidate_median_ms": 1.0,
                },
            },
        }
        report = engine.analyze_scoring_result(scoring_result)
        fa = report.family_analyses["modular_arithmetic_net"]

        # Verify all expected fields are present
        self.assertIn("family", fa)
        self.assertIn("classification", fa)
        self.assertIn("pass_rate", fa)
        self.assertIn("speedup", fa)
        self.assertIn("cognitive_return", fa)
        self.assertIn("crpt", fa)
        self.assertIn("decision_quality", fa)
        self.assertIn("actionability", fa)
        self.assertIn("risk_control", fa)
        self.assertIn("reuse_value", fa)
        self.assertIn("accuracy", fa)
        self.assertIn("compression_efficiency", fa)
        self.assertIn("estimated_budget", fa)


if __name__ == "__main__":
    unittest.main()
