"""Statistical confidence interval models for per-family scoring.

Mathematical models for calculating Wilson score intervals and confidence
bounds on per-family benchmark performance.

Reference:
    Medina, F. (2026). Per-Family Scoring and Statistical Confidence in
    Multi-Family Benchmark Architectures. Journal of Benchmark Architecture,
    1(1), 1-29.
"""

from __future__ import annotations

import math
from typing import NamedTuple


class ConfidenceInterval(NamedTuple):
    """Confidence interval with lower and upper bounds."""

    lower: float
    upper: float
    point_estimate: float
    confidence_level: float


def wilson_score_interval(
    num_successes: int,
    num_trials: int,
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Calculate Wilson score confidence interval for binomial proportion.

    The Wilson score interval is more accurate than the normal approximation,
    especially for small sample sizes or extreme proportions.

    Implements the formula:
        p̂ = x/n
        z = z_{α/2} (critical value for confidence level)
        Lower = (p̂ + z²/(2n) - z√(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)
        Upper = (p̂ + z²/(2n) + z√(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)

    Args:
        num_successes: Number of successful trials (correct outputs).
        num_trials: Total number of trials (test cases).
        confidence_level: Desired confidence level (default 0.95 for 95%).

    Returns:
        ConfidenceInterval with lower, upper bounds and point estimate.

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> # 95/100 correct with 95% confidence
        >>> ci = wilson_score_interval(95, 100, 0.95)
        >>> ci.point_estimate
        0.95
        >>> 0.89 < ci.lower < 0.91  # Approximately
        True
    """
    if num_trials <= 0:
        raise ValueError("num_trials must be positive")
    if not 0 <= num_successes <= num_trials:
        raise ValueError("num_successes must be between 0 and num_trials")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be in (0, 1)")

    # Point estimate
    p_hat = num_successes / num_trials

    # Critical value for confidence level (z-score)
    # For 95%, z ≈ 1.96; for 99%, z ≈ 2.576
    z = _z_critical_value(confidence_level)

    # Wilson score interval calculation
    denominator = 1 + z**2 / num_trials

    center_adjustment = p_hat + z**2 / (2 * num_trials)

    margin_base = p_hat * (1 - p_hat) / num_trials + z**2 / (4 * num_trials**2)
    margin = z * math.sqrt(max(0, margin_base))  # max to handle numerical errors

    lower = (center_adjustment - margin) / denominator
    upper = (center_adjustment + margin) / denominator

    # Clamp to [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))

    return ConfidenceInterval(lower, upper, p_hat, confidence_level)


def _z_critical_value(confidence_level: float) -> float:
    """Get z-score critical value for given confidence level.

    Args:
        confidence_level: Confidence level (e.g., 0.95 for 95%).

    Returns:
        Corresponding z-score critical value.
    """
    # Lookup table for common confidence levels
    z_values = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
        0.999: 3.291,
    }

    if confidence_level in z_values:
        return z_values[confidence_level]

    # For other values, use approximation from inverse normal CDF
    # This is a simplified approximation
    alpha = 1 - confidence_level
    return math.sqrt(2) * _inverse_erf(1 - alpha)


def _inverse_erf(x: float) -> float:
    """Approximate inverse error function."""
    # Simple rational approximation
    a = 0.147
    ln_term = math.log(1 - x**2)
    first = 2 / (math.pi * a) + ln_term / 2
    second = ln_term / a

    sign = 1 if x >= 0 else -1
    return sign * math.sqrt(math.sqrt(first**2 - second) - first)


def per_family_confidence_interval(
    family_results: dict[str, tuple[int, int]],
    confidence_level: float = 0.95,
) -> dict[str, ConfidenceInterval]:
    """Calculate confidence intervals for each adversarial family.

    Args:
        family_results: Dictionary mapping family name to (successes, trials).
        confidence_level: Desired confidence level.

    Returns:
        Dictionary mapping family name to its ConfidenceInterval.

    Example:
        >>> results = {
        ...     "overflow": (90, 100),
        ...     "erasure": (85, 100),
        ...     "cascade": (80, 100),
        ... }
        >>> intervals = per_family_confidence_interval(results)
        >>> intervals["overflow"].point_estimate
        0.9
    """
    intervals = {}
    for family, (successes, trials) in family_results.items():
        intervals[family] = wilson_score_interval(successes, trials, confidence_level)
    return intervals


def combined_score_confidence(
    family_results: dict[str, tuple[int, int]],
    family_weights: dict[str, float],
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Calculate confidence interval for weighted combined score.

    Uses propagation of uncertainty for weighted average of family scores.

    Args:
        family_results: Dictionary mapping family name to (successes, trials).
        family_weights: Weight (importance) of each family. Must sum to 1.
        confidence_level: Desired confidence level.

    Returns:
        ConfidenceInterval for the overall weighted score.

    Raises:
        ValueError: If weights don't sum to 1 or families don't match.

    Example:
        >>> results = {"overflow": (90, 100), "erasure": (85, 100)}
        >>> weights = {"overflow": 0.5, "erasure": 0.5}
        >>> ci = combined_score_confidence(results, weights)
        >>> 0.85 < ci.point_estimate < 0.90
        True
    """
    if not math.isclose(sum(family_weights.values()), 1.0, rel_tol=1e-9):
        raise ValueError("Family weights must sum to 1.0")

    if set(family_results.keys()) != set(family_weights.keys()):
        raise ValueError("Family sets must match")

    # Calculate weighted point estimate
    weighted_score = 0.0
    weighted_variance = 0.0

    for family, (successes, trials) in family_results.items():
        weight = family_weights[family]
        proportion = successes / trials

        # Variance of binomial proportion: p(1-p)/n
        variance = proportion * (1 - proportion) / trials

        weighted_score += weight * proportion
        # Variance of weighted sum (assuming independence)
        weighted_variance += (weight**2) * variance

    # Calculate margin of error
    z = _z_critical_value(confidence_level)
    margin = z * math.sqrt(weighted_variance)

    lower = max(0.0, weighted_score - margin)
    upper = min(1.0, weighted_score + margin)

    return ConfidenceInterval(lower, upper, weighted_score, confidence_level)


def family_variance(num_successes: int, num_trials: int) -> float:
    """Calculate variance of binomial proportion estimator.

    Implements: Var(p̂) = p(1-p)/n

    Args:
        num_successes: Number of successes.
        num_trials: Total trials.

    Returns:
        Variance of the proportion estimator.

    Example:
        >>> family_variance(90, 100)
        0.0009000000000000001
    """
    if num_trials <= 0:
        raise ValueError("num_trials must be positive")

    proportion = num_successes / num_trials
    return proportion * (1 - proportion) / num_trials


def minimum_sample_size(
    target_margin: float,
    confidence_level: float = 0.95,
    expected_proportion: float = 0.5,
) -> int:
    """Calculate minimum sample size for desired margin of error.

    Uses conservative estimate assuming p = 0.5 (maximum variance).

    Args:
        target_margin: Desired margin of error (half-width of CI).
        confidence_level: Desired confidence level.
        expected_proportion: Expected success proportion (default 0.5 for conservative estimate).

    Returns:
        Minimum number of samples needed.

    Example:
        >>> # For ±3% margin at 95% confidence
        >>> minimum_sample_size(0.03, 0.95)
        1068
    """
    if not 0 < target_margin < 1:
        raise ValueError("target_margin must be in (0, 1)")
    if not 0 < expected_proportion < 1:
        raise ValueError("expected_proportion must be in (0, 1)")

    z = _z_critical_value(confidence_level)
    p = expected_proportion

    # n = (z² * p * (1-p)) / margin²
    n = (z**2 * p * (1 - p)) / target_margin**2

    return math.ceil(n)
