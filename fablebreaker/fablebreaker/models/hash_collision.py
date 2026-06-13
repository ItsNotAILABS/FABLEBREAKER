"""Hash collision resistance and security models.

Mathematical models for analyzing SHA-256 collision resistance, birthday
attack probabilities, and cryptographic security levels in hash-based
verification protocols.

Reference:
    Medina, F. (2026). Formal Verification of Evaluator Equivalence Through
    Hash-Based Semantic Preservation. Journal of Semantic Preservation,
    1(1), 1-26.
"""

from __future__ import annotations

import math


# SHA-256 produces 256-bit hashes
SHA256_BITS = 256
SHA256_SPACE_SIZE = 2**SHA256_BITS


def hash_collision_resistance(num_hashes: int, hash_bits: int = SHA256_BITS) -> float:
    """Calculate probability of at least one collision in n random hashes.

    Uses birthday paradox approximation:
        P(collision) ≈ 1 - e^(-n²/(2·2^b))

    where n is number of hashes and b is hash output size in bits.

    Args:
        num_hashes: Number of independent hash outputs.
        hash_bits: Size of hash output in bits (default 256 for SHA-256).

    Returns:
        Probability of at least one collision.

    Example:
        >>> # With 2^40 hashes of SHA-256:
        >>> p = hash_collision_resistance(2**40, 256)
        >>> p < 1e-30  # Astronomically unlikely
        True
    """
    if num_hashes < 0:
        raise ValueError("num_hashes must be non-negative")
    if hash_bits <= 0:
        raise ValueError("hash_bits must be positive")

    if num_hashes <= 1:
        return 0.0  # No collision possible

    # Total hash space
    space_size = 2**hash_bits

    # Birthday approximation: P(collision) ≈ 1 - e^(-n²/(2·M))
    exponent = -(num_hashes**2) / (2 * space_size)

    # For very small exponents, use Taylor expansion for accuracy
    if exponent > -1e-10:
        # First-order approximation: 1 - e^x ≈ -x for small x
        return -exponent

    return 1 - math.exp(exponent)


def birthday_attack_probability(
    num_hashes: int,
    hash_bits: int = SHA256_BITS,
) -> float:
    """Calculate birthday attack success probability.

    Birthday attack: adversary generates n hash pairs hoping for a collision.

    Args:
        num_hashes: Number of hash computations the adversary can perform.
        hash_bits: Hash output size in bits.

    Returns:
        Probability of finding a collision.

    Example:
        >>> # Classic birthday problem with 256-bit hash
        >>> # Need ~2^128 hashes for 50% collision probability
        >>> birthday_attack_probability(2**128, 256)
        0.39346934028736658
    """
    return hash_collision_resistance(num_hashes, hash_bits)


def hash_verification_security_level(
    hash_bits: int = SHA256_BITS,
) -> int:
    """Calculate security level in bits for hash-based verification.

    Security level is hash_bits / 2 due to birthday paradox.
    For SHA-256 (256 bits), security level is 128 bits.

    Args:
        hash_bits: Hash output size in bits.

    Returns:
        Security level in bits (work factor for collision attack).

    Example:
        >>> hash_verification_security_level(256)
        128
    """
    return hash_bits // 2


def collisions_needed_for_probability(
    target_probability: float,
    hash_bits: int = SHA256_BITS,
) -> int:
    """Calculate number of hashes needed to achieve target collision probability.

    Inverts the birthday approximation formula.

    Args:
        target_probability: Desired collision probability (0 to 1).
        hash_bits: Hash output size in bits.

    Returns:
        Number of hashes needed (approximate).

    Example:
        >>> # Hashes needed for 50% collision probability with SHA-256
        >>> n = collisions_needed_for_probability(0.5, 256)
        >>> 2**127 < n < 2**129  # Approximately 2^128
        True
    """
    if not 0 < target_probability < 1:
        raise ValueError("target_probability must be in (0, 1)")
    if hash_bits <= 0:
        raise ValueError("hash_bits must be positive")

    space_size = 2**hash_bits

    # From P ≈ 1 - e^(-n²/(2·M)), solve for n:
    # -n²/(2·M) = ln(1 - P)
    # n² = -2·M·ln(1 - P)
    # n = sqrt(-2·M·ln(1 - P))

    n_squared = -2 * space_size * math.log(1 - target_probability)
    n = math.sqrt(n_squared)

    return math.ceil(n)


def preimage_attack_probability(
    num_attempts: int,
    hash_bits: int = SHA256_BITS,
) -> float:
    """Calculate probability of successful first-preimage attack.

    First-preimage resistance: given hash H(x), find any x' such that H(x') = H(x).
    This is harder than collision finding (full hash_bits security, not half).

    Args:
        num_attempts: Number of hash computations the adversary can perform.
        hash_bits: Hash output size in bits.

    Returns:
        Probability of finding a preimage.

    Example:
        >>> # Even with 2^100 attempts, preimage on SHA-256 is infeasible
        >>> p = preimage_attack_probability(2**100, 256)
        >>> p < 1e-40
        True
    """
    if num_attempts < 0:
        raise ValueError("num_attempts must be non-negative")
    if hash_bits <= 0:
        raise ValueError("hash_bits must be positive")

    space_size = 2**hash_bits

    # Each attempt has probability 1/2^b of success
    # Probability of failure on all attempts: (1 - 1/2^b)^n
    # Probability of success on at least one: 1 - (1 - 1/2^b)^n

    single_attempt_prob = 1 / space_size

    # For small probabilities, use approximation: (1-p)^n ≈ e^(-np)
    if num_attempts * single_attempt_prob < 0.1:
        prob_all_fail = math.exp(-num_attempts * single_attempt_prob)
    else:
        prob_all_fail = (1 - single_attempt_prob) ** num_attempts

    return 1 - prob_all_fail


def hash_chain_collision_probability(
    chain_length: int,
    hashes_per_link: int = 1,
    hash_bits: int = SHA256_BITS,
) -> float:
    """Calculate collision probability in a hash chain.

    For evidence chains where each link contains one or more hashes,
    calculate the probability that at least one collision occurs anywhere
    in the chain.

    Args:
        chain_length: Number of links in the chain.
        hashes_per_link: Number of hashes computed per link.
        hash_bits: Hash output size in bits.

    Returns:
        Probability of collision in the entire chain.

    Example:
        >>> # 1000-link chain with 10 hashes per link
        >>> p = hash_chain_collision_probability(1000, 10, 256)
        >>> p < 1e-50  # Still astronomically unlikely
        True
    """
    total_hashes = chain_length * hashes_per_link
    return hash_collision_resistance(total_hashes, hash_bits)


def false_positive_rate(
    hash_bits: int = SHA256_BITS,
) -> float:
    """Calculate false positive rate for hash-based equivalence testing.

    When comparing two expressions using hash equality, what is the
    probability that two non-equivalent expressions have the same hash?

    Args:
        hash_bits: Hash output size in bits.

    Returns:
        False positive rate (collision probability for random inputs).

    Example:
        >>> fpr = false_positive_rate(256)
        >>> fpr == 1 / (2**256)
        True
    """
    return 1 / (2**hash_bits)


def security_bits_from_work_factor(work_factor: float) -> float:
    """Convert computational work factor to security bits.

    Args:
        work_factor: Number of operations required (e.g., 2^128).

    Returns:
        Security level in bits.

    Example:
        >>> security_bits_from_work_factor(2**128)
        128.0
    """
    if work_factor <= 0:
        raise ValueError("work_factor must be positive")

    return math.log2(work_factor)


def work_factor_from_security_bits(security_bits: int) -> int:
    """Convert security bits to computational work factor.

    Args:
        security_bits: Security level in bits.

    Returns:
        Required number of operations.

    Example:
        >>> work_factor_from_security_bits(128)
        340282366920938463463374607431768211456
    """
    if security_bits < 0:
        raise ValueError("security_bits must be non-negative")

    return 2**security_bits
