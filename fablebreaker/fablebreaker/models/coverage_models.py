"""Coverage probability models for adversarial defect detection.

Mathematical models for analyzing defect detection probabilities and coverage
guarantees in hidden-seed adversarial testing.

Reference:
    Medina, F. (2026). Hidden-Seed Adversarial Generation for Evaluator Stress
    Testing. Journal of Adversarial Evaluation, 1(1), 1-28.
"""

from __future__ import annotations

import math
from typing import Callable


def defect_detection_probability(
    coverage: float,
    num_hidden_seeds: int,
) -> float:
    """Calculate probability of detecting a defect with given coverage.

    Implements: P(detect) = 1 - (1 - κ_D)^n

    Where κ_D is the defect coverage (probability a random instance exposes
    the defect) and n is the number of independent hidden seed draws.

    Args:
        coverage: Defect coverage κ_D ∈ [0, 1]. Probability that a random
                 instance from the distribution exposes the defect.
        num_hidden_seeds: Number of independent hidden seeds n.

    Returns:
        Probability of detecting at least one failing instance.

    Raises:
        ValueError: If coverage not in [0, 1] or num_hidden_seeds < 0.

    Example:
        >>> # With 10% coverage and 20 hidden seeds:
        >>> defect_detection_probability(0.1, 20)
        0.8784474215233186
    """
    if not 0 <= coverage <= 1:
        raise ValueError(f"Coverage must be in [0, 1], got {coverage}")
    if num_hidden_seeds < 0:
        raise ValueError(f"num_hidden_seeds must be non-negative, got {num_hidden_seeds}")

    # Probability of missing the defect on all n draws
    prob_miss = (1 - coverage) ** num_hidden_seeds

    # Probability of detecting on at least one draw
    return 1 - prob_miss


def family_weighted_coverage(
    family_weights: dict[str, float],
    family_coverages: dict[str, float],
) -> float:
    """Calculate weighted coverage across adversarial families.

    Implements: κ_D = Σ_i π_i κ_{D|i}

    Where π_i is the probability of sampling family i, and κ_{D|i} is the
    defect coverage conditional on family i.

    Args:
        family_weights: Routing probabilities π for each family. Must sum to 1.
        family_coverages: Defect coverage κ_{D|i} for each family.

    Returns:
        Weighted average defect coverage.

    Raises:
        ValueError: If weights don't sum to 1 or families don't match.

    Example:
        >>> weights = {"overflow": 0.3, "erasure": 0.3, "cascade": 0.4}
        >>> coverages = {"overflow": 0.15, "erasure": 0.20, "cascade": 0.10}
        >>> family_weighted_coverage(weights, coverages)
        0.145
    """
    if not math.isclose(sum(family_weights.values()), 1.0, rel_tol=1e-9):
        raise ValueError("Family weights must sum to 1.0")

    if set(family_weights.keys()) != set(family_coverages.keys()):
        raise ValueError("Family sets must match between weights and coverages")

    weighted_coverage = 0.0
    for family, weight in family_weights.items():
        weighted_coverage += weight * family_coverages[family]

    return weighted_coverage


def coverage_lower_bound(
    num_equivalence_classes: int,
    max_class_probability: float,
    memorized_classes: int,
) -> float:
    """Calculate lower bound on coverage under bounded duplication.

    If each hidden seed yields one of M equivalence classes of structurally
    distinct traces, and no class has probability mass > δ, then a candidate
    that memorizes k classes can succeed on at most mass kδ.

    Args:
        num_equivalence_classes: Total number of distinct structural equivalence
                                classes M in the hidden partition.
        max_class_probability: Maximum probability mass δ on any single class.
        memorized_classes: Number of classes k the candidate has memorized.

    Returns:
        Upper bound on probability mass covered by memorization (success without
        generalization).

    Example:
        >>> # 1000 distinct structures, max 0.01 each, memorize 50
        >>> coverage_lower_bound(1000, 0.01, 50)
        0.5
    """
    if num_equivalence_classes < 1:
        raise ValueError("num_equivalence_classes must be positive")
    if not 0 <= max_class_probability <= 1:
        raise ValueError("max_class_probability must be in [0, 1]")
    if memorized_classes < 0:
        raise ValueError("memorized_classes must be non-negative")

    # Maximum mass that can be covered by memorization
    memorization_bound = min(
        memorized_classes * max_class_probability,
        1.0,  # Cannot exceed 100%
    )

    return memorization_bound


def min_entropy_bound(max_probability: float) -> float:
    """Calculate min-entropy lower bound from maximum class probability.

    Implements: H_∞ ≥ -log₂ δ

    Where δ is the maximum probability mass on any single outcome.

    Args:
        max_probability: Maximum probability mass δ on any single outcome.

    Returns:
        Min-entropy lower bound in bits.

    Example:
        >>> min_entropy_bound(0.25)
        2.0
    """
    if not 0 < max_probability <= 1:
        raise ValueError("max_probability must be in (0, 1]")

    return -math.log2(max_probability)


def adaptive_coverage(
    baseline_coverage: float,
    historical_evasion_rate: float,
    amplification_factor: float = 2.0,
) -> float:
    """Calculate adaptively weighted coverage for evasive families.

    Suggested model for future work: reallocate probability mass toward
    families with historically high public-hidden divergence.

    Args:
        baseline_coverage: Base defect coverage κ_D for the family.
        historical_evasion_rate: Fraction of past candidates that failed on
                                this family in hidden eval but not public.
        amplification_factor: Multiplier for high-evasion families.

    Returns:
        Adjusted coverage weight.

    Example:
        >>> adaptive_coverage(0.10, 0.30, 2.0)
        0.16
    """
    if not 0 <= baseline_coverage <= 1:
        raise ValueError("baseline_coverage must be in [0, 1]")
    if not 0 <= historical_evasion_rate <= 1:
        raise ValueError("historical_evasion_rate must be in [0, 1]")

    # Amplify coverage based on historical evasion
    amplified = baseline_coverage * (1 + historical_evasion_rate * amplification_factor)

    # Cap at 1.0
    return min(amplified, 1.0)


def detection_confidence(
    num_tests: int,
    defect_coverage: float,
    confidence_level: float = 0.95,
) -> float:
    """Calculate confidence that a defect will be detected.

    Uses binomial model: probability of k successes in n trials.

    Args:
        num_tests: Number of independent hidden seed tests.
        defect_coverage: Probability each test exposes the defect.
        confidence_level: Desired confidence level (default 95%).

    Returns:
        True if we can be confidence_level certain of detecting at least one
        failure, expressed as actual detection probability.

    Example:
        >>> # Need high detection probability for high confidence
        >>> detection_confidence(50, 0.05, 0.95)
        0.9230840729851517
    """
    return defect_detection_probability(defect_coverage, num_tests)
