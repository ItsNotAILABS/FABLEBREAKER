"""FableBreaker Analysis Engine.

The analysis engine routes evaluation results through the full tokenomic
measurement pipeline:

    1. Classify the task and estimate risk/complexity
    2. Rank salience targets from evaluation data
    3. Allocate token budget proportionally
    4. Score cognitive return across five categories
    5. Audit compression quality
    6. Detect wasted tokens
    7. Extract reusable rules and memory
    8. Compute Cognitive Return Per Token (CRPT)
    9. Update future allocation policy
    10. Produce a full analysis report

This module is the bridge between raw Fablebreaker evaluation results
(correctness, speedup, family breakdown) and the Tokenomics measurement
framework (CRPT, salience, compression efficiency, tokenomic gain).

Foundation: https://doi.org/10.5281/zenodo.20589250
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .scorer import score as run_scorer
from .tokenomics.token_value import TokenValueFunction, TokenWeights
from .tokenomics.cognitive_return import CognitiveReturnMetrics
from .tokenomics.salience import SalienceEngine, SalienceItem, SalienceWeights
from .tokenomics.compression import compression_efficiency
from .tokenomics.benchmark import (
    BenchmarkRunner, BenchmarkResult, TaskScore, TaskClass, tokenomic_gain,
)
from .tokenomics.runtime_loop import (
    RuntimeMeasurementLoop, TaskClassification, TaskComplexity, TaskRisk,
)


# ---------------------------------------------------------------------------
# Task classification heuristics
# ---------------------------------------------------------------------------

_FAMILY_COMPLEXITY: dict[str, TaskComplexity] = {
    "dynamic_match_storm": TaskComplexity.HIGH,
    "del_erasure_trap": TaskComplexity.MEDIUM,
    "duplication_aliasing": TaskComplexity.HIGH,
    "branch_balance": TaskComplexity.MEDIUM,
    "deep_pair_projection": TaskComplexity.MEDIUM,
    "modular_arithmetic_net": TaskComplexity.LOW,
    "overflow_corridor": TaskComplexity.HIGH,
    "nested_conditional_cascade": TaskComplexity.CRITICAL,
}

_FAMILY_RISK: dict[str, TaskRisk] = {
    "dynamic_match_storm": TaskRisk.MODERATE,
    "del_erasure_trap": TaskRisk.HIGH,
    "duplication_aliasing": TaskRisk.MODERATE,
    "branch_balance": TaskRisk.LOW,
    "deep_pair_projection": TaskRisk.LOW,
    "modular_arithmetic_net": TaskRisk.MINIMAL,
    "overflow_corridor": TaskRisk.HIGH,
    "nested_conditional_cascade": TaskRisk.CRITICAL,
}


def classify_family(family: str) -> TaskClassification:
    """Classify a benchmark family into a task classification."""
    return TaskClassification(
        task_type=family,
        complexity=_FAMILY_COMPLEXITY.get(family, TaskComplexity.MEDIUM),
        risk=_FAMILY_RISK.get(family, TaskRisk.MODERATE),
        modules_needed=["astlang", "generator", "scorer"],
    )


# ---------------------------------------------------------------------------
# Analysis report data class
# ---------------------------------------------------------------------------

@dataclass
class AnalysisReport:
    """Complete analysis report produced by the engine.

    Combines Fablebreaker evaluation results with tokenomic measurements
    into a unified report suitable for internal analysis and external
    consumption via the API.
    """

    # Evaluation identity
    candidate: str
    dataset: str
    timestamp_utc: str = ""

    # Core evaluation results
    cases: int = 0
    correct: int = 0
    failed: int = 0
    certified: bool = False
    speedup_vs_reference: float = 0.0

    # Per-family tokenomic analysis
    family_analyses: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Aggregate tokenomic metrics
    aggregate_crpt: float = 0.0
    aggregate_compression_efficiency: float = 0.0
    total_waste_rate: float = 0.0
    reuse_extraction_rate: float = 0.0

    # Salience allocation summary
    salience_ranking: list[tuple[str, float]] = field(default_factory=list)
    budget_allocation: dict[str, int] = field(default_factory=dict)

    # Evaluation criteria (Section 15.7)
    evaluation_criteria: dict[str, float] = field(default_factory=dict)

    # Report integrity
    report_hash: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp_utc:
            self.timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def compute_report_hash(self) -> str:
        """Compute SHA-256 hash of the report for integrity verification."""
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for API output or JSON export."""
        return {
            "candidate": self.candidate,
            "dataset": self.dataset,
            "timestamp_utc": self.timestamp_utc,
            "evaluation": {
                "cases": self.cases,
                "correct": self.correct,
                "failed": self.failed,
                "certified": self.certified,
                "speedup_vs_reference": self.speedup_vs_reference,
            },
            "tokenomics": {
                "aggregate_crpt": self.aggregate_crpt,
                "aggregate_compression_efficiency": self.aggregate_compression_efficiency,
                "total_waste_rate": self.total_waste_rate,
                "reuse_extraction_rate": self.reuse_extraction_rate,
            },
            "salience": {
                "ranking": [{"family": f, "score": s} for f, s in self.salience_ranking],
                "budget_allocation": self.budget_allocation,
            },
            "family_analyses": self.family_analyses,
            "evaluation_criteria": self.evaluation_criteria,
            "report_hash": self.report_hash,
        }


# ---------------------------------------------------------------------------
# Analysis Engine
# ---------------------------------------------------------------------------

class AnalysisEngine:
    """Routes Fablebreaker evaluation results through the tokenomic pipeline.

    The engine performs the full runtime measurement loop for each family
    in a benchmark evaluation, then aggregates results into a unified
    report with CRPT, salience allocation, compression audit, and the
    eight evaluation criteria from Section 15.7.

    Usage:
        engine = AnalysisEngine()

        # Analyze raw scoring results
        report = engine.analyze_scoring_result(scoring_result)

        # Or run end-to-end: score + analyze
        report = engine.run(dataset_path, candidate_module)

        # Compare tokenomic vs non-tokenomic systems
        result = engine.compare(dataset_path, candidate_a, candidate_b)
    """

    def __init__(
        self,
        salience_weights: SalienceWeights | None = None,
        token_weights: TokenWeights | None = None,
        default_budget: int = 1000,
    ) -> None:
        self.salience_engine = SalienceEngine(
            weights=salience_weights or SalienceWeights()
        )
        self.token_value_fn = TokenValueFunction(
            weights=token_weights or TokenWeights()
        )
        self.measurement_loop = RuntimeMeasurementLoop(
            salience_engine=self.salience_engine,
            token_value_fn=self.token_value_fn,
            default_budget=default_budget,
        )
        self.benchmark_runner = BenchmarkRunner()

    def analyze_scoring_result(
        self, scoring_result: dict[str, Any]
    ) -> AnalysisReport:
        """Analyze a scoring result dict through the full tokenomic pipeline.

        Args:
            scoring_result: Dictionary from scorer.score(), containing
                cases, correct, failed, certified, family_breakdown, etc.

        Returns:
            AnalysisReport with full tokenomic analysis.
        """
        report = AnalysisReport(
            candidate=scoring_result.get("candidate", "unknown"),
            dataset=scoring_result.get("dataset", "unknown"),
            cases=scoring_result.get("cases", 0),
            correct=scoring_result.get("correct", 0),
            failed=scoring_result.get("failed", 0),
            certified=scoring_result.get("certified", False),
            speedup_vs_reference=scoring_result.get("speedup_vs_reference", 0.0),
        )

        breakdown = scoring_result.get("family_breakdown", {})

        # Build salience items from family breakdown
        salience_items = self._build_salience_items(breakdown)
        report.salience_ranking = self.salience_engine.rank(salience_items)

        # Estimate total budget and allocate
        total_budget = self.measurement_loop.default_budget * max(1, len(breakdown))
        report.budget_allocation = self.salience_engine.allocate(
            salience_items, total_budget
        )

        # Analyze each family through the measurement loop
        for family_name, family_data in breakdown.items():
            family_analysis = self._analyze_family(family_name, family_data)
            report.family_analyses[family_name] = family_analysis

        # Compute aggregate metrics
        report.aggregate_crpt = self.measurement_loop.average_crpt()
        report.total_waste_rate = self.measurement_loop.total_waste_rate()
        report.reuse_extraction_rate = self.measurement_loop.reuse_extraction_rate()

        # Compute aggregate compression efficiency
        ce_values = [
            fa["compression_efficiency"]
            for fa in report.family_analyses.values()
            if fa.get("compression_efficiency", 0) > 0
        ]
        report.aggregate_compression_efficiency = (
            sum(ce_values) / len(ce_values) if ce_values else 0.0
        )

        # Compute evaluation criteria (Section 15.7)
        report.evaluation_criteria = self._compute_evaluation_criteria(report)

        # Seal report with integrity hash
        report.report_hash = report.compute_report_hash()

        return report

    def run(
        self,
        dataset_path: str,
        candidate_module: str,
        repeat: int = 1,
    ) -> AnalysisReport:
        """Run end-to-end: score a candidate then analyze through tokenomics.

        Args:
            dataset_path: Path to the JSONL dataset file.
            candidate_module: Python module path of the candidate.
            repeat: Number of timing repetitions per case.

        Returns:
            AnalysisReport with evaluation + tokenomic analysis.
        """
        from pathlib import Path
        scoring_result = run_scorer(
            Path(dataset_path), candidate_module, repeat
        )
        return self.analyze_scoring_result(scoring_result)

    def compare(
        self,
        dataset_path: str,
        baseline_module: str,
        tokenomic_module: str,
        repeat: int = 1,
    ) -> dict[str, Any]:
        """Compare two systems using the tokenomic benchmark framework.

        System A (baseline): scored without tokenomic optimization.
        System B (tokenomic): scored with tokenomic analysis.

        Returns a comparison report with tokenomic gain metrics.
        """
        report_a = self.run(dataset_path, baseline_module, repeat)
        report_b = self.run(dataset_path, tokenomic_module, repeat)

        # Create benchmark results per family
        all_families = set(report_a.family_analyses) | set(report_b.family_analyses)
        for family_name in all_families:
            fa_a = report_a.family_analyses.get(family_name, {})
            fa_b = report_b.family_analyses.get(family_name, {})

            baseline_score = TaskScore(
                decision_quality=fa_a.get("decision_quality", 0),
                actionability=fa_a.get("actionability", 0),
                risk_control=fa_a.get("risk_control", 0),
                accuracy=fa_a.get("accuracy", 0),
                tokens_used=max(1, fa_a.get("estimated_tokens", 1)),
            )
            tokenomic_score = TaskScore(
                decision_quality=fa_b.get("decision_quality", 0),
                actionability=fa_b.get("actionability", 0),
                risk_control=fa_b.get("risk_control", 0),
                accuracy=fa_b.get("accuracy", 0),
                tokens_used=max(1, fa_b.get("estimated_tokens", 1)),
            )
            self.benchmark_runner.add_result(BenchmarkResult(
                task_class=TaskClass.ARCHITECTURE_DESIGN,
                task_description=f"Family: {family_name}",
                baseline_score=baseline_score,
                tokenomic_score=tokenomic_score,
            ))

        gain = tokenomic_gain(
            score_b=sum(
                fa.get("cognitive_return", 0)
                for fa in report_b.family_analyses.values()
            ),
            tokens_b=max(1, sum(
                fa.get("estimated_tokens", 1)
                for fa in report_b.family_analyses.values()
            )),
            score_a=sum(
                fa.get("cognitive_return", 0)
                for fa in report_a.family_analyses.values()
            ),
            tokens_a=max(1, sum(
                fa.get("estimated_tokens", 1)
                for fa in report_a.family_analyses.values()
            )),
        )

        return {
            "baseline": report_a.to_dict(),
            "tokenomic": report_b.to_dict(),
            "tokenomic_gain": gain,
            "benchmark_summary": self.benchmark_runner.summary(),
            "hypothesis_result": (
                "CONFIRMED" if gain > 0
                else "INCONCLUSIVE" if gain == 0
                else "REJECTED"
            ),
        }

    def analyze_families(
        self, families_data: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Analyze multiple families independently without full scoring.

        Useful for API consumers who have pre-computed family breakdown
        data and want tokenomic analysis only.
        """
        results = {}
        for family_name, family_data in families_data.items():
            results[family_name] = self._analyze_family(family_name, family_data)
        return results

    # -------------------------------------------------------------------
    # Internal pipeline stages
    # -------------------------------------------------------------------

    def _build_salience_items(
        self, breakdown: dict[str, dict[str, Any]]
    ) -> list[SalienceItem]:
        """Build salience items from family breakdown data.

        Maps evaluation metrics to salience dimensions:
        - urgency: inverse of pass_rate (failing families are urgent)
        - risk: based on family classification
        - mission_relevance: proportional to case count
        - novelty: inverse of speedup (slower = more novel/uncertain)
        - known_context: speedup (faster = more understood)
        """
        items = []
        total_cases = sum(fd.get("count", 0) for fd in breakdown.values())
        for family_name, family_data in breakdown.items():
            pass_rate = family_data.get("pass_rate", 0.0)
            speedup = family_data.get("speedup", 0.0)
            count = family_data.get("count", 0)
            classification = classify_family(family_name)

            risk_score = {
                TaskRisk.MINIMAL: 1.0,
                TaskRisk.LOW: 2.0,
                TaskRisk.MODERATE: 3.0,
                TaskRisk.HIGH: 4.0,
                TaskRisk.CRITICAL: 5.0,
            }.get(classification.risk, 3.0)

            items.append(SalienceItem(
                id=family_name,
                urgency=max(0, (1.0 - pass_rate) * 5.0),
                risk=risk_score,
                mission_relevance=(count / total_cases * 5.0) if total_cases > 0 else 1.0,
                time_sensitivity=2.5,
                novelty=max(0, (1.0 - min(1.0, speedup / 5.0)) * 5.0) if speedup > 0 else 5.0,
                known_context=min(5.0, speedup) if speedup > 0 else 0.0,
                metadata={"family": family_name, "classification": classification.task_type},
            ))
        return items

    def _analyze_family(
        self, family_name: str, family_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Route a single family through the tokenomic measurement loop."""
        classification = classify_family(family_name)
        pass_rate = family_data.get("pass_rate", 0.0)
        speedup = family_data.get("speedup", 0.0)
        count = family_data.get("count", 0)
        correct = family_data.get("correct", 0)
        median_ms = family_data.get("candidate_median_ms", 0.0)

        # Estimate token equivalents from timing data
        estimated_tokens = max(1, int(median_ms * 10))

        # Score cognitive return dimensions based on evaluation results
        decision_quality = min(5.0, pass_rate * 5.0)
        actionability = min(5.0, pass_rate * speedup) if speedup > 0 else pass_rate * 2.5
        risk_control = min(5.0, pass_rate * 3.0 + (1.0 if speedup > 1.0 else 0.0))
        reuse_value = min(5.0, speedup) if pass_rate == 1.0 else 0.0
        learning_gain = min(5.0, (speedup - 1.0) * 2.0) if speedup > 1.0 else 0.5

        cognitive_scores = CognitiveReturnMetrics(
            decision_quality=decision_quality,
            actionability=min(5.0, actionability),
            risk_control=min(5.0, risk_control),
            reuse_value=min(5.0, reuse_value),
            learning_gain=min(5.0, max(0.0, learning_gain)),
        )

        # Compression scoring
        info_retained = decision_quality
        action_clarity = min(5.0, actionability)
        risk_preserved = min(5.0, risk_control)

        # Build salience item for this family
        salience_item = SalienceItem(
            id=family_name,
            urgency=max(0, (1.0 - pass_rate) * 5.0),
            risk=3.0,
        )

        # Run through measurement loop
        record = self.measurement_loop.run(
            task_classification=classification,
            salience_items=[salience_item],
            cognitive_scores=cognitive_scores,
            compression_scores=(info_retained, action_clarity, risk_preserved),
            prompt_tokens=estimated_tokens,
            output_tokens=estimated_tokens,
            reusable_rules=(
                [f"Family {family_name}: pass_rate={pass_rate}, speedup={speedup}"]
                if pass_rate == 1.0 and speedup > 1.0
                else []
            ),
        )

        # Compute accuracy for benchmark scoring
        accuracy = min(5.0, (correct / count * 5.0) if count > 0 else 0.0)

        return {
            "family": family_name,
            "classification": {
                "task_type": classification.task_type,
                "complexity": classification.complexity.value,
                "risk": classification.risk.value,
            },
            "pass_rate": pass_rate,
            "speedup": speedup,
            "count": count,
            "correct": correct,
            "estimated_tokens": estimated_tokens,
            "cognitive_return": cognitive_scores.cognitive_return,
            "crpt": record.crpt,
            "decision_quality": decision_quality,
            "actionability": min(5.0, actionability),
            "risk_control": min(5.0, risk_control),
            "reuse_value": min(5.0, reuse_value),
            "learning_gain": min(5.0, max(0.0, learning_gain)),
            "accuracy": accuracy,
            "compression_efficiency": compression_efficiency(
                info_retained, action_clarity, risk_preserved, estimated_tokens
            ),
            "estimated_budget": record.task_classification.estimated_budget,
            "wasted_tokens": record.wasted_tokens,
            "reusable_rules": record.reusable_rules,
        }

    def _compute_evaluation_criteria(
        self, report: AnalysisReport
    ) -> dict[str, float]:
        """Compute the eight evaluation criteria from Section 15.7."""
        family_analyses = list(report.family_analyses.values())
        if not family_analyses:
            return {}

        n = len(family_analyses)

        # 1. Cognitive Return Per Token
        crpt = report.aggregate_crpt

        # 2. Compression Fidelity
        compression_fidelity = report.aggregate_compression_efficiency

        # 3. Action Conversion Rate — fraction of families where actionability > 2.5
        action_conversions = sum(
            1 for fa in family_analyses if fa.get("actionability", 0) > 2.5
        )
        action_conversion_rate = action_conversions / n

        # 4. Risk Preservation — average risk_control across families
        risk_preservation = sum(
            fa.get("risk_control", 0) for fa in family_analyses
        ) / n / 5.0

        # 5. Reuse Extraction Rate
        reuse_extraction = report.reuse_extraction_rate

        # 6. Context Hygiene — inverse of waste rate
        context_hygiene = 1.0 - report.total_waste_rate

        # 7. Adaptive Depth Accuracy — variance of CRPT across families
        crpt_values = [fa.get("crpt", 0) for fa in family_analyses]
        if len(crpt_values) >= 2:
            mean_crpt = sum(crpt_values) / len(crpt_values)
            variance = sum((v - mean_crpt) ** 2 for v in crpt_values) / len(crpt_values)
            adaptive_depth = max(0.0, 1.0 - min(1.0, variance))
        else:
            adaptive_depth = 1.0

        # 8. Error Avoidance — overall pass rate
        total_cases = sum(fa.get("count", 0) for fa in family_analyses)
        total_correct = sum(fa.get("correct", 0) for fa in family_analyses)
        error_avoidance = total_correct / total_cases if total_cases > 0 else 0.0

        return {
            "cognitive_return_per_token": crpt,
            "compression_fidelity": compression_fidelity,
            "action_conversion_rate": action_conversion_rate,
            "risk_preservation": risk_preservation,
            "reuse_extraction_rate": reuse_extraction,
            "context_hygiene": context_hygiene,
            "adaptive_depth_accuracy": adaptive_depth,
            "error_avoidance": error_avoidance,
        }
