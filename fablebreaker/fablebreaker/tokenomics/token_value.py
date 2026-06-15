"""Token Value Function (Section 15.1).

A token is evaluated by the value it contributes to the task. Each emitted
token is treated as a unit of compute, attention, memory surface, and action
influence.

TV(t) = w_d*D_t + w_a*A_t + w_r*R_t + w_c*C_t + w_m*M_t - w_n*N_t

Simplified:
    TV = DQ + ACT + RISK + REUSE + LEARN - WASTE
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenWeights:
    """Task-specific weighting coefficients for token value calculation."""

    decision: float = 1.0
    action: float = 1.0
    risk: float = 1.0
    compression: float = 1.0
    memory: float = 1.0
    noise: float = 1.0


@dataclass
class TokenScores:
    """Per-token component scores.

    Attributes:
        decision_value: Decision value contributed by the token (D_t).
        action_usefulness: Action usefulness (A_t).
        risk_reduction: Risk reduction (R_t).
        compression_contribution: Compression contribution (C_t).
        memory_value: Memory or reuse value (M_t).
        noise: Noise, redundancy, or attention waste (N_t).
    """

    decision_value: float = 0.0
    action_usefulness: float = 0.0
    risk_reduction: float = 0.0
    compression_contribution: float = 0.0
    memory_value: float = 0.0
    noise: float = 0.0


@dataclass
class TokenValueFunction:
    """Computes token value using configurable weights.

    A token has positive value when it improves decision quality, enables
    action, reduces risk, compresses useful knowledge, or creates reusable
    memory. A token has negative value when it repeats already-known context,
    adds generic language, increases ambiguity, or consumes attention without
    improving the outcome.
    """

    weights: TokenWeights = field(default_factory=TokenWeights)

    def compute(self, scores: TokenScores) -> float:
        """Compute the value of a single token.

        TV(t) = w_d*D_t + w_a*A_t + w_r*R_t + w_c*C_t + w_m*M_t - w_n*N_t
        """
        return (
            self.weights.decision * scores.decision_value
            + self.weights.action * scores.action_usefulness
            + self.weights.risk * scores.risk_reduction
            + self.weights.compression * scores.compression_contribution
            + self.weights.memory * scores.memory_value
            - self.weights.noise * scores.noise
        )

    def compute_batch(self, token_scores: list[TokenScores]) -> list[float]:
        """Compute values for a sequence of tokens."""
        return [self.compute(s) for s in token_scores]

    def total_value(self, token_scores: list[TokenScores]) -> float:
        """Compute aggregate value across all tokens."""
        return sum(self.compute_batch(token_scores))

    def positive_ratio(self, token_scores: list[TokenScores]) -> float:
        """Fraction of tokens with positive value."""
        if not token_scores:
            return 0.0
        values = self.compute_batch(token_scores)
        positive = sum(1 for v in values if v > 0)
        return positive / len(values)


def token_value(
    decision_quality: float = 0.0,
    actionability: float = 0.0,
    risk_control: float = 0.0,
    reuse: float = 0.0,
    learning: float = 0.0,
    waste: float = 0.0,
) -> float:
    """Simplified token value formula.

    TV = DQ + ACT + RISK + REUSE + LEARN - WASTE
    """
    return decision_quality + actionability + risk_control + reuse + learning - waste
