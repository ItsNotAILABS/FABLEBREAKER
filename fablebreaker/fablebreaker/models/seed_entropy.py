"""Seed entropy calculations for hidden-seed adversarial generation.

Mathematical models for analyzing seed entropy, route entropy, and structural
entropy in the FableBreaker hidden-seed protocol.

Reference:
    Medina, F. (2026). Hidden-Seed Adversarial Generation for Evaluator Stress
    Testing. Journal of Adversarial Evaluation, 1(1), 1-28.
"""

from __future__ import annotations

import math
from typing import Any


def calculate_seed_entropy(probabilities: dict[str, float]) -> float:
    """Calculate Shannon entropy over seed distribution.

    Implements: H_hid = -Σ_s P(s) log₂ P(s)

    Args:
        probabilities: Dictionary mapping seed identifiers to their probabilities.
                      Must sum to 1.0.

    Returns:
        Shannon entropy in bits.

    Raises:
        ValueError: If probabilities don't sum to 1.0 or contain negative values.

    Example:
        >>> probs = {"seed1": 0.25, "seed2": 0.25, "seed3": 0.25, "seed4": 0.25}
        >>> calculate_seed_entropy(probs)
        2.0
    """
    total = sum(probabilities.values())
    if not math.isclose(total, 1.0, rel_tol=1e-9):
        raise ValueError(f"Probabilities must sum to 1.0, got {total}")

    if any(p < 0 for p in probabilities.values()):
        raise ValueError("Probabilities must be non-negative")

    entropy = 0.0
    for p in probabilities.values():
        if p > 0:  # 0 log 0 = 0 by convention
            entropy -= p * math.log2(p)

    return entropy


def calculate_route_entropy(
    family_probs: dict[str, float],
    complexity_probs: dict[str, dict[str, float]],
) -> float:
    """Calculate route entropy over family and complexity bucket selection.

    Route entropy measures uncertainty over the family and complexity bucket
    selected by a seed before AST generation begins.

    Args:
        family_probs: Probability mass assigned to each family.
        complexity_probs: For each family, probability distribution over
                         complexity buckets.

    Returns:
        Route entropy in bits.

    Example:
        >>> families = {"overflow": 0.25, "erasure": 0.25, "cascade": 0.5}
        >>> complexity = {
        ...     "overflow": {"low": 0.5, "high": 0.5},
        ...     "erasure": {"low": 0.5, "high": 0.5},
        ...     "cascade": {"low": 0.5, "high": 0.5},
        ... }
        >>> calculate_route_entropy(families, complexity)
        2.5
    """
    # Calculate joint distribution over (family, complexity) routes
    joint_probs = {}
    for family, family_prob in family_probs.items():
        if family not in complexity_probs:
            raise ValueError(f"Missing complexity distribution for family {family}")
        for complexity, complexity_prob in complexity_probs[family].items():
            route_key = f"{family}:{complexity}"
            joint_probs[route_key] = family_prob * complexity_prob

    return calculate_seed_entropy(joint_probs)


def calculate_structural_entropy(
    ast_traces: dict[str, int],
    total_samples: int,
) -> float:
    """Calculate structural entropy over accepted AST traces.

    Structural entropy measures uncertainty over the shape and structure of
    AST instances conditional on a route selection.

    Args:
        ast_traces: Dictionary mapping normalized AST trace hashes to their
                   occurrence counts.
        total_samples: Total number of samples generated.

    Returns:
        Structural entropy in bits.

    Example:
        >>> traces = {"trace_a": 10, "trace_b": 10, "trace_c": 10, "trace_d": 10}
        >>> calculate_structural_entropy(traces, 40)
        2.0
    """
    if total_samples <= 0:
        raise ValueError("Total samples must be positive")

    probabilities = {
        trace: count / total_samples for trace, count in ast_traces.items()
    }

    return calculate_seed_entropy(probabilities)


def calculate_family_conditional_entropy(
    family: str,
    ast_traces_per_seed: dict[str, str],
    seeds_per_family: dict[str, list[str]],
) -> float:
    """Calculate entropy of AST traces conditional on a specific family.

    Implements: H_hid(F_i) where F_i is a specific adversarial family.

    Args:
        family: Target family identifier.
        ast_traces_per_seed: Mapping from seed ID to its normalized AST trace hash.
        seeds_per_family: Mapping from family to list of seeds that route to it.

    Returns:
        Conditional entropy in bits.

    Raises:
        ValueError: If family is not found in seeds_per_family.

    Example:
        >>> ast_traces = {"seed1": "trace_a", "seed2": "trace_b", "seed3": "trace_a"}
        >>> seeds = {"overflow": ["seed1", "seed2", "seed3"]}
        >>> calculate_family_conditional_entropy("overflow", ast_traces, seeds)
        0.9182958340544896
    """
    if family not in seeds_per_family:
        raise ValueError(f"Family '{family}' not found")

    family_seeds = seeds_per_family[family]
    if not family_seeds:
        return 0.0

    # Count trace occurrences within this family
    trace_counts: dict[str, int] = {}
    for seed in family_seeds:
        if seed in ast_traces_per_seed:
            trace = ast_traces_per_seed[seed]
            trace_counts[trace] = trace_counts.get(trace, 0) + 1

    total = len(family_seeds)
    return calculate_structural_entropy(trace_counts, total)


def min_entropy(probabilities: dict[str, float]) -> float:
    """Calculate min-entropy (worst-case entropy).

    Implements: H_∞ = -log₂(max_s P(s))

    Min-entropy provides a conservative bound on unpredictability by measuring
    only the most likely outcome.

    Args:
        probabilities: Distribution over outcomes.

    Returns:
        Min-entropy in bits.

    Example:
        >>> probs = {"a": 0.5, "b": 0.3, "c": 0.2}
        >>> min_entropy(probs)
        1.0
    """
    if not probabilities:
        return 0.0

    max_prob = max(probabilities.values())
    if max_prob <= 0:
        return float("inf")

    return -math.log2(max_prob)
