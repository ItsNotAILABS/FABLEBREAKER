"""FableBreaker SDK — Unified programmatic interface.

The FableBreakerSDK is the single entry point for all consumers — internal
analysis, external API integrations, and third-party tooling. It unifies:

    - Protocol SDK (14 published protocols)
    - Tokenomics Measurement Framework
    - Analysis Engine (routing pipeline)
    - Scoring and Generation
    - Certification and Governance

This is the class you import when you want to use Fablebreaker as a library.

Usage:
    from fablebreaker.sdk import FableBreakerSDK

    sdk = FableBreakerSDK()

    # Access protocols
    corridor = sdk.protocols.overflow_corridors.generate(seed=42, size=30)

    # Run evaluation with tokenomic analysis
    report = sdk.analyze(dataset="dataset/public.jsonl",
                         candidate="candidates.baseline_candidate")

    # Access tokenomics directly
    crpt = sdk.tokenomics.cognitive_return_per_token(metrics, 100, 200)

    # Get system info
    info = sdk.info()

Foundation: https://doi.org/10.5281/zenodo.20589250
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .engine import AnalysisEngine, AnalysisReport, classify_family
from .protocols import (
    OverflowCorridorProtocol,
    ConditionalCascadeProtocol,
    GovernanceCertificationProtocol,
    PerFamilyScoringProtocol,
    APIReproducibilityProtocol,
    ProtocolRegistry,
    FOUNDATION_DOI,
    FOUNDATION_CITATION,
)
from .tokenomics import (
    TokenValueFunction,
    CognitiveReturnMetrics,
    cognitive_return_per_token,
    SalienceEngine,
    CompressionMetrics,
    compression_efficiency,
    BenchmarkRunner,
    tokenomic_gain,
    RuntimeMeasurementLoop,
)
from .tokenomics.salience import SalienceWeights, SalienceItem
from .tokenomics.token_value import TokenWeights, TokenScores


SDK_VERSION = "1.0.0"


@dataclass
class ProtocolsAccessor:
    """Provides access to all protocol SDK implementations.

    Each protocol is available as an attribute for direct use.
    """

    overflow_corridors: OverflowCorridorProtocol = field(
        default_factory=OverflowCorridorProtocol
    )
    conditional_cascades: ConditionalCascadeProtocol = field(
        default_factory=ConditionalCascadeProtocol
    )
    governance_certification: GovernanceCertificationProtocol = field(
        default_factory=GovernanceCertificationProtocol
    )
    per_family_scoring: PerFamilyScoringProtocol = field(
        default_factory=PerFamilyScoringProtocol
    )
    api_reproducibility: APIReproducibilityProtocol = field(
        default_factory=APIReproducibilityProtocol
    )
    registry: ProtocolRegistry = field(default_factory=ProtocolRegistry)

    def list_protocols(self) -> list[str]:
        """Return names of all available protocol implementations."""
        return [
            "overflow_corridors",
            "conditional_cascades",
            "governance_certification",
            "per_family_scoring",
            "api_reproducibility",
        ]

    def summary(self) -> dict[str, Any]:
        """Return summary of protocols and their paper mappings."""
        return self.registry.summary()


@dataclass
class TokenomicsAccessor:
    """Provides access to all tokenomics measurement components.

    Wraps the tokenomics module to provide a clean interface for
    token value computation, cognitive return metrics, salience
    allocation, compression efficiency, and benchmarking.
    """

    token_value_fn: TokenValueFunction = field(
        default_factory=TokenValueFunction
    )
    salience_engine: SalienceEngine = field(
        default_factory=SalienceEngine
    )
    measurement_loop: RuntimeMeasurementLoop = field(
        default_factory=RuntimeMeasurementLoop
    )
    benchmark_runner: BenchmarkRunner = field(
        default_factory=BenchmarkRunner
    )

    # Re-export key functions for convenience
    cognitive_return_per_token = staticmethod(cognitive_return_per_token)
    compression_efficiency = staticmethod(compression_efficiency)
    tokenomic_gain = staticmethod(tokenomic_gain)

    def create_cognitive_metrics(
        self,
        decision_quality: float = 0.0,
        actionability: float = 0.0,
        risk_control: float = 0.0,
        reuse_value: float = 0.0,
        learning_gain: float = 0.0,
    ) -> CognitiveReturnMetrics:
        """Create a CognitiveReturnMetrics instance."""
        return CognitiveReturnMetrics(
            decision_quality=decision_quality,
            actionability=actionability,
            risk_control=risk_control,
            reuse_value=reuse_value,
            learning_gain=learning_gain,
        )

    def create_compression_metrics(
        self,
        information_retained: float = 0.0,
        action_clarity: float = 0.0,
        risk_preserved: float = 0.0,
        output_tokens: int = 0,
    ) -> CompressionMetrics:
        """Create a CompressionMetrics instance."""
        return CompressionMetrics(
            information_retained=information_retained,
            action_clarity=action_clarity,
            risk_preserved=risk_preserved,
            output_tokens=output_tokens,
        )

    def create_salience_item(
        self,
        item_id: str,
        urgency: float = 0.0,
        risk: float = 0.0,
        mission_relevance: float = 0.0,
        time_sensitivity: float = 0.0,
        novelty: float = 0.0,
        known_context: float = 0.0,
    ) -> SalienceItem:
        """Create a SalienceItem for budget allocation."""
        return SalienceItem(
            id=item_id,
            urgency=urgency,
            risk=risk,
            mission_relevance=mission_relevance,
            time_sensitivity=time_sensitivity,
            novelty=novelty,
            known_context=known_context,
        )

    def compute_token_value(self, scores: TokenScores) -> float:
        """Compute token value for a single token."""
        return self.token_value_fn.compute(scores)

    def allocate_budget(
        self, items: list[SalienceItem], total_budget: int
    ) -> dict[str, int]:
        """Allocate token budget across salience items."""
        return self.salience_engine.allocate(items, total_budget)

    def summary(self) -> dict[str, Any]:
        """Return measurement loop metrics summary."""
        return {
            "average_crpt": self.measurement_loop.average_crpt(),
            "total_waste_rate": self.measurement_loop.total_waste_rate(),
            "reuse_extraction_rate": self.measurement_loop.reuse_extraction_rate(),
            "interactions_recorded": len(self.measurement_loop.history),
            "policy_adjustments": dict(self.measurement_loop.policy_adjustments),
            "benchmark_results": self.benchmark_runner.summary(),
        }


class FableBreakerSDK:
    """Unified SDK for the FableBreaker Intelligence System.

    This is the primary entry point for all programmatic access to
    Fablebreaker — evaluation, analysis, tokenomics, protocols, and
    certification.

    Usage:
        sdk = FableBreakerSDK()

        # System information
        info = sdk.info()

        # Analyze a candidate
        report = sdk.analyze("dataset/public.jsonl", "candidates.baseline_candidate")

        # Access protocols directly
        corridor = sdk.protocols.overflow_corridors.generate(seed=42, size=30)

        # Access tokenomics directly
        crpt = sdk.tokenomics.cognitive_return_per_token(metrics, 100, 200)

        # Compare two candidates
        comparison = sdk.compare("dataset/public.jsonl", "candidate_a", "candidate_b")

        # Analyze pre-computed scoring results
        report = sdk.analyze_result(scoring_dict)

        # Export analysis as JSON
        json_str = sdk.export_report(report)
    """

    VERSION = SDK_VERSION
    FOUNDATION_DOI = FOUNDATION_DOI
    FOUNDATION_CITATION = FOUNDATION_CITATION

    def __init__(
        self,
        salience_weights: SalienceWeights | None = None,
        token_weights: TokenWeights | None = None,
        api_base_url: str = "http://127.0.0.1:8787",
        default_budget: int = 1000,
    ) -> None:
        """Initialize the FableBreaker SDK.

        Args:
            salience_weights: Custom weights for salience scoring.
            token_weights: Custom weights for token value computation.
            api_base_url: Base URL for the FableBreaker service API.
            default_budget: Default token budget per family.
        """
        self._engine = AnalysisEngine(
            salience_weights=salience_weights,
            token_weights=token_weights,
            default_budget=default_budget,
        )

        # Protocol accessor with custom API base URL
        self._protocols = ProtocolsAccessor(
            api_reproducibility=APIReproducibilityProtocol(base_url=api_base_url),
        )

        self._tokenomics = TokenomicsAccessor(
            token_value_fn=self._engine.token_value_fn,
            salience_engine=self._engine.salience_engine,
            measurement_loop=self._engine.measurement_loop,
            benchmark_runner=self._engine.benchmark_runner,
        )

    @property
    def protocols(self) -> ProtocolsAccessor:
        """Access all protocol SDK implementations."""
        return self._protocols

    @property
    def tokenomics(self) -> TokenomicsAccessor:
        """Access tokenomics measurement framework."""
        return self._tokenomics

    @property
    def engine(self) -> AnalysisEngine:
        """Access the analysis engine directly."""
        return self._engine

    def info(self) -> dict[str, Any]:
        """Return complete system information.

        Includes SDK version, foundation reference, available protocols,
        tokenomics configuration, and evaluation criteria definitions.
        """
        return {
            "sdk_version": self.VERSION,
            "foundation_doi": self.FOUNDATION_DOI,
            "foundation_citation": self.FOUNDATION_CITATION,
            "protocols": self._protocols.summary(),
            "tokenomics": self._tokenomics.summary(),
            "evaluation_criteria": [
                "cognitive_return_per_token",
                "compression_fidelity",
                "action_conversion_rate",
                "risk_preservation",
                "reuse_extraction_rate",
                "context_hygiene",
                "adaptive_depth_accuracy",
                "error_avoidance",
            ],
            "task_classes": [
                "invoice_execution",
                "estimating",
                "cashflow_decision",
                "proposal_generation",
                "research_synthesis",
                "architecture_design",
                "red_team_review",
                "memory_consolidation",
            ],
        }

    def analyze(
        self,
        dataset: str,
        candidate: str,
        repeat: int = 1,
    ) -> AnalysisReport:
        """Run end-to-end evaluation and tokenomic analysis.

        Scores the candidate against the dataset, then routes the
        results through the full tokenomic measurement pipeline.

        Args:
            dataset: Path to the JSONL dataset file.
            candidate: Python module path of the candidate.
            repeat: Number of timing repetitions per case.

        Returns:
            AnalysisReport with full evaluation + tokenomic analysis.
        """
        return self._engine.run(dataset, candidate, repeat)

    def analyze_result(
        self, scoring_result: dict[str, Any]
    ) -> AnalysisReport:
        """Analyze a pre-computed scoring result through tokenomics.

        Use this when you already have scoring results and want
        tokenomic analysis without re-running evaluation.

        Args:
            scoring_result: Dictionary from scorer.score().

        Returns:
            AnalysisReport with tokenomic analysis.
        """
        return self._engine.analyze_scoring_result(scoring_result)

    def compare(
        self,
        dataset: str,
        baseline: str,
        tokenomic: str,
        repeat: int = 1,
    ) -> dict[str, Any]:
        """Compare tokenomic vs non-tokenomic systems.

        Args:
            dataset: Path to the JSONL dataset file.
            baseline: Python module path of the baseline candidate.
            tokenomic: Python module path of the tokenomic candidate.
            repeat: Number of timing repetitions.

        Returns:
            Comparison report with tokenomic gain metrics.
        """
        return self._engine.compare(dataset, baseline, tokenomic, repeat)

    def export_report(
        self, report: AnalysisReport, indent: int = 2
    ) -> str:
        """Export an analysis report as formatted JSON.

        Args:
            report: AnalysisReport to export.
            indent: JSON indentation level.

        Returns:
            JSON string of the report.
        """
        return json.dumps(report.to_dict(), indent=indent, sort_keys=True)

    def save_report(
        self, report: AnalysisReport, path: str
    ) -> str:
        """Save an analysis report to a JSON file.

        Args:
            report: AnalysisReport to save.
            path: File path to write to.

        Returns:
            The path written to.
        """
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            self.export_report(report) + "\n", encoding="utf-8"
        )
        return str(out)

    def classify_family(self, family: str) -> dict[str, Any]:
        """Classify a benchmark family for tokenomic analysis.

        Args:
            family: Family name (e.g. 'overflow_corridor').

        Returns:
            Classification with complexity, risk, and modules needed.
        """
        classification = classify_family(family)
        return {
            "task_type": classification.task_type,
            "complexity": classification.complexity.value,
            "risk": classification.risk.value,
            "estimated_budget": self._engine.measurement_loop.estimate_budget(
                classification
            ),
            "modules_needed": classification.modules_needed,
        }
