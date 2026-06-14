# FableBreaker Mathematical Models

**Python implementations of all formal mathematical models from the FableBreaker Research Journal**

This module contains executable Python implementations of every mathematical model, formula, and algorithm described across the 14 papers in the FableBreaker Research Journal (Volume 1, 2026).

## Overview

The FableBreaker Research Journal spans 5 research areas with 14 published papers. Every mathematical model from these papers has been extracted from the HTML publications and implemented as tested, documented Python code.

### Journal Coverage

| Journal | Papers | Models Implemented |
|---------|--------|-------------------|
| Journal of Adversarial Evaluation | 3 | Seed entropy, coverage probability, family routing |
| Journal of Benchmark Architecture | 3 | Scoring protocols, confidence intervals, game resistance |
| Journal of Certification Systems | 3 | Cryptographic evidence chains, hash collision resistance |
| Journal of Semantic Preservation | 2 | Formal verification, evaluator equivalence |
| Journal of Reproducibility Methods | 3 | API reproducibility, deterministic generation |

## Installation

```python
from fablebreaker.models import *
```

All models are available through the `fablebreaker.models` package.

## Module Structure

### 1. Seed Entropy Models (`seed_entropy.py`)

Mathematical models for analyzing entropy in hidden-seed adversarial generation.

**Key Functions:**
- `calculate_seed_entropy(probabilities)` - Shannon entropy: H = -Σ P(s) log₂ P(s)
- `calculate_route_entropy(family_probs, complexity_probs)` - Route entropy over family selection
- `calculate_structural_entropy(ast_traces, total)` - Entropy of AST structures
- `min_entropy(probabilities)` - Worst-case entropy: H_∞ = -log₂(max P(s))

**Example:**
```python
from fablebreaker.models import calculate_seed_entropy

probs = {"seed1": 0.25, "seed2": 0.25, "seed3": 0.25, "seed4": 0.25}
entropy = calculate_seed_entropy(probs)
# Result: 2.0 bits (uniform distribution over 4 seeds)
```

**Reference:** Medina (2026). "Hidden-Seed Adversarial Generation for Evaluator Stress Testing". *Journal of Adversarial Evaluation*, 1(1).

---

### 2. Coverage Models (`coverage_models.py`)

Probability models for defect detection in adversarial testing.

**Key Functions:**
- `defect_detection_probability(coverage, n)` - P(detect) = 1 - (1 - κ)^n
- `family_weighted_coverage(weights, coverages)` - κ_D = Σ π_i κ_{D|i}
- `coverage_lower_bound(M, δ, k)` - Memorization bound analysis
- `min_entropy_bound(δ)` - H_∞ ≥ -log₂ δ

**Example:**
```python
from fablebreaker.models import defect_detection_probability

# With 10% defect coverage and 20 hidden seeds:
prob = defect_detection_probability(0.1, 20)
# Result: ~87.8% chance of detecting the defect
```

**Reference:** Medina (2026). "Hidden-Seed Adversarial Generation for Evaluator Stress Testing". *Journal of Adversarial Evaluation*, 1(1).

---

### 3. Scoring Confidence Models (`scoring_confidence.py`)

Statistical confidence intervals for benchmark scoring.

**Key Functions:**
- `wilson_score_interval(successes, trials, confidence)` - Wilson score confidence interval
- `per_family_confidence_interval(results, confidence)` - Per-family CI calculation
- `combined_score_confidence(results, weights, confidence)` - Weighted combined score CI
- `minimum_sample_size(margin, confidence)` - Required sample size calculation

**Example:**
```python
from fablebreaker.models import wilson_score_interval

ci = wilson_score_interval(95, 100, 0.95)
print(f"Score: {ci.point_estimate:.2f} [{ci.lower:.2f}, {ci.upper:.2f}]")
# Result: Score: 0.95 [0.89, 0.98]
```

**Reference:** Medina (2026). "Per-Family Scoring and Statistical Confidence in Multi-Family Benchmark Architectures". *Journal of Benchmark Architecture*, 1(1).

---

### 4. Hash Collision Models (`hash_collision.py`)

Cryptographic security analysis for hash-based verification.

**Key Functions:**
- `hash_collision_resistance(n, bits)` - Birthday paradox: P ≈ 1 - e^(-n²/(2·2^b))
- `birthday_attack_probability(n, bits)` - Collision attack success probability
- `hash_verification_security_level(bits)` - Security level = bits/2
- `preimage_attack_probability(n, bits)` - First-preimage attack probability
- `false_positive_rate(bits)` - FPR = 1/2^bits

**Example:**
```python
from fablebreaker.models import hash_collision_resistance

# Probability of collision with 2^40 SHA-256 hashes:
prob = hash_collision_resistance(2**40, 256)
# Result: < 1e-30 (astronomically unlikely)
```

**Reference:** Medina (2026). "Formal Verification of Evaluator Equivalence Through Hash-Based Semantic Preservation". *Journal of Semantic Preservation*, 1(1).

---

### 5. Cryptographic Evidence Chains (`cryptographic_evidence.py`)

Models for tamper-proof audit trails in benchmark certification.

**Key Classes:**
- `EvidenceChain` - Complete cryptographic evidence chain
- `EvidenceLink` - Single link with SHA-256 integrity

**Key Functions:**
- `generate_evidence_chain(id, events)` - Create chain from events
- `verify_evidence_chain(chain)` - Verify chain integrity
- `chain_integrity_proof(chain)` - Generate compact proof

**Example:**
```python
from fablebreaker.models import generate_evidence_chain, verify_evidence_chain

events = [
    ("2026-06-01T10:00:00Z", "candidate_submission", {"candidate": "baseline"}),
    ("2026-06-01T10:01:00Z", "test_execution", {"tests": 100, "passed": 95}),
    ("2026-06-01T10:02:00Z", "certification", {"status": "passed"}),
]

chain = generate_evidence_chain("cert-001", events)
is_valid, msg = verify_evidence_chain(chain)
# Result: True, "Chain valid with 3 links"
```

**Reference:** Medina (2026). "Cryptographic Evidence Chains for Performance Claim Certification". *Journal of Certification Systems*, 1(1).

---

### 6. Adversarial Family Models (`adversarial_families.py`)

Formal specifications for the 8 adversarial attack families.

**Key Classes:**
- `AdversarialFamily` - Family specification with difficulty, attack vector, complexity
- `DifficultyLevel` - Enum: LOW, MEDIUM, HIGH, CRITICAL

**Key Constants:**
- `OVERFLOW_CORRIDOR` - Arithmetic overflow attacks (HIGH)
- `ERASURE_TRAP` - Silent erasure detection (HIGH)
- `CONDITIONAL_CASCADE` - Exponential branching (CRITICAL)
- `DYNAMIC_MATCH_STORM` - Pattern matching overload (HIGH)
- `DUPLICATION_ALIASING` - Identity confusion (HIGH)
- `BRANCH_BALANCE` - Decision tree imbalance (MEDIUM)
- `DEEP_PAIR_PROJECTION` - Nested structure navigation (MEDIUM)
- `MODULAR_ARITHMETIC` - Numeric edge cases (LOW)

**Key Functions:**
- `calculate_family_difficulty_score(family, size)` - Difficulty = size^α
- `family_weight_by_difficulty(families, weights)` - Weight distribution
- `estimate_required_test_cases(family, coverage)` - Sample size estimation

**Example:**
```python
from fablebreaker.models import CONDITIONAL_CASCADE, calculate_family_difficulty_score

score = calculate_family_difficulty_score(CONDITIONAL_CASCADE, 50)
# Result: > 1000 (CRITICAL difficulty grows rapidly)
```

**Reference:** Medina (2026). "A Taxonomy of Evaluator Evasion Strategies in Code Optimization Benchmarks". *Journal of Adversarial Evaluation*, 1(1).

---

### 7. API Reproducibility Models (`api_reproducibility.py`)

Models for deterministic API-driven testing and reproducible scoring.

**Key Classes:**
- `ReproducibilityContext` - Immutable context for deterministic generation
- `ExecutionTrace` - Trace of deterministic execution

**Key Functions:**
- `calculate_reproducibility_score(traces)` - Score = matching_pairs / total_pairs
- `generate_api_request_hash(endpoint, params, version)` - Deterministic request hash
- `verify_api_reproducibility(req, expected, actual)` - Verify reproducible results
- `generate_deterministic_sequence(seed, length, version)` - Pseudo-random sequence

**Example:**
```python
from fablebreaker.models import ReproducibilityContext, ExecutionTrace

ctx = ReproducibilityContext(seed=12345, version="1.0.0", protocol_hash="abc", generator_config={})
trace1 = ExecutionTrace(ctx, test_case_hashes=["hash1"], result_hash="result1")
trace2 = ExecutionTrace(ctx, test_case_hashes=["hash1"], result_hash="result1")

assert trace1.verify_determinism(trace2)  # True - executions are reproducible
```

**Reference:** Medina (2026). "API-Driven Reproducibility for Distributed Benchmark Execution". *Journal of Reproducibility Methods*, 1(1).

---

## Testing

All models include comprehensive test coverage:

```bash
cd fablebreaker
python -m pytest tests/test_mathematical_models.py -v
```

Test coverage includes:
- ✅ Seed entropy calculations
- ✅ Coverage probability models
- ✅ Wilson score confidence intervals
- ✅ Hash collision resistance
- ✅ Cryptographic evidence chains
- ✅ Adversarial family specifications
- ✅ API reproducibility protocols

## Citation

If you use these mathematical models in your research, please cite:

```bibtex
@article{medina2026fablebreaker,
  title={FableBreaker: A Reproducible Benchmark for Semantic-Preserving Evaluator Optimization},
  author={Medina, Freddy},
  journal={DOI},
  volume={10.5281/zenodo.20589250},
  year={2026}
}
```

## License

These mathematical model implementations are part of the FableBreaker benchmark system.

---

**From HTML papers to executable Python**: All 14 papers in the FableBreaker Research Journal have been fully implemented as mathematical models you can import and use.
