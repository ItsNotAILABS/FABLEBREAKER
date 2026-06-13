"""Mathematical models for FableBreaker benchmark theory.

This module provides Python implementations of the formal mathematical models
described in the FableBreaker Research Journal papers.

Reference:
    Medina, F. (2026). FableBreaker: A Reproducible Benchmark for
    Semantic-Preserving Evaluator Optimization.
    DOI: https://doi.org/10.5281/zenodo.20589250
"""

from .seed_entropy import (
    calculate_seed_entropy,
    calculate_route_entropy,
    calculate_structural_entropy,
    calculate_family_conditional_entropy,
    min_entropy,
)
from .coverage_models import (
    defect_detection_probability,
    family_weighted_coverage,
    coverage_lower_bound,
    min_entropy_bound,
    adaptive_coverage,
    detection_confidence,
)
from .scoring_confidence import (
    wilson_score_interval,
    per_family_confidence_interval,
    combined_score_confidence,
    family_variance,
    minimum_sample_size,
    ConfidenceInterval,
)
from .hash_collision import (
    hash_collision_resistance,
    birthday_attack_probability,
    hash_verification_security_level,
    collisions_needed_for_probability,
    preimage_attack_probability,
    hash_chain_collision_probability,
    false_positive_rate,
    security_bits_from_work_factor,
    work_factor_from_security_bits,
)
from .cryptographic_evidence import (
    generate_evidence_chain,
    verify_evidence_chain,
    chain_integrity_proof,
    chain_append_proof,
    EvidenceChain,
    EvidenceLink,
)

__all__ = [
    # Seed entropy models
    "calculate_seed_entropy",
    "calculate_route_entropy",
    "calculate_structural_entropy",
    "calculate_family_conditional_entropy",
    "min_entropy",
    # Coverage models
    "defect_detection_probability",
    "family_weighted_coverage",
    "coverage_lower_bound",
    "min_entropy_bound",
    "adaptive_coverage",
    "detection_confidence",
    # Scoring confidence models
    "wilson_score_interval",
    "per_family_confidence_interval",
    "combined_score_confidence",
    "family_variance",
    "minimum_sample_size",
    "ConfidenceInterval",
    # Hash collision models
    "hash_collision_resistance",
    "birthday_attack_probability",
    "hash_verification_security_level",
    "collisions_needed_for_probability",
    "preimage_attack_probability",
    "hash_chain_collision_probability",
    "false_positive_rate",
    "security_bits_from_work_factor",
    "work_factor_from_security_bits",
    # Cryptographic evidence models
    "generate_evidence_chain",
    "verify_evidence_chain",
    "chain_integrity_proof",
    "chain_append_proof",
    "EvidenceChain",
    "EvidenceLink",
]
