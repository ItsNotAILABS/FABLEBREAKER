"""Tokenomic vs. Non-Tokenomic Benchmark Tasks (Section 15.5).

Validates Tokenomics empirically by comparing:
    System A: Non-Tokenomic Baseline (no explicit token allocation, salience
              scoring, compression audit, or cognitive return measurement).
    System B: Tokenomic System (salience ranking, token budgeting, sparse
              module activation, compression auditing, risk preservation,
              and reuse extraction).

Score = DQ + ACT + RISK + REUSE + ACCURACY - WASTE

TokenomicGain = (Score_B / Tokens_B) - (Score_A / Tokens_A)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskClass(Enum):
    """Benchmark task classes for tokenomic evaluation."""

    INVOICE_EXECUTION = "invoice_execution"
    ESTIMATING = "estimating"
    CASHFLOW_DECISION = "cashflow_decision"
    PROPOSAL_GENERATION = "proposal_generation"
    RESEARCH_SYNTHESIS = "research_synthesis"
    ARCHITECTURE_DESIGN = "architecture_design"
    RED_TEAM_REVIEW = "red_team_review"
    MEMORY_CONSOLIDATION = "memory_consolidation"


@dataclass
class TaskScore:
    """Score for a benchmark task.

    Score = DQ + ACT + RISK + REUSE + ACCURACY - WASTE

    Attributes:
        decision_quality: Decision quality (0-5).
        actionability: Actionability (0-5).
        risk_control: Risk control (0-5).
        reuse_value: Reusable value (0-5).
        accuracy: Factual, mathematical, or procedural correctness (0-5).
        waste: Unnecessary token expenditure (0-5).
        tokens_used: Total tokens consumed for this task.
    """

    decision_quality: float = 0.0
    actionability: float = 0.0
    risk_control: float = 0.0
    reuse_value: float = 0.0
    accuracy: float = 0.0
    waste: float = 0.0
    tokens_used: int = 0

    @property
    def total_score(self) -> float:
        """Compute total score: DQ + ACT + RISK + REUSE + ACCURACY - WASTE."""
        return (
            self.decision_quality
            + self.actionability
            + self.risk_control
            + self.reuse_value
            + self.accuracy
            - self.waste
        )

    @property
    def score_per_token(self) -> float:
        """Score normalized by tokens used."""
        if self.tokens_used <= 0:
            return 0.0
        return self.total_score / self.tokens_used


@dataclass
class BenchmarkResult:
    """Result of comparing tokenomic vs non-tokenomic systems on a task.

    Attributes:
        task_class: The type of benchmark task.
        task_description: Human-readable task description.
        baseline_score: Score from the non-tokenomic system (System A).
        tokenomic_score: Score from the tokenomic system (System B).
        metadata: Additional context about the benchmark run.
    """

    task_class: TaskClass
    task_description: str
    baseline_score: TaskScore
    tokenomic_score: TaskScore
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def tokenomic_gain(self) -> float:
        """Compute tokenomic gain.

        TokenomicGain = (Score_B / Tokens_B) - (Score_A / Tokens_A)

        A tokenomic system is superior when it produces equal or higher task
        score with fewer tokens, or significantly higher task score with a
        justified increase in tokens.
        """
        return self.tokenomic_score.score_per_token - self.baseline_score.score_per_token

    @property
    def is_tokenomic_superior(self) -> bool:
        """Whether the tokenomic system outperforms the baseline."""
        return self.tokenomic_gain > 0


def tokenomic_gain(
    score_b: float,
    tokens_b: int,
    score_a: float,
    tokens_a: int,
) -> float:
    """Compute tokenomic gain between two systems.

    TokenomicGain = (Score_B / Tokens_B) - (Score_A / Tokens_A)

    Args:
        score_b: Total score of the tokenomic system.
        tokens_b: Total tokens used by the tokenomic system.
        score_a: Total score of the non-tokenomic baseline.
        tokens_a: Total tokens used by the non-tokenomic baseline.

    Returns:
        Tokenomic gain (positive means tokenomic system is better).
    """
    efficiency_b = score_b / tokens_b if tokens_b > 0 else 0.0
    efficiency_a = score_a / tokens_a if tokens_a > 0 else 0.0
    return efficiency_b - efficiency_a


@dataclass
class BenchmarkRunner:
    """Runs tokenomic vs non-tokenomic benchmark comparisons.

    Manages a suite of benchmark tasks and aggregates results across
    multiple task classes.
    """

    results: list[BenchmarkResult] = field(default_factory=list)

    def add_result(self, result: BenchmarkResult) -> None:
        """Record a benchmark result."""
        self.results.append(result)

    def aggregate_gain(self) -> float:
        """Compute average tokenomic gain across all benchmark tasks."""
        if not self.results:
            return 0.0
        return sum(r.tokenomic_gain for r in self.results) / len(self.results)

    def gains_by_task_class(self) -> dict[TaskClass, float]:
        """Compute average tokenomic gain per task class."""
        class_results: dict[TaskClass, list[float]] = {}
        for result in self.results:
            class_results.setdefault(result.task_class, []).append(result.tokenomic_gain)
        return {
            tc: sum(gains) / len(gains)
            for tc, gains in class_results.items()
        }

    def win_rate(self) -> float:
        """Fraction of tasks where the tokenomic system is superior."""
        if not self.results:
            return 0.0
        wins = sum(1 for r in self.results if r.is_tokenomic_superior)
        return wins / len(self.results)

    def summary(self) -> dict[str, Any]:
        """Produce a summary report of all benchmark results."""
        return {
            "total_tasks": len(self.results),
            "aggregate_gain": self.aggregate_gain(),
            "win_rate": self.win_rate(),
            "gains_by_class": {
                tc.value: gain for tc, gain in self.gains_by_task_class().items()
            },
        }
