"""Tests for mathematical models module.

Comprehensive test suite for all mathematical models extracted from the
FableBreaker Research Journal papers.
"""

import math
import unittest
from fablebreaker.models import (
    # Seed entropy
    calculate_seed_entropy,
    calculate_route_entropy,
    calculate_structural_entropy,
    calculate_family_conditional_entropy,
    min_entropy,
    # Coverage
    defect_detection_probability,
    family_weighted_coverage,
    coverage_lower_bound,
    min_entropy_bound,
    # Scoring confidence
    wilson_score_interval,
    per_family_confidence_interval,
    combined_score_confidence,
    family_variance,
    minimum_sample_size,
    # Hash collision
    hash_collision_resistance,
    birthday_attack_probability,
    hash_verification_security_level,
    preimage_attack_probability,
    false_positive_rate,
    # Evidence chains
    generate_evidence_chain,
    verify_evidence_chain,
    chain_integrity_proof,
    EvidenceChain,
    # Adversarial families
    ADVERSARIAL_FAMILIES,
    DifficultyLevel,
    calculate_family_difficulty_score,
    family_weight_by_difficulty,
    get_family_by_name,
    # API reproducibility
    ReproducibilityContext,
    ExecutionTrace,
    calculate_reproducibility_score,
    generate_api_request_hash,
    verify_api_reproducibility,
)


class TestSeedEntropy(unittest.TestCase):
    """Tests for seed entropy calculations."""

    def test_uniform_distribution_entropy(self):
        """Test entropy of uniform distribution."""
        # 4 equally likely outcomes should give 2 bits of entropy
        probs = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
        entropy = calculate_seed_entropy(probs)
        self.assertTrue(math.isclose(entropy, 2.0, rel_tol=1e-9))

    def test_deterministic_entropy(self):
        """Test entropy of deterministic outcome."""
        # Single outcome with probability 1 should give 0 entropy
        probs = {"a": 1.0}
        entropy = calculate_seed_entropy(probs)
        self.assertTrue(math.isclose(entropy, 0.0, rel_tol=1e-9))

    def test_route_entropy_calculation(self):
        """Test route entropy with families and complexity."""
        families = {"overflow": 0.5, "erasure": 0.5}
        complexity = {
            "overflow": {"low": 0.5, "high": 0.5},
            "erasure": {"low": 0.5, "high": 0.5},
        }
        entropy = calculate_route_entropy(families, complexity)
        self.assertEqual(entropy, 2.0)  # 4 equally likely routes

    def test_structural_entropy(self):
        """Test structural entropy over AST traces."""
        traces = {"trace_a": 10, "trace_b": 10, "trace_c": 10, "trace_d": 10}
        entropy = calculate_structural_entropy(traces, 40)
        self.assertTrue(math.isclose(entropy, 2.0, rel_tol=1e-9))


class TestCoverageModels(unittest.TestCase):
    """Tests for defect coverage probability models."""

    def test_perfect_coverage_detection(self):
        """Test detection with 100% coverage."""
        prob = defect_detection_probability(1.0, 10)
        self.assertTrue(math.isclose(prob, 1.0))

    def test_zero_coverage_detection(self):
        """Test detection with 0% coverage."""
        prob = defect_detection_probability(0.0, 10)
        self.assertTrue(math.isclose(prob, 0.0))

    def test_moderate_coverage_detection(self):
        """Test detection with moderate coverage."""
        # 10% coverage with 20 tests should give ~87.8% detection
        prob = defect_detection_probability(0.1, 20)
        self.assertTrue(0.87 < prob < 0.89)

    def test_family_weighted_coverage(self):
        """Test weighted coverage calculation."""
        weights = {"overflow": 0.3, "erasure": 0.3, "cascade": 0.4}
        coverages = {"overflow": 0.15, "erasure": 0.20, "cascade": 0.10}
        weighted = family_weighted_coverage(weights, coverages)
        expected = 0.3 * 0.15 + 0.3 * 0.20 + 0.4 * 0.10
        self.assertTrue(math.isclose(weighted, expected))

    def test_coverage_lower_bound(self):
        """Test memorization bound calculation."""
        bound = coverage_lower_bound(1000, 0.01, 50)
        self.assertTrue(math.isclose(bound, 0.5))  # 50 * 0.01 = 0.5


class TestScoringConfidence(unittest.TestCase):
    """Tests for statistical confidence interval models."""

    def test_wilson_score_interval_perfect_score(self):
        """Test Wilson interval with 100% success."""
        ci = wilson_score_interval(100, 100, 0.95)
        self.assertAlmostEqual(ci.point_estimate, 1.0)
        self.assertGreater(ci.lower, 0.95)  # Should be close to 1 but not exactly 1
        self.assertAlmostEqual(ci.upper, 1.0, places=5)

    def test_wilson_score_interval_moderate(self):
        """Test Wilson interval with moderate success rate."""
        ci = wilson_score_interval(95, 100, 0.95)
        self.assertAlmostEqual(ci.point_estimate, 0.95)
        self.assertTrue(0.88 < ci.lower < 0.92)
        self.assertTrue(0.97 < ci.upper <= 1.0)

    def test_family_variance_calculation(self):
        """Test variance of binomial proportion."""
        variance = family_variance(90, 100)
        expected = 0.9 * 0.1 / 100
        self.assertTrue(math.isclose(variance, expected))

    def test_minimum_sample_size(self):
        """Test minimum sample size calculation."""
        n = minimum_sample_size(0.03, 0.95)
        self.assertGreater(n, 1000)  # Should need >1000 samples for ±3% margin


class TestHashCollision(unittest.TestCase):
    """Tests for hash collision resistance models."""

    def test_collision_resistance_small_n(self):
        """Test collision probability with few hashes."""
        prob = hash_collision_resistance(100, 256)
        self.assertLess(prob, 1e-70)  # Astronomically unlikely

    def test_birthday_attack_sha256(self):
        """Test birthday attack probability."""
        # Need ~2^128 hashes for 50% collision on SHA-256
        prob = birthday_attack_probability(2**128, 256)
        self.assertTrue(0.3 < prob < 0.5)

    def test_security_level(self):
        """Test security level calculation."""
        level = hash_verification_security_level(256)
        self.assertEqual(level, 128)

    def test_preimage_attack_hardness(self):
        """Test preimage attack is harder than collision."""
        preimage_prob = preimage_attack_probability(2**100, 256)
        self.assertLess(preimage_prob, 1e-40)  # Much harder


class TestCryptographicEvidence(unittest.TestCase):
    """Tests for cryptographic evidence chain models."""

    def test_empty_chain_creation(self):
        """Test creating an empty evidence chain."""
        chain = generate_evidence_chain("test-chain", [])
        self.assertEqual(chain.chain_id, "test-chain")
        self.assertEqual(len(chain.links), 0)
        self.assertTrue(chain.verify_integrity())

    def test_single_link_chain(self):
        """Test chain with one link."""
        events = [("2026-06-01T10:00:00Z", "test_event", {"data": "test"})]
        chain = generate_evidence_chain("chain-1", events)
        self.assertEqual(len(chain.links), 1)
        self.assertTrue(chain.verify_integrity())

    def test_multi_link_chain(self):
        """Test chain with multiple links."""
        events = [
            ("2026-06-01T10:00:00Z", "event1", {"data": "1"}),
            ("2026-06-01T10:01:00Z", "event2", {"data": "2"}),
            ("2026-06-01T10:02:00Z", "event3", {"data": "3"}),
        ]
        chain = generate_evidence_chain("chain-2", events)
        self.assertEqual(len(chain.links), 3)
        self.assertTrue(chain.verify_integrity())

    def test_chain_integrity_proof(self):
        """Test generating integrity proof."""
        events = [("2026-06-01T10:00:00Z", "event", {"data": "test"})]
        chain = generate_evidence_chain("chain-3", events)
        proof = chain_integrity_proof(chain)
        self.assertEqual(proof["chain_id"], "chain-3")
        self.assertEqual(proof["chain_length"], 1)
        self.assertIn("final_hash", proof)

    def test_chain_tampering_detection(self):
        """Test that tampering is detected."""
        events = [("2026-06-01T10:00:00Z", "event", {"data": "test"})]
        chain = generate_evidence_chain("chain-4", events)

        # Tamper with the data
        chain.links[0].data["data"] = "tampered"

        # Chain should fail verification
        is_valid, _ = verify_evidence_chain(chain)
        self.assertFalse(is_valid)


class TestAdversarialFamilies(unittest.TestCase):
    """Tests for adversarial family models."""

    def test_all_families_registered(self):
        """Test that all 8 families are registered."""
        self.assertEqual(len(ADVERSARIAL_FAMILIES), 8)

    def test_family_lookup_by_name(self):
        """Test looking up families by name."""
        family = get_family_by_name("overflow corridor")
        self.assertIsNotNone(family)
        self.assertEqual(family.difficulty, DifficultyLevel.HIGH)

    def test_difficulty_score_calculation(self):
        """Test family difficulty scoring."""
        family = get_family_by_name("conditional_cascade")
        score = calculate_family_difficulty_score(family, 50)
        self.assertGreater(score, 1000)  # CRITICAL difficulty grows rapidly

    def test_family_weight_distribution(self):
        """Test weighting by difficulty."""
        families = list(ADVERSARIAL_FAMILIES.values())
        weights = family_weight_by_difficulty(families)
        self.assertTrue(math.isclose(sum(weights.values()), 1.0))


class TestAPIReproducibility(unittest.TestCase):
    """Tests for API reproducibility protocol models."""

    def test_reproducibility_context_hashing(self):
        """Test deterministic context hashing."""
        ctx1 = ReproducibilityContext(12345, "1.0.0", "abc", {"key": "value"})
        ctx2 = ReproducibilityContext(12345, "1.0.0", "abc", {"key": "value"})
        self.assertEqual(ctx1.calculate_context_hash(), ctx2.calculate_context_hash())

    def test_execution_trace_determinism(self):
        """Test verifying deterministic execution."""
        ctx = ReproducibilityContext(123, "1.0", "abc", {})
        trace1 = ExecutionTrace(ctx, ["hash1"], "result1")
        trace2 = ExecutionTrace(ctx, ["hash1"], "result1")
        self.assertTrue(trace1.verify_determinism(trace2))

    def test_reproducibility_score_perfect(self):
        """Test perfect reproducibility score."""
        ctx = ReproducibilityContext(123, "1.0", "abc", {})
        traces = [
            ExecutionTrace(ctx, ["h1"], "r1"),
            ExecutionTrace(ctx, ["h1"], "r1"),
            ExecutionTrace(ctx, ["h1"], "r1"),
        ]
        score = calculate_reproducibility_score(traces)
        self.assertEqual(score, 1.0)

    def test_api_request_hash_determinism(self):
        """Test API request hashing is deterministic."""
        hash1 = generate_api_request_hash("/score", {"seed": 123}, "1.0")
        hash2 = generate_api_request_hash("/score", {"seed": 123}, "1.0")
        self.assertEqual(hash1, hash2)

    def test_api_reproducibility_verification(self):
        """Test API reproducibility verification."""
        req_hash = "abc123"
        result_hash = "def456"
        is_repro, _ = verify_api_reproducibility(req_hash, result_hash, result_hash)
        self.assertTrue(is_repro)


if __name__ == "__main__":
    unittest.main()
