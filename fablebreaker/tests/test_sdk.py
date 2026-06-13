"""Tests for the FableBreaker SDK."""

from __future__ import annotations

import json
import unittest

from fablebreaker.sdk import FableBreakerSDK, ProtocolsAccessor, TokenomicsAccessor
from fablebreaker.engine import AnalysisReport
from fablebreaker.tokenomics.token_value import TokenScores
from fablebreaker.tokenomics.salience import SalienceItem


class TestFableBreakerSDK(unittest.TestCase):
    def test_sdk_creation(self) -> None:
        sdk = FableBreakerSDK()
        self.assertIsNotNone(sdk.protocols)
        self.assertIsNotNone(sdk.tokenomics)
        self.assertIsNotNone(sdk.engine)

    def test_sdk_info(self) -> None:
        sdk = FableBreakerSDK()
        info = sdk.info()
        self.assertEqual(info["sdk_version"], "1.0.0")
        self.assertIn("foundation_doi", info)
        self.assertIn("protocols", info)
        self.assertIn("tokenomics", info)
        self.assertIn("evaluation_criteria", info)
        self.assertEqual(len(info["evaluation_criteria"]), 8)
        self.assertIn("task_classes", info)
        self.assertEqual(len(info["task_classes"]), 8)

    def test_sdk_constants(self) -> None:
        self.assertEqual(FableBreakerSDK.FOUNDATION_DOI, "10.5281/zenodo.20589250")
        self.assertIn("Medina", FableBreakerSDK.FOUNDATION_CITATION)

    def test_sdk_analyze_result(self) -> None:
        sdk = FableBreakerSDK()
        scoring_result = {
            "candidate": "test",
            "dataset": "test.jsonl",
            "cases": 5,
            "correct": 5,
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
                },
            },
        }
        report = sdk.analyze_result(scoring_result)
        self.assertIsInstance(report, AnalysisReport)
        self.assertTrue(report.certified)
        self.assertGreater(report.aggregate_crpt, 0)
        self.assertIn("overflow_corridor", report.family_analyses)

    def test_sdk_export_report(self) -> None:
        sdk = FableBreakerSDK()
        report = sdk.analyze_result({
            "candidate": "test",
            "dataset": "test.jsonl",
            "cases": 1,
            "correct": 1,
            "failed": 0,
            "certified": True,
            "family_breakdown": {
                "branch_balance": {
                    "count": 1, "correct": 1,
                    "pass_rate": 1.0, "speedup": 1.0,
                    "candidate_median_ms": 0.2,
                },
            },
        })
        json_str = sdk.export_report(report)
        parsed = json.loads(json_str)
        self.assertIn("candidate", parsed)
        self.assertIn("tokenomics", parsed)
        self.assertIn("salience", parsed)

    def test_sdk_classify_family(self) -> None:
        sdk = FableBreakerSDK()
        result = sdk.classify_family("nested_conditional_cascade")
        self.assertEqual(result["task_type"], "nested_conditional_cascade")
        self.assertEqual(result["complexity"], "critical")
        self.assertEqual(result["risk"], "critical")
        self.assertGreater(result["estimated_budget"], 0)
        self.assertIn("astlang", result["modules_needed"])


class TestProtocolsAccessor(unittest.TestCase):
    def test_list_protocols(self) -> None:
        accessor = ProtocolsAccessor()
        protocols = accessor.list_protocols()
        self.assertEqual(len(protocols), 5)
        self.assertIn("overflow_corridors", protocols)
        self.assertIn("governance_certification", protocols)

    def test_summary(self) -> None:
        accessor = ProtocolsAccessor()
        summary = accessor.summary()
        self.assertEqual(summary["total_papers"], 14)
        self.assertEqual(summary["journals"], 5)

    def test_protocol_access(self) -> None:
        accessor = ProtocolsAccessor()
        # Verify protocols are initialized and accessible
        result = accessor.overflow_corridors.generate(seed=42, size=10)
        self.assertTrue(result.valid)

        result = accessor.conditional_cascades.generate(seed=42, size=10)
        self.assertTrue(result.valid)

        # Governance works
        gov = accessor.governance_certification.create_governance_version(
            version="1.0.0",
            effective_date="2026-01-01",
            rules_hash="test",
            authority="ItsNotAI LABS",
        )
        self.assertEqual(gov.version, "1.0.0")

        # Per-family scoring works
        rec = accessor.per_family_scoring.minimum_sample_recommendation(10)
        self.assertFalse(rec["sufficient"])

        # API client works
        catalog = accessor.api_reproducibility.endpoint_catalog
        self.assertGreater(len(catalog), 0)

        # Registry works
        self.assertEqual(accessor.registry.paper_count, 14)


class TestTokenomicsAccessor(unittest.TestCase):
    def test_create_cognitive_metrics(self) -> None:
        accessor = TokenomicsAccessor()
        metrics = accessor.create_cognitive_metrics(
            decision_quality=4.0, actionability=3.0,
        )
        self.assertEqual(metrics.cognitive_return, 7.0)

    def test_create_compression_metrics(self) -> None:
        accessor = TokenomicsAccessor()
        m = accessor.create_compression_metrics(
            information_retained=3.0, action_clarity=3.0,
            risk_preserved=3.0, output_tokens=100,
        )
        self.assertTrue(m.passes_tokenomic_test())

    def test_create_salience_item(self) -> None:
        accessor = TokenomicsAccessor()
        item = accessor.create_salience_item("test", urgency=5.0, risk=3.0)
        self.assertEqual(item.id, "test")
        self.assertEqual(item.urgency, 5.0)

    def test_compute_token_value(self) -> None:
        accessor = TokenomicsAccessor()
        value = accessor.compute_token_value(TokenScores(decision_value=3.0))
        self.assertEqual(value, 3.0)

    def test_allocate_budget(self) -> None:
        accessor = TokenomicsAccessor()
        items = [
            SalienceItem(id="high", urgency=8.0),
            SalienceItem(id="low", urgency=2.0),
        ]
        allocation = accessor.allocate_budget(items, 1000)
        self.assertGreater(allocation["high"], allocation["low"])

    def test_summary(self) -> None:
        accessor = TokenomicsAccessor()
        summary = accessor.summary()
        self.assertIn("average_crpt", summary)
        self.assertIn("total_waste_rate", summary)
        self.assertIn("interactions_recorded", summary)
        self.assertIn("benchmark_results", summary)

    def test_static_functions(self) -> None:
        from fablebreaker.tokenomics.cognitive_return import CognitiveReturnMetrics
        crpt = TokenomicsAccessor.cognitive_return_per_token(
            CognitiveReturnMetrics(decision_quality=5.0), 100, 100,
        )
        self.assertGreater(crpt, 0)

        ce = TokenomicsAccessor.compression_efficiency(3.0, 3.0, 3.0, 100)
        self.assertAlmostEqual(ce, 0.09)

        gain = TokenomicsAccessor.tokenomic_gain(15.0, 100, 10.0, 200)
        self.assertAlmostEqual(gain, 0.10)


class TestSDKEndToEnd(unittest.TestCase):
    """End-to-end integration test using the SDK."""

    def test_full_workflow(self) -> None:
        sdk = FableBreakerSDK()

        # 1. Get system info
        info = sdk.info()
        self.assertIn("sdk_version", info)

        # 2. Generate adversarial expressions
        corridor = sdk.protocols.overflow_corridors.generate(seed=42, size=20)
        cascade = sdk.protocols.conditional_cascades.generate(seed=42, size=15)
        self.assertTrue(corridor.valid)
        self.assertTrue(cascade.valid)

        # 3. Analyze scoring results
        scoring = {
            "candidate": "test",
            "dataset": "test.jsonl",
            "cases": 3,
            "correct": 3,
            "failed": 0,
            "certified": True,
            "speedup_vs_reference": 1.5,
            "family_breakdown": {
                "overflow_corridor": {
                    "count": 1, "correct": 1,
                    "pass_rate": 1.0, "speedup": 1.5,
                    "candidate_median_ms": 0.5,
                },
                "nested_conditional_cascade": {
                    "count": 1, "correct": 1,
                    "pass_rate": 1.0, "speedup": 1.2,
                    "candidate_median_ms": 0.8,
                },
                "del_erasure_trap": {
                    "count": 1, "correct": 1,
                    "pass_rate": 1.0, "speedup": 2.0,
                    "candidate_median_ms": 0.3,
                },
            },
        }
        report = sdk.analyze_result(scoring)
        self.assertTrue(report.certified)
        self.assertGreater(report.aggregate_crpt, 0)

        # 4. Export report as JSON
        json_str = sdk.export_report(report)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["evaluation"]["certified"], True)
        self.assertGreater(len(parsed["family_analyses"]), 0)

        # 5. Verify tokenomics state
        summary = sdk.tokenomics.summary()
        self.assertGreater(summary["interactions_recorded"], 0)

        # 6. Create governance evidence pack
        gov = sdk.protocols.governance_certification.create_governance_version(
            version="1.0.0",
            effective_date="2026-01-01",
            rules_hash="abc123",
            authority="ItsNotAI LABS",
        )
        from fablebreaker.protocols.governance_certification import GovernanceRole
        role = sdk.protocols.governance_certification.grant_role(
            operator="operator@example.com",
            role=GovernanceRole.SCORING_OPERATOR,
            granted_by="admin@itsnotai.com",
        )
        pack = sdk.protocols.governance_certification.create_evidence_pack(
            suite_id="fablebreaker",
            candidate_name="test",
            candidate_source_ref="deadbeef",
            certified=True,
            speedup=1.5,
            governance_version=gov,
            operator_role=role,
        )
        self.assertTrue(pack.verify_integrity())


if __name__ == "__main__":
    unittest.main()
