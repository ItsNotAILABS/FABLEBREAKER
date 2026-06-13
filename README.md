<p align="center">
  <img src="assets/fablebreaker-banner-dark.svg" alt="Fablebreaker Intelligence System" width="100%"/>
</p>

<h1 align="center">Your AI claims survive — or they don't.</h1>

<p align="center">
  <strong>Fablebreaker is the correctness-first intelligence system that certifies whether AI systems actually work — not just whether they say they do.</strong>
</p>

<p align="center">
  <a href="https://github.com/ItsNotAILABS/FABLEBREAKER-BENCHMARK/actions/workflows/pylint.yml"><img src="https://github.com/ItsNotAILABS/FABLEBREAKER-BENCHMARK/actions/workflows/pylint.yml/badge.svg" alt="Pylint"/></a>
  <a href="https://github.com/ItsNotAILABS/FABLEBREAKER-BENCHMARK"><img src="https://img.shields.io/badge/version-2.0.0-7b2ff7?style=flat-square&logo=semver&logoColor=white" alt="Version"/></a>
  <a href="https://github.com/ItsNotAILABS/FABLEBREAKER-BENCHMARK"><img src="https://img.shields.io/badge/status-active-00d2ff?style=flat-square" alt="Status"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-proprietary-302b63?style=flat-square" alt="License"/></a>
  <a href="https://doi.org/10.5281/zenodo.20589250"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20589250-blue?style=flat-square&logo=doi" alt="DOI"/></a>
</p>

<p align="center">
  <a href="#get-started-in-60-seconds"><img src="https://img.shields.io/badge/⚡_Get_Started-60_seconds-00d2ff?style=for-the-badge" alt="Get Started"/></a>
  <a href="#submit-your-ai"><img src="https://img.shields.io/badge/🎯_Submit_Your_AI-prove_it_works-7b2ff7?style=for-the-badge" alt="Submit"/></a>
  <a href="#enterprise"><img src="https://img.shields.io/badge/🏢_Enterprise-certification-gold?style=for-the-badge" alt="Enterprise"/></a>
</p>

---

## The Problem

Every AI company claims their model is better. Faster. Smarter. More accurate.

**Nobody proves it.**

Benchmarks are self-reported. Results are cherry-picked. Evaluations are gameable. The entire AI evaluation landscape runs on trust — and trust is broken.

---

## The Solution

**Fablebreaker doesn't trust. Fablebreaker certifies.**

| What Others Do | What Fablebreaker Does |
|----------------|----------------------|
| Self-reported scores | **Adversarial hidden-seed evaluation** — secret test corpora you can't game |
| One-time benchmarks | **Continuous certification** — your AI re-proves itself on every update |
| Speed over correctness | **Zero-tolerance correctness gate** — one wrong answer = zero certification |
| Gameable datasets | **8 adversarial attack families** — overflow, erasure, cascade, aliasing, and more |
| No accountability | **SHA-256 cryptographic proof chains** — results are locked, tamper-proof, and permanent |

> **Single incorrect output on any hidden test case = disqualified.** Regardless of every other score.

---

## How It Works

```
   You submit your AI system
            │
            ▼
   ┌────────────────────────┐
   │  1. PUBLIC EVALUATION   │  Known dataset — open, fair, reproducible
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │  2. HIDDEN-SEED ATTACK  │  Secret adversarial corpus — 8 attack families
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │  3. HASH VERIFICATION   │  SHA-256 lock — zero tolerance for errors
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │  4. GOVERNANCE REVIEW   │  Expert sign-off — evidence chain verified
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │  5. CERTIFICATION       │  Cryptographic proof — permanent, unforgeable
   └────────────────────────┘
```

**Your system either survives all five stages — or it doesn't get certified.** There is no "partial pass."

---

## Get Started in 60 Seconds

### Install & Run

```bash
git clone https://github.com/ItsNotAILABS/FABLEBREAKER-BENCHMARK.git
cd FABLEBREAKER-BENCHMARK/fablebreaker
python tools/run_full_audit.py --candidate candidates.baseline_candidate
```

### Launch the Service

```bash
python fablebreaker_service.py --host 127.0.0.1 --port 8787
```

### Check It's Running

```bash
curl http://127.0.0.1:8787/api/v1/health
```

### Submit a Candidate

```bash
curl -X POST http://127.0.0.1:8787/api/v1/score \
  -H "Content-Type: application/json" \
  -d '{"candidate": "candidates.baseline_candidate", "dataset": "dataset/public.jsonl"}'
```

That's it. You get a correctness score, per-family breakdown with 95% confidence intervals, and a clear pass/fail certification decision.

---

## Submit Your AI

Any AI system that can evaluate expressions can be submitted for certification. Your candidate must implement:

```python
def evaluate(expr: dict) -> object:
    """
    Evaluate a Fablebreaker AST expression.
    Your output must be semantically identical to the reference evaluator.
    Verification: SHA-256(canonical(your_output)) == SHA-256(canonical(reference_output))
    """
```

**That's the contract.** If your output matches the reference evaluator's output on every case — including hidden adversarial cases you've never seen — you get certified.

---

## The 8 Adversarial Families

Your AI system faces attack from 8 distinct adversarial families, each designed to exploit a different weakness:

| Family | Attack Vector | Difficulty |
|--------|--------------|-----------|
| 🌊 **Overflow Corridor** | Resource exhaustion — pushes budget limits | HIGH |
| 🕳️ **Erasure Trap** | Silent data deletion — tests if you notice | HIGH |
| 🌀 **Conditional Cascade** | Exponential branching — tests deep reasoning | CRITICAL |
| ⚡ **Dynamic Match Storm** | Pattern matching overload | HIGH |
| 👯 **Duplication Aliasing** | Identity confusion — are these the same? | HIGH |
| 🌿 **Branch Balance** | Decision tree imbalance | MEDIUM |
| 🔗 **Deep Pair Projection** | Nested structure navigation | MEDIUM |
| 🔢 **Modular Arithmetic** | Numeric edge cases | LOW |

> If your system can't handle all 8 families under adversarial pressure with zero errors, it's not ready for production. We tell you that before your users find out.

---

## What You Get

### 🆓 Free (Open Source)

- Full public evaluation suite
- Local scoring with per-family breakdown
- 95% confidence intervals on every score
- Public dataset with all 8 adversarial families
- Self-hosted evaluation service
- Complete audit trail

### 💼 Certification Report (Paid)

- Hidden-seed adversarial challenge (secret corpus)
- Full certification with SHA-256 proof chain
- Per-family diagnostic report
- Governance sign-off with evidence pack
- Published certification badge
- Dispute resolution guarantee

### 🏢 Enterprise (Custom)

- Custom adversarial suites for your specific AI system
- CI/CD integration — certification on every commit
- Private leaderboard infrastructure
- Longitudinal regression monitoring
- Custom benchmark design for your domain
- Signed evidence packs for compliance

---

## Enterprise

**For AI labs, devtool companies, and anyone making claims about their AI systems.**

Fablebreaker Enterprise gives you:

| Feature | What It Means |
|---------|--------------|
| **Continuous Monitoring** | Your AI gets re-tested on every release. Regressions caught instantly. |
| **Custom Attack Suites** | Adversarial tests designed for YOUR specific system and domain. |
| **CI/CD Integration** | Certification baked into your deployment pipeline. |
| **Compliance Artifacts** | Signed evidence packs for auditors, investors, and regulators. |
| **Private Leaderboard** | Internal team ranking — see who's actually improving things. |

> **If you're an AI lab making performance claims, you need independent certification.** Otherwise you're grading your own homework.

---

## The Math Engine

Under the hood, Fablebreaker runs on a formal measurement framework:

### Cognitive Return Per Token (CRPT)
```
CRPT = (DQ + ACT + RISK + REUSE + LEARN) / Total_Tokens
```
Every output is measured for decision quality, actionability, risk control, reuse value, and learning gain.

### Token Value Function
```
TV(t) = w_d·D + w_a·A + w_r·R + w_c·C + w_m·M − w_n·N
```
Every token emitted is evaluated by the value it contributes. Noise is penalized.

### Salience Allocation
```
S_i = α·U + β·R + γ·M + δ·T + ε·N − ζ·K
```
Attention is allocated before generation, proportional to urgency, risk, mission relevance, and novelty.

### Hash Verification
```
SHA-256(canonical(output)) == expected_digest
```
All correctness claims are cryptographically locked. Forgery is impossible.

---

## Research

Fablebreaker publishes peer-reviewed research across 5 journals:

| Journal | Papers | Focus |
|---------|--------|-------|
| [Adversarial Evaluation](journal/adversarial-evaluation/) | 3 | Attack generation and stress testing |
| [Benchmark Architecture](journal/benchmark-architecture/) | 3 | Game-resistant evaluation design |
| [Certification Systems](journal/certification-systems/) | 3 | Trust protocols and governance |
| [Semantic Preservation](journal/semantic-preservation/) | 2 | Formal correctness verification |
| [Reproducibility Methods](journal/reproducibility-methods/) | 3 | Deterministic generation and API automation |

📄 **Foundation Paper:** [doi.org/10.5281/zenodo.20589250](https://doi.org/10.5281/zenodo.20589250)

---

## API Reference

All endpoints at `/api/v1/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service status |
| GET | `/manifest` | System capabilities and version |
| GET | `/status` | Current evaluation state |
| GET | `/candidates` | List registered candidates |
| GET | `/families` | List adversarial families |
| POST | `/score` | Submit a candidate for scoring |

**Rate limit:** 60 requests/minute per IP
**Format:** JSON responses with SHA-256 integrity verification

---

## Protocol SDK

For developers building on Fablebreaker:

```python
from fablebreaker.sdk import FableBreakerSDK

sdk = FableBreakerSDK()

# Generate adversarial test cases
corridor = sdk.protocols.overflow_corridors.generate(seed=42, size=30)

# Run full evaluation with tokenomic analysis
report = sdk.analyze(dataset="dataset/public.jsonl",
                     candidate="candidates.baseline_candidate")

# Measure cognitive return per token
crpt = sdk.tokenomics.cognitive_return_per_token(metrics, 100, 200)
```

14 protocols available. All importable. All documented. All reproducible.

---

## Why Fablebreaker?

| | Traditional Benchmarks | Fablebreaker |
|---|---|---|
| **Trust model** | Self-reported | Adversarial certification |
| **Gameability** | Easy — study the test set | Impossible — hidden seeds rotate |
| **Accountability** | None | SHA-256 proof chains + governance |
| **Correctness** | Optional (speed wins) | Non-negotiable (1 error = fail) |
| **Coverage** | Single dimension | 8 adversarial families + cross-benchmark synthesis |
| **Proof** | "We scored 95%" | Cryptographic certification with evidence pack |

---

## Benchmark Ingestion

Fablebreaker consumes all major AI benchmarks as **input signals**:

| Benchmark | Signal Extracted |
|-----------|-----------------|
| **MMLU** | Knowledge breadth |
| **HumanEval** | Functional correctness |
| **GPQA** | Expert reasoning |
| **ARC** | Abstract reasoning |
| **SWE-bench** | Real-world code understanding |
| **TruthfulQA** | Hallucination detection |
| **GSM8K / MATH** | Formal reasoning |
| **BigBench** | Multi-dimensional capability |

> These benchmarks measure individual capabilities. Fablebreaker synthesizes them into a **holistic accountability judgment** backed by adversarial certification.

---

## Contributing

Submit candidates, adversarial families, protocols, or scoring improvements via pull request. Requirements:

1. Pass the full audit pipeline (all 8 families, zero errors)
2. Maintain hash integrity across public and hidden datasets
3. Conform to the [Governance Model](GOVERNANCE.md)
4. Follow the [Packet Policy](PACKET_POLICY.md)

---

<p align="center">
  <img src="assets/fablebreaker-logo.svg" alt="Fablebreaker" width="400"/>
</p>

<p align="center">
  <strong>ItsNotAI LABS</strong><br>
  <em>Correctness before claims. Certification before trust. Accountability before adoption.</em>
</p>

<p align="center">
  <sub>Fablebreaker is not a benchmark. It is a living intelligence system that holds AI accountable.<br>Benchmarks are data it consumes — not what it is.</sub>
</p>
