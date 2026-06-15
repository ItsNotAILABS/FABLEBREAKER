"""Salience Allocation Equations (Section 15.3).

Tokenomic systems allocate attention before generating output. A Salience
Engine ranks what deserves token budget based on urgency, risk, mission
relevance, novelty, time sensitivity, and whether context is already known.

S_i = alpha*U_i + beta*R_i + gamma*M_i + delta*T_i + epsilon*N_i - zeta*K_i

Budget allocation:
    B_i = B_total * (S_i / sum(S))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SalienceWeights:
    """Task-specific weights for salience scoring.

    Attributes:
        alpha: Weight for urgency.
        beta: Weight for risk/consequence.
        gamma: Weight for mission relevance.
        delta: Weight for time sensitivity.
        epsilon: Weight for novelty/uncertainty.
        zeta: Weight for known/already-settled context (subtracted).
    """

    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    delta: float = 1.0
    epsilon: float = 1.0
    zeta: float = 1.0


@dataclass
class SalienceItem:
    """An information unit to be scored for salience.

    Attributes:
        id: Unique identifier for this item.
        urgency: How urgent this item is.
        risk: Risk or consequence if not addressed.
        mission_relevance: How relevant to the current mission.
        time_sensitivity: How time-critical this item is.
        novelty: Novelty or uncertainty of this item.
        known_context: How much of this is already known/settled.
        metadata: Optional additional metadata.
    """

    id: str
    urgency: float = 0.0
    risk: float = 0.0
    mission_relevance: float = 0.0
    time_sensitivity: float = 0.0
    novelty: float = 0.0
    known_context: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


def salience_score(item: SalienceItem, weights: SalienceWeights | None = None) -> float:
    """Compute salience score for an information unit.

    S_i = alpha*U_i + beta*R_i + gamma*M_i + delta*T_i + epsilon*N_i - zeta*K_i
    """
    w = weights or SalienceWeights()
    return (
        w.alpha * item.urgency
        + w.beta * item.risk
        + w.gamma * item.mission_relevance
        + w.delta * item.time_sensitivity
        + w.epsilon * item.novelty
        - w.zeta * item.known_context
    )


def allocate_budget(
    items: list[SalienceItem],
    total_budget: int,
    weights: SalienceWeights | None = None,
    min_budget: int = 0,
) -> dict[str, int]:
    """Allocate token budget proportionally based on salience scores.

    B_i = B_total * (S_i / sum(S))

    Items with non-positive salience receive the minimum budget.
    This prevents low-value context from consuming high-value token space.

    Args:
        items: Information units to allocate budget to.
        total_budget: Total available output token budget.
        weights: Optional task-specific salience weights.
        min_budget: Minimum token budget per item (default 0).

    Returns:
        Mapping of item id to allocated token budget.
    """
    if not items:
        return {}

    scores = {item.id: salience_score(item, weights) for item in items}

    # Clamp negative scores to zero for allocation purposes.
    positive_scores = {k: max(0.0, v) for k, v in scores.items()}
    total_salience = sum(positive_scores.values())

    allocations: dict[str, int] = {}
    if total_salience <= 0:
        # Equal distribution when all scores are non-positive.
        per_item = max(min_budget, total_budget // len(items))
        for item in items:
            allocations[item.id] = per_item
    else:
        for item in items:
            proportion = positive_scores[item.id] / total_salience
            allocated = max(min_budget, int(total_budget * proportion))
            allocations[item.id] = allocated

    return allocations


@dataclass
class SalienceEngine:
    """Engine for ranking and allocating token budget across information units.

    The system spends tokens on what is urgent, risky, mission-relevant,
    time-sensitive, uncertain, and not already known.
    """

    weights: SalienceWeights = field(default_factory=SalienceWeights)
    min_budget_per_item: int = 0

    def rank(self, items: list[SalienceItem]) -> list[tuple[str, float]]:
        """Rank items by salience score, highest first."""
        scored = [(item.id, salience_score(item, self.weights)) for item in items]
        return sorted(scored, key=lambda x: x[1], reverse=True)

    def allocate(self, items: list[SalienceItem], total_budget: int) -> dict[str, int]:
        """Allocate token budget proportionally across items."""
        return allocate_budget(items, total_budget, self.weights, self.min_budget_per_item)

    def filter_above_threshold(
        self, items: list[SalienceItem], threshold: float = 0.0
    ) -> list[SalienceItem]:
        """Return only items with salience above the given threshold."""
        return [
            item for item in items if salience_score(item, self.weights) > threshold
        ]
