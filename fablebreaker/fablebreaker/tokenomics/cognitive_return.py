"""Cognitive Return Metrics (Section 15.2).

The primary system-level metric is Cognitive Return Per Token:

    CRPT = Cognitive Return / (Prompt Tokens + Output Tokens)

Cognitive Return is scored across five categories (each 0-5 scale):
    CR = DQ + ACT + RISK + REUSE + LEARN
"""

from __future__ import annotations

from dataclasses import dataclass


# Maximum score per category on the 0-5 scale.
MAX_CATEGORY_SCORE = 5.0
NUM_CATEGORIES = 5
MAX_COGNITIVE_RETURN = MAX_CATEGORY_SCORE * NUM_CATEGORIES


@dataclass
class CognitiveReturnMetrics:
    """Scores for the five cognitive return categories.

    Each category is scored on a 0-5 scale:
        - decision_quality: Did the response improve the actual decision?
        - actionability: Can the user or system act immediately?
        - risk_control: Did the response identify or reduce meaningful failure modes?
        - reuse_value: Did the response create a reusable rule, template, memory,
          artifact, or procedure?
        - learning_gain: Did the interaction improve future system behavior?
    """

    decision_quality: float = 0.0
    actionability: float = 0.0
    risk_control: float = 0.0
    reuse_value: float = 0.0
    learning_gain: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "decision_quality",
            "actionability",
            "risk_control",
            "reuse_value",
            "learning_gain",
        ):
            val = getattr(self, field_name)
            if val < 0.0 or val > MAX_CATEGORY_SCORE:
                raise ValueError(
                    f"{field_name} must be between 0 and {MAX_CATEGORY_SCORE}, got {val}"
                )

    @property
    def cognitive_return(self) -> float:
        """Total cognitive return: CR = DQ + ACT + RISK + REUSE + LEARN."""
        return (
            self.decision_quality
            + self.actionability
            + self.risk_control
            + self.reuse_value
            + self.learning_gain
        )

    @property
    def normalized(self) -> float:
        """Cognitive return normalized to 0-1 range."""
        return self.cognitive_return / MAX_COGNITIVE_RETURN


def cognitive_return_per_token(
    metrics: CognitiveReturnMetrics,
    prompt_tokens: int,
    output_tokens: int,
) -> float:
    """Compute Cognitive Return Per Token (CRPT).

    CRPT = (DQ + ACT + RISK + REUSE + LEARN) / (Prompt Tokens + Output Tokens)

    This metric rewards systems that produce compact but useful outputs.
    It penalizes long outputs that do not improve action, judgment, risk
    control, or future reuse.
    """
    total_tokens = prompt_tokens + output_tokens
    if total_tokens <= 0:
        return 0.0
    return metrics.cognitive_return / total_tokens
