"""Adversarial family mathematical models.

Formal specifications and difficulty metrics for the 8 adversarial attack
families in the FableBreaker benchmark.

Reference:
    Medina, F. (2026). A Taxonomy of Evaluator Evasion Strategies in Code
    Optimization Benchmarks. Journal of Adversarial Evaluation, 1(1), 1-31.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DifficultyLevel(Enum):
    """Difficulty classification for adversarial families."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class AdversarialFamily:
    """Specification of an adversarial attack family."""

    name: str
    difficulty: DifficultyLevel
    attack_vector: str
    description: str
    typical_defect_mechanism: str
    complexity_exponent: float  # Growth rate of attack complexity


# The 8 adversarial families from the FableBreaker benchmark
OVERFLOW_CORRIDOR = AdversarialFamily(
    name="Overflow Corridor",
    difficulty=DifficultyLevel.HIGH,
    attack_vector="Resource exhaustion — pushes budget limits",
    description="Searches the narrow region where intermediate computations "
    "approach the arithmetic boundary while final outputs remain valid",
    typical_defect_mechanism="Assuming unbounded integer identities under "
    "bounded machine arithmetic",
    complexity_exponent=2.1,
)

ERASURE_TRAP = AdversarialFamily(
    name="Erasure Trap",
    difficulty=DifficultyLevel.HIGH,
    attack_vector="Silent data deletion — tests if you notice",
    description="Exploits the difference between syntactic irrelevance and "
    "semantic irrelevance in subtree evaluation",
    typical_defect_mechanism="Discarding conditionally live subtrees that "
    "appear irrelevant under partial evaluation",
    complexity_exponent=1.9,
)

CONDITIONAL_CASCADE = AdversarialFamily(
    name="Conditional Cascade",
    difficulty=DifficultyLevel.CRITICAL,
    attack_vector="Exponential branching — tests deep reasoning",
    description="Nested conditional expressions with deep interaction depth "
    "and non-obvious branch activation patterns",
    typical_defect_mechanism="Failing to preserve precise branch selection "
    "logic under aggressive optimization",
    complexity_exponent=2.5,
)

DYNAMIC_MATCH_STORM = AdversarialFamily(
    name="Dynamic Match Storm",
    difficulty=DifficultyLevel.HIGH,
    attack_vector="Pattern matching overload",
    description="Long chains of pattern matches with varying tag distributions "
    "and accumulated transformations",
    typical_defect_mechanism="Memoizing shallow patterns without handling "
    "accumulation effects",
    complexity_exponent=1.7,
)

DUPLICATION_ALIASING = AdversarialFamily(
    name="Duplication Aliasing",
    difficulty=DifficultyLevel.HIGH,
    attack_vector="Identity confusion — are these the same?",
    description="Expressions with subtle sharing and aliasing that affect "
    "evaluation semantics",
    typical_defect_mechanism="Over-aggressive common subexpression elimination "
    "violating evaluation order",
    complexity_exponent=1.8,
)

BRANCH_BALANCE = AdversarialFamily(
    name="Branch Balance",
    difficulty=DifficultyLevel.MEDIUM,
    attack_vector="Decision tree imbalance",
    description="Conditionals with highly imbalanced branch probabilities "
    "and asymmetric evaluation costs",
    typical_defect_mechanism="Assuming uniform branch frequencies in "
    "optimization heuristics",
    complexity_exponent=1.5,
)

DEEP_PAIR_PROJECTION = AdversarialFamily(
    name="Deep Pair Projection",
    difficulty=DifficultyLevel.MEDIUM,
    attack_vector="Nested structure navigation",
    description="Deeply nested pair construction and projection sequences",
    typical_defect_mechanism="Incorrect fusion of projection chains",
    complexity_exponent=1.6,
)

MODULAR_ARITHMETIC = AdversarialFamily(
    name="Modular Arithmetic",
    difficulty=DifficultyLevel.LOW,
    attack_vector="Numeric edge cases",
    description="Modular arithmetic expressions with carefully chosen moduli "
    "and operand ranges",
    typical_defect_mechanism="Applying non-modular identities to modular "
    "expressions",
    complexity_exponent=1.3,
)

# Complete family registry
ADVERSARIAL_FAMILIES = {
    "overflow_corridor": OVERFLOW_CORRIDOR,
    "erasure_trap": ERASURE_TRAP,
    "conditional_cascade": CONDITIONAL_CASCADE,
    "dynamic_match_storm": DYNAMIC_MATCH_STORM,
    "duplication_aliasing": DUPLICATION_ALIASING,
    "branch_balance": BRANCH_BALANCE,
    "deep_pair_projection": DEEP_PAIR_PROJECTION,
    "modular_arithmetic_net": MODULAR_ARITHMETIC,
}


def calculate_family_difficulty_score(family: AdversarialFamily, size: int) -> float:
    """Calculate difficulty score for a family at given size.

    Uses power-law model: difficulty = size^α where α is the family's
    complexity exponent.

    Args:
        family: The adversarial family.
        size: Program size parameter.

    Returns:
        Difficulty score (higher = more difficult).

    Example:
        >>> score = calculate_family_difficulty_score(CONDITIONAL_CASCADE, 50)
        >>> score > 1000  # Critical difficulty grows rapidly
        True
    """
    return size**family.complexity_exponent


def family_weight_by_difficulty(
    families: list[AdversarialFamily],
    difficulty_weights: Optional[dict[DifficultyLevel, float]] = None,
) -> dict[str, float]:
    """Calculate probability weights for families based on difficulty.

    Args:
        families: List of adversarial families to weight.
        difficulty_weights: Optional weights per difficulty level.
                           If None, uses default: LOW=0.1, MEDIUM=0.2,
                           HIGH=0.3, CRITICAL=0.4.

    Returns:
        Dictionary mapping family name to sampling probability.

    Example:
        >>> weights = family_weight_by_difficulty([OVERFLOW_CORRIDOR, ERASURE_TRAP])
        >>> sum(weights.values())
        1.0
    """
    if difficulty_weights is None:
        difficulty_weights = {
            DifficultyLevel.LOW: 0.1,
            DifficultyLevel.MEDIUM: 0.2,
            DifficultyLevel.HIGH: 0.3,
            DifficultyLevel.CRITICAL: 0.4,
        }

    # Count families at each difficulty level
    difficulty_counts: dict[DifficultyLevel, int] = {}
    for family in families:
        difficulty_counts[family.difficulty] = (
            difficulty_counts.get(family.difficulty, 0) + 1
        )

    # Calculate weights
    weights = {}
    for family in families:
        # Weight = (difficulty_weight) / (families_at_this_difficulty)
        count = difficulty_counts[family.difficulty]
        family_weight = difficulty_weights[family.difficulty] / count
        weights[family.name.lower().replace(" ", "_")] = family_weight

    # Normalize to sum to 1.0
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def estimate_required_test_cases(
    family: AdversarialFamily,
    target_coverage: float = 0.95,
) -> int:
    """Estimate number of test cases needed for target coverage.

    Uses heuristic based on family difficulty and desired coverage.

    Args:
        family: The adversarial family.
        target_coverage: Desired coverage level (0 to 1).

    Returns:
        Estimated number of test cases.

    Example:
        >>> n = estimate_required_test_cases(CONDITIONAL_CASCADE, 0.95)
        >>> n > 100  # Critical families need many tests
        True
    """
    if not 0 < target_coverage <= 1:
        raise ValueError("target_coverage must be in (0, 1]")

    # Base test case count per difficulty level
    base_counts = {
        DifficultyLevel.LOW: 50,
        DifficultyLevel.MEDIUM: 100,
        DifficultyLevel.HIGH: 200,
        DifficultyLevel.CRITICAL: 400,
    }

    base = base_counts[family.difficulty]

    # Adjust for coverage target
    # Higher coverage requires more tests (logarithmic relationship)
    import math

    coverage_multiplier = -math.log(1 - target_coverage)

    return int(base * coverage_multiplier)


def family_interaction_complexity(
    families: list[AdversarialFamily],
) -> float:
    """Calculate complexity score for a multi-family test suite.

    When multiple families are combined, their interactions can create
    emergent complexity beyond individual family difficulty.

    Args:
        families: List of families in the test suite.

    Returns:
        Interaction complexity score.

    Example:
        >>> complexity = family_interaction_complexity([OVERFLOW_CORRIDOR, ERASURE_TRAP])
        >>> complexity > 0
        True
    """
    if not families:
        return 0.0

    # Average complexity exponent
    avg_exponent = sum(f.complexity_exponent for f in families) / len(families)

    # Interaction factor: more families = more potential interactions
    interaction_factor = len(families) * (len(families) - 1) / 2

    return avg_exponent * (1 + 0.1 * interaction_factor)


def get_family_by_name(name: str) -> Optional[AdversarialFamily]:
    """Look up an adversarial family by name.

    Args:
        name: Family name (case-insensitive, spaces/underscores interchangeable).

    Returns:
        AdversarialFamily if found, None otherwise.

    Example:
        >>> family = get_family_by_name("overflow corridor")
        >>> family.difficulty == DifficultyLevel.HIGH
        True
    """
    normalized = name.lower().replace(" ", "_")
    return ADVERSARIAL_FAMILIES.get(normalized)
