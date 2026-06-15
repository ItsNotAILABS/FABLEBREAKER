"""Compression Efficiency Metrics (Section 15.4).

Compression is not the same as shortening. A compressed response is successful
only if it preserves meaning, action clarity, and risk awareness.

CE = MeaningPreserved / TokensUsed

Operational version:
    CEF = (InformationRetained + ActionClarity + RiskPreserved) / OutputTokens

Good compression reduces surface length while preserving correct action.
Bad compression merely deletes context and can increase operational risk.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompressionMetrics:
    """Metrics for evaluating compression quality.

    A compressed output passes the tokenomic test only if the user or
    downstream system can still act correctly.

    Attributes:
        information_retained: Preservation of important task-relevant content (0-5).
        action_clarity: Clarity of the next step or decision (0-5).
        risk_preserved: Preservation of necessary caution, uncertainty, or
            constraints (0-5).
        output_tokens: Total output tokens used.
    """

    information_retained: float = 0.0
    action_clarity: float = 0.0
    risk_preserved: float = 0.0
    output_tokens: int = 0

    @property
    def meaning_score(self) -> float:
        """Combined meaning preservation score."""
        return self.information_retained + self.action_clarity + self.risk_preserved

    @property
    def efficiency(self) -> float:
        """Compression Efficiency Factor (CEF).

        CEF = (InformationRetained + ActionClarity + RiskPreserved) / OutputTokens
        """
        if self.output_tokens <= 0:
            return 0.0
        return self.meaning_score / self.output_tokens

    def passes_tokenomic_test(self, min_efficiency: float = 0.0) -> bool:
        """Check if the compressed output passes the tokenomic test.

        The output passes if compression efficiency is above the minimum
        threshold and all component scores are positive (meaning is preserved).
        """
        return (
            self.information_retained > 0
            and self.action_clarity > 0
            and self.risk_preserved > 0
            and self.efficiency >= min_efficiency
        )


def compression_efficiency(
    information_retained: float,
    action_clarity: float,
    risk_preserved: float,
    output_tokens: int,
) -> float:
    """Compute Compression Efficiency Factor.

    CEF = (InformationRetained + ActionClarity + RiskPreserved) / OutputTokens

    Args:
        information_retained: Preservation of task-relevant content.
        action_clarity: Clarity of next step or decision.
        risk_preserved: Preservation of caution and constraints.
        output_tokens: Total output tokens used.

    Returns:
        Compression efficiency score. Higher is better.
    """
    if output_tokens <= 0:
        return 0.0
    return (information_retained + action_clarity + risk_preserved) / output_tokens


def compare_compression(
    original_tokens: int,
    compressed_tokens: int,
    original_meaning: float,
    compressed_meaning: float,
) -> dict[str, float]:
    """Compare compression between an original and compressed version.

    Returns:
        Dictionary with compression ratio, meaning retention, and
        efficiency gain metrics.
    """
    compression_ratio = (
        compressed_tokens / original_tokens if original_tokens > 0 else 1.0
    )
    meaning_retention = (
        compressed_meaning / original_meaning if original_meaning > 0 else 0.0
    )
    original_eff = original_meaning / original_tokens if original_tokens > 0 else 0.0
    compressed_eff = (
        compressed_meaning / compressed_tokens if compressed_tokens > 0 else 0.0
    )
    efficiency_gain = compressed_eff - original_eff

    return {
        "compression_ratio": compression_ratio,
        "meaning_retention": meaning_retention,
        "original_efficiency": original_eff,
        "compressed_efficiency": compressed_eff,
        "efficiency_gain": efficiency_gain,
    }
