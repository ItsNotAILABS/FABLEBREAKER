"""Tests for the Tokenomics Measurement and Benchmarking Framework."""

from __future__ import annotations

import unittest

from fablebreaker.tokenomics.token_value import (
    TokenScores,
    TokenValueFunction,
    TokenWeights,
    token_value,
)
from fablebreaker.tokenomics.cognitive_return import (
    CognitiveReturnMetrics,
    cognitive_return_per_token,
)
from fablebreaker.tokenomics.salience import (
    SalienceEngine,
    SalienceItem,
    SalienceWeights,
    allocate_budget,
    salience_score,
)
from fablebreaker.tokenomics.compression import (
    CompressionMetrics,
    compare_compression,
    compression_efficiency,
)
from fablebreaker.tokenomics.benchmark import (
    BenchmarkResult,
    BenchmarkRunner,
    TaskClass,
    TaskScore,
    tokenomic_gain,
)
from fablebreaker.tokenomics.runtime_loop import (
    InteractionRecord,
    RuntimeMeasurementLoop,
    TaskClassification,
    TaskComplexity,
    TaskRisk,
)


class TestTokenValueFunction(unittest.TestCase):
    def test_positive_value_token(self) -> None:
        scores = TokenScores(
            decision_value=3.0, action_usefulness=2.0, risk_reduction=1.0,
            compression_contribution=1.0, memory_value=2.0, noise=0.0,
        )
        tvf = TokenValueFunction()
        self.assertEqual(tvf.compute(scores), 9.0)

    def test_negative_value_token(self) -> None:
        scores = TokenScores(noise=5.0)
        tvf = TokenValueFunction()
        self.assertEqual(tvf.compute(scores), -5.0)

    def test_weighted_computation(self) -> None:
        weights = TokenWeights(decision=2.0, action=0.0, risk=0.0,
                               compression=0.0, memory=0.0, noise=1.0)
        scores = TokenScores(decision_value=3.0, noise=1.0)
        tvf = TokenValueFunction(weights=weights)
        self.assertEqual(tvf.compute(scores), 5.0)  # 2*3 - 1*1

    def test_batch_and_total(self) -> None:
        tvf = TokenValueFunction()
        batch = [
            TokenScores(decision_value=2.0),
            TokenScores(decision_value=3.0),
        ]
        self.assertEqual(tvf.total_value(batch), 5.0)

    def test_positive_ratio(self) -> None:
        tvf = TokenValueFunction()
        batch = [
            TokenScores(decision_value=2.0),
            TokenScores(noise=3.0),
            TokenScores(decision_value=1.0),
        ]
        self.assertAlmostEqual(tvf.positive_ratio(batch), 2 / 3)

    def test_simplified_token_value(self) -> None:
        result = token_value(
            decision_quality=3.0, actionability=2.0, risk_control=1.0,
            reuse=1.0, learning=1.0, waste=2.0,
        )
        self.assertEqual(result, 6.0)


class TestCognitiveReturnMetrics(unittest.TestCase):
    def test_cognitive_return(self) -> None:
        m = CognitiveReturnMetrics(
            decision_quality=4.0, actionability=3.0, risk_control=2.0,
            reuse_value=1.0, learning_gain=5.0,
        )
        self.assertEqual(m.cognitive_return, 15.0)

    def test_normalized(self) -> None:
        m = CognitiveReturnMetrics(
            decision_quality=5.0, actionability=5.0, risk_control=5.0,
            reuse_value=5.0, learning_gain=5.0,
        )
        self.assertEqual(m.normalized, 1.0)

    def test_validation(self) -> None:
        with self.assertRaises(ValueError):
            CognitiveReturnMetrics(decision_quality=6.0)
        with self.assertRaises(ValueError):
            CognitiveReturnMetrics(actionability=-1.0)

    def test_crpt(self) -> None:
        m = CognitiveReturnMetrics(
            decision_quality=4.0, actionability=3.0, risk_control=2.0,
            reuse_value=1.0, learning_gain=0.0,
        )
        crpt = cognitive_return_per_token(m, prompt_tokens=100, output_tokens=100)
        self.assertAlmostEqual(crpt, 10.0 / 200)

    def test_crpt_zero_tokens(self) -> None:
        m = CognitiveReturnMetrics(decision_quality=4.0)
        self.assertEqual(cognitive_return_per_token(m, 0, 0), 0.0)


class TestSalience(unittest.TestCase):
    def test_salience_score_default_weights(self) -> None:
        item = SalienceItem(
            id="test", urgency=3.0, risk=2.0, mission_relevance=4.0,
            time_sensitivity=1.0, novelty=2.0, known_context=1.0,
        )
        # 3 + 2 + 4 + 1 + 2 - 1 = 11
        self.assertEqual(salience_score(item), 11.0)

    def test_salience_known_context_reduces_score(self) -> None:
        item_novel = SalienceItem(id="a", urgency=3.0, known_context=0.0)
        item_known = SalienceItem(id="b", urgency=3.0, known_context=5.0)
        self.assertGreater(salience_score(item_novel), salience_score(item_known))

    def test_budget_allocation_proportional(self) -> None:
        items = [
            SalienceItem(id="high", urgency=8.0),
            SalienceItem(id="low", urgency=2.0),
        ]
        allocation = allocate_budget(items, total_budget=1000)
        self.assertGreater(allocation["high"], allocation["low"])
        self.assertEqual(allocation["high"], 800)
        self.assertEqual(allocation["low"], 200)

    def test_budget_allocation_negative_scores(self) -> None:
        items = [
            SalienceItem(id="a", known_context=10.0),  # negative score
            SalienceItem(id="b", urgency=5.0),
        ]
        allocation = allocate_budget(items, total_budget=1000)
        self.assertEqual(allocation["a"], 0)
        self.assertEqual(allocation["b"], 1000)

    def test_salience_engine_rank(self) -> None:
        engine = SalienceEngine()
        items = [
            SalienceItem(id="low", urgency=1.0),
            SalienceItem(id="high", urgency=5.0),
            SalienceItem(id="mid", urgency=3.0),
        ]
        ranked = engine.rank(items)
        self.assertEqual(ranked[0][0], "high")
        self.assertEqual(ranked[1][0], "mid")
        self.assertEqual(ranked[2][0], "low")

    def test_filter_above_threshold(self) -> None:
        engine = SalienceEngine()
        items = [
            SalienceItem(id="a", urgency=1.0),
            SalienceItem(id="b", urgency=5.0),
            SalienceItem(id="c", known_context=10.0),
        ]
        filtered = engine.filter_above_threshold(items, threshold=2.0)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, "b")


class TestCompression(unittest.TestCase):
    def test_compression_efficiency_basic(self) -> None:
        eff = compression_efficiency(4.0, 3.0, 2.0, output_tokens=100)
        self.assertAlmostEqual(eff, 9.0 / 100)

    def test_compression_efficiency_zero_tokens(self) -> None:
        self.assertEqual(compression_efficiency(4.0, 3.0, 2.0, 0), 0.0)

    def test_compression_metrics_passes_test(self) -> None:
        m = CompressionMetrics(
            information_retained=3.0, action_clarity=3.0,
            risk_preserved=3.0, output_tokens=100,
        )
        self.assertTrue(m.passes_tokenomic_test())

    def test_compression_metrics_fails_if_risk_zero(self) -> None:
        m = CompressionMetrics(
            information_retained=3.0, action_clarity=3.0,
            risk_preserved=0.0, output_tokens=100,
        )
        self.assertFalse(m.passes_tokenomic_test())

    def test_compare_compression(self) -> None:
        result = compare_compression(
            original_tokens=200, compressed_tokens=100,
            original_meaning=8.0, compressed_meaning=7.0,
        )
        self.assertAlmostEqual(result["compression_ratio"], 0.5)
        self.assertAlmostEqual(result["meaning_retention"], 7.0 / 8.0)
        self.assertGreater(result["efficiency_gain"], 0)


class TestBenchmark(unittest.TestCase):
    def test_task_score(self) -> None:
        score = TaskScore(
            decision_quality=4.0, actionability=3.0, risk_control=2.0,
            reuse_value=1.0, accuracy=5.0, waste=2.0, tokens_used=100,
        )
        self.assertEqual(score.total_score, 13.0)
        self.assertAlmostEqual(score.score_per_token, 0.13)

    def test_tokenomic_gain_function(self) -> None:
        gain = tokenomic_gain(score_b=15.0, tokens_b=100, score_a=10.0, tokens_a=200)
        # 15/100 - 10/200 = 0.15 - 0.05 = 0.10
        self.assertAlmostEqual(gain, 0.10)

    def test_benchmark_result(self) -> None:
        baseline = TaskScore(
            decision_quality=3.0, actionability=3.0, risk_control=2.0,
            reuse_value=1.0, accuracy=4.0, waste=3.0, tokens_used=500,
        )
        tokenomic = TaskScore(
            decision_quality=4.0, actionability=4.0, risk_control=3.0,
            reuse_value=2.0, accuracy=4.0, waste=1.0, tokens_used=200,
        )
        result = BenchmarkResult(
            task_class=TaskClass.INVOICE_EXECUTION,
            task_description="Test task",
            baseline_score=baseline,
            tokenomic_score=tokenomic,
        )
        self.assertTrue(result.is_tokenomic_superior)
        self.assertGreater(result.tokenomic_gain, 0)

    def test_benchmark_runner(self) -> None:
        runner = BenchmarkRunner()
        runner.add_result(BenchmarkResult(
            task_class=TaskClass.ESTIMATING,
            task_description="Estimate task",
            baseline_score=TaskScore(decision_quality=3.0, tokens_used=500),
            tokenomic_score=TaskScore(decision_quality=4.0, tokens_used=200),
        ))
        runner.add_result(BenchmarkResult(
            task_class=TaskClass.RED_TEAM_REVIEW,
            task_description="Red team",
            baseline_score=TaskScore(decision_quality=4.0, tokens_used=300),
            tokenomic_score=TaskScore(decision_quality=4.0, tokens_used=300),
        ))
        summary = runner.summary()
        self.assertEqual(summary["total_tasks"], 2)
        self.assertGreater(summary["win_rate"], 0)


class TestRuntimeMeasurementLoop(unittest.TestCase):
    def test_estimate_budget(self) -> None:
        loop = RuntimeMeasurementLoop()
        classification = TaskClassification(
            task_type="invoice", complexity=TaskComplexity.HIGH,
            risk=TaskRisk.MODERATE,
        )
        budget = loop.estimate_budget(classification)
        self.assertEqual(budget, int(1000 * 1.2))  # HIGH base * MODERATE multiplier

    def test_full_loop_run(self) -> None:
        loop = RuntimeMeasurementLoop()
        classification = TaskClassification(
            task_type="research", complexity=TaskComplexity.MEDIUM,
            risk=TaskRisk.LOW,
        )
        items = [
            SalienceItem(id="main", urgency=5.0, risk=3.0),
            SalienceItem(id="context", urgency=1.0),
        ]
        cognitive = CognitiveReturnMetrics(
            decision_quality=4.0, actionability=3.0, risk_control=2.0,
            reuse_value=2.0, learning_gain=1.0,
        )
        record = loop.run(
            task_classification=classification,
            salience_items=items,
            cognitive_scores=cognitive,
            compression_scores=(4.0, 3.0, 3.0),
            prompt_tokens=200,
            output_tokens=300,
            reusable_rules=["Use structured output for research tasks"],
        )
        self.assertGreater(record.crpt, 0)
        self.assertEqual(len(record.reusable_rules), 1)
        self.assertEqual(len(loop.history), 1)

    def test_policy_updates(self) -> None:
        loop = RuntimeMeasurementLoop()
        classification = TaskClassification(
            task_type="invoice", complexity=TaskComplexity.HIGH,
            risk=TaskRisk.LOW,
        )
        items = [SalienceItem(id="main", urgency=5.0)]
        cognitive = CognitiveReturnMetrics(
            decision_quality=5.0, actionability=5.0, risk_control=5.0,
            reuse_value=5.0, learning_gain=5.0,
        )
        # Run with much fewer tokens than budgeted to trigger policy reduction.
        loop.run(
            task_classification=classification,
            salience_items=items,
            cognitive_scores=cognitive,
            compression_scores=(5.0, 5.0, 5.0),
            prompt_tokens=50,
            output_tokens=100,
        )
        # Policy should have been adjusted downward for this task type.
        self.assertLess(loop.policy_adjustments.get("invoice", 1.0), 1.0)

    def test_waste_detection(self) -> None:
        loop = RuntimeMeasurementLoop()
        token_scores = [
            TokenScores(decision_value=3.0),
            TokenScores(noise=2.0),  # net negative
            TokenScores(decision_value=1.0),
            TokenScores(),  # zero value
        ]
        wasted = loop.detect_waste(token_scores)
        self.assertEqual(wasted, 2)  # negative and zero value tokens

    def test_average_crpt_and_waste_rate(self) -> None:
        loop = RuntimeMeasurementLoop()
        classification = TaskClassification(
            task_type="test", complexity=TaskComplexity.LOW, risk=TaskRisk.MINIMAL,
        )
        cognitive = CognitiveReturnMetrics(
            decision_quality=3.0, actionability=2.0, risk_control=1.0,
            reuse_value=1.0, learning_gain=1.0,
        )
        loop.run(
            task_classification=classification,
            salience_items=[SalienceItem(id="x", urgency=3.0)],
            cognitive_scores=cognitive,
            compression_scores=(3.0, 2.0, 2.0),
            prompt_tokens=100,
            output_tokens=200,
            token_scores=[TokenScores(noise=5.0)] * 10,
        )
        self.assertGreater(loop.average_crpt(), 0)
        self.assertGreater(loop.total_waste_rate(), 0)


if __name__ == "__main__":
    unittest.main()
