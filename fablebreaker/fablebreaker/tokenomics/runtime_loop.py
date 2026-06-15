"""Runtime Measurement Loop (Section 15.6).

A deployable Tokenomic AI System evaluates itself through a runtime
measurement loop that creates a feedback mechanism where every interaction
improves future efficiency.

Steps:
    1. Classify the task
    2. Estimate task risk and complexity
    3. Rank salience targets
    4. Allocate token budget
    5. Recruit only necessary modules or agents
    6. Generate the response or artifact
    7. Audit compression quality
    8. Score cognitive return
    9. Detect wasted tokens
    10. Extract reusable rules or memory
    11. Update future token allocation policy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .cognitive_return import CognitiveReturnMetrics, cognitive_return_per_token
from .compression import CompressionMetrics
from .salience import SalienceEngine, SalienceItem
from .token_value import TokenScores, TokenValueFunction


class TaskComplexity(Enum):
    """Task complexity levels for budget estimation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskRisk(Enum):
    """Task risk levels."""

    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskClassification:
    """Classification of a task for token budget allocation."""

    task_type: str
    complexity: TaskComplexity
    risk: TaskRisk
    estimated_budget: int = 0
    modules_needed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionRecord:
    """Record of a single interaction through the measurement loop."""

    task_classification: TaskClassification
    salience_items: list[SalienceItem]
    budget_allocation: dict[str, int]
    output_tokens: int = 0
    prompt_tokens: int = 0
    cognitive_return: CognitiveReturnMetrics | None = None
    compression: CompressionMetrics | None = None
    wasted_tokens: int = 0
    reusable_rules: list[str] = field(default_factory=list)
    crpt: float = 0.0


class TaskClassifier(Protocol):
    """Protocol for task classification implementations."""

    def classify(self, task_input: Any) -> TaskClassification: ...


class ResponseGenerator(Protocol):
    """Protocol for response generation implementations."""

    def generate(
        self, task_input: Any, budget: int, modules: list[str]
    ) -> tuple[str, int]: ...


@dataclass
class RuntimeMeasurementLoop:
    """Runtime measurement loop for tokenomic AI systems.

    Creates a feedback loop where every interaction improves future
    efficiency. A successful interaction should not only solve the current
    task, but reduce the cost of solving similar tasks later.
    """

    salience_engine: SalienceEngine = field(default_factory=SalienceEngine)
    token_value_fn: TokenValueFunction = field(default_factory=TokenValueFunction)
    history: list[InteractionRecord] = field(default_factory=list)
    policy_adjustments: dict[str, float] = field(default_factory=dict)
    default_budget: int = 1000

    def estimate_budget(self, classification: TaskClassification) -> int:
        """Estimate token budget based on task classification.

        Step 2: Estimate task risk and complexity.
        """
        base_budgets = {
            TaskComplexity.LOW: 250,
            TaskComplexity.MEDIUM: 500,
            TaskComplexity.HIGH: 1000,
            TaskComplexity.CRITICAL: 2000,
        }
        risk_multipliers = {
            TaskRisk.MINIMAL: 0.8,
            TaskRisk.LOW: 1.0,
            TaskRisk.MODERATE: 1.2,
            TaskRisk.HIGH: 1.5,
            TaskRisk.CRITICAL: 2.0,
        }
        base = base_budgets.get(classification.complexity, 500)
        multiplier = risk_multipliers.get(classification.risk, 1.0)

        # Apply learned policy adjustments for this task type.
        adjustment = self.policy_adjustments.get(classification.task_type, 1.0)

        return int(base * multiplier * adjustment)

    def rank_and_allocate(
        self, items: list[SalienceItem], total_budget: int
    ) -> dict[str, int]:
        """Steps 3-4: Rank salience targets and allocate token budget."""
        return self.salience_engine.allocate(items, total_budget)

    def audit_compression(
        self,
        information_retained: float,
        action_clarity: float,
        risk_preserved: float,
        output_tokens: int,
    ) -> CompressionMetrics:
        """Step 7: Audit compression quality."""
        return CompressionMetrics(
            information_retained=information_retained,
            action_clarity=action_clarity,
            risk_preserved=risk_preserved,
            output_tokens=output_tokens,
        )

    def score_cognitive_return(
        self,
        decision_quality: float,
        actionability: float,
        risk_control: float,
        reuse_value: float,
        learning_gain: float,
        prompt_tokens: int,
        output_tokens: int,
    ) -> tuple[CognitiveReturnMetrics, float]:
        """Step 8: Score cognitive return."""
        metrics = CognitiveReturnMetrics(
            decision_quality=decision_quality,
            actionability=actionability,
            risk_control=risk_control,
            reuse_value=reuse_value,
            learning_gain=learning_gain,
        )
        crpt = cognitive_return_per_token(metrics, prompt_tokens, output_tokens)
        return metrics, crpt

    def detect_waste(
        self, token_scores: list[TokenScores], threshold: float = 0.0
    ) -> int:
        """Step 9: Detect wasted tokens (those with negative or zero value)."""
        values = self.token_value_fn.compute_batch(token_scores)
        return sum(1 for v in values if v <= threshold)

    def update_policy(self, record: InteractionRecord) -> None:
        """Step 11: Update future token allocation policy.

        Adjusts budget estimates based on observed efficiency.
        """
        task_type = record.task_classification.task_type
        if record.crpt > 0 and record.output_tokens > 0:
            # If we achieved good CRPT with fewer tokens than budgeted,
            # reduce future budgets slightly for this task type.
            budget = record.task_classification.estimated_budget
            if budget > 0 and record.output_tokens < budget * 0.7:
                current = self.policy_adjustments.get(task_type, 1.0)
                self.policy_adjustments[task_type] = max(0.5, current * 0.95)
            elif record.output_tokens > budget * 1.2 and record.wasted_tokens == 0:
                # Needed more tokens but didn't waste them — increase budget.
                current = self.policy_adjustments.get(task_type, 1.0)
                self.policy_adjustments[task_type] = min(3.0, current * 1.05)

    def run(
        self,
        task_classification: TaskClassification,
        salience_items: list[SalienceItem],
        cognitive_scores: CognitiveReturnMetrics,
        compression_scores: tuple[float, float, float],
        prompt_tokens: int,
        output_tokens: int,
        token_scores: list[TokenScores] | None = None,
        reusable_rules: list[str] | None = None,
    ) -> InteractionRecord:
        """Execute the full runtime measurement loop.

        Args:
            task_classification: The classified task.
            salience_items: Information units for budget allocation.
            cognitive_scores: Scored cognitive return metrics.
            compression_scores: Tuple of (info_retained, action_clarity, risk_preserved).
            prompt_tokens: Number of prompt tokens used.
            output_tokens: Number of output tokens generated.
            token_scores: Optional per-token score breakdown for waste detection.
            reusable_rules: Optional extracted reusable rules/memory.

        Returns:
            Complete interaction record for this measurement cycle.
        """
        # Step 2: Estimate budget
        estimated_budget = self.estimate_budget(task_classification)
        task_classification.estimated_budget = estimated_budget

        # Steps 3-4: Rank and allocate
        budget_allocation = self.rank_and_allocate(salience_items, estimated_budget)

        # Step 7: Audit compression
        compression = self.audit_compression(
            compression_scores[0], compression_scores[1], compression_scores[2],
            output_tokens,
        )

        # Step 8: Score cognitive return
        crpt = cognitive_return_per_token(cognitive_scores, prompt_tokens, output_tokens)

        # Step 9: Detect waste
        wasted = 0
        if token_scores:
            wasted = self.detect_waste(token_scores)

        # Step 10: Extract reusable rules
        rules = reusable_rules or []

        # Build record
        record = InteractionRecord(
            task_classification=task_classification,
            salience_items=salience_items,
            budget_allocation=budget_allocation,
            output_tokens=output_tokens,
            prompt_tokens=prompt_tokens,
            cognitive_return=cognitive_scores,
            compression=compression,
            wasted_tokens=wasted,
            reusable_rules=rules,
            crpt=crpt,
        )

        # Step 11: Update policy
        self.update_policy(record)

        # Store in history
        self.history.append(record)

        return record

    def average_crpt(self) -> float:
        """Average Cognitive Return Per Token across all recorded interactions."""
        if not self.history:
            return 0.0
        return sum(r.crpt for r in self.history) / len(self.history)

    def total_waste_rate(self) -> float:
        """Proportion of total tokens that were wasted across all interactions."""
        total_tokens = sum(r.output_tokens for r in self.history)
        total_waste = sum(r.wasted_tokens for r in self.history)
        if total_tokens <= 0:
            return 0.0
        return total_waste / total_tokens

    def reuse_extraction_rate(self) -> float:
        """Fraction of interactions that produced reusable rules."""
        if not self.history:
            return 0.0
        with_rules = sum(1 for r in self.history if r.reusable_rules)
        return with_rules / len(self.history)
