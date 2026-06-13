# 🛡️ FableBreaker AutoAgent

**Automated adversarial code review for GitHub PRs — native FableBreaker engine intelligence, not a wrapper.**

FableBreaker AutoAgent runs on every pull request, scans changed files using the **internal FableBreaker Intelligence Engine pipeline** (adversarial, correctness, contamination, certification, meta-evaluation), and posts a structured review report as a PR comment. Unlike CodeRabbit or CodeQL, this uses FableBreaker's own cognition — the same engines that power the benchmark itself.

---

## Quick Start (Add to Any Repo)

Create `.github/workflows/fablebreaker.yml` in your repository:

```yaml
name: FableBreaker AutoAgent
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    uses: ItsNotAILABS/FABLEBREAKER-BENCHMARK/.github/workflows/fablebreaker-autoagent.yml@main
    with:
      scan-pattern: "*.py"
      severity-threshold: "medium"
```

That's it. Every PR will now get automated FableBreaker analysis.

---

## What It Does

On every PR, FableBreaker AutoAgent:

1. **Detects changed files** matching your configured pattern
2. **Runs the SDK skill scan** (code review, security, refactoring, documentation)
3. **Runs the native engine pipeline** — adversarial probing, correctness verification, contamination detection, certification evaluation, and meta-evaluation
4. **Posts a structured report** as a PR comment with:
   - Overall verdict (PASS / WARN / FAIL)
   - Issue counts by severity
   - Security risk score
   - Engines used in the analysis
   - Per-file findings in collapsible sections
5. **Optionally fails the check** if critical issues are detected

---

## Example Output

```
## 🛡️ FableBreaker AutoAgent Report

> Automated adversarial code review — correctness before speed.

**Verdict:** ⚠️ WARN — High-severity issues found

| Metric | Value |
|--------|-------|
| Files Scanned | 4 |
| Total Issues | 7 |
| Critical | 0 |
| High | 2 |
| Medium | 3 |
| Low | 2 |
| Security Score | 3.2 / 10 |
```

---

## Configuration Options

| Input | Default | Description |
|-------|---------|-------------|
| `scan-pattern` | `*.py` | Glob pattern for files to analyze |
| `severity-threshold` | `low` | Minimum severity to report: `low`, `medium`, `high`, `critical` |
| `scan-mode` | `changed-files` | What to scan: `changed-files`, `full-repo`, `directory` |
| `target-directory` | `.` | Directory to scan (when `scan-mode` is `directory`) |
| `fail-on-critical` | `true` | Fail the CI check if critical issues are found |
| `max-issues-per-file` | `10` | Maximum issues to report per file |

---

## Outputs

| Output | Description |
|--------|-------------|
| `total-issues` | Total number of issues found |
| `critical-issues` | Number of critical issues found |
| `security-score` | Security risk score (0-10) |
| `verdict` | Overall verdict: `PASS`, `WARN`, `FAIL` |
| `report-path` | Path to the full JSON report |

---

## Scan Modes

### `changed-files` (default)
Only scans files modified in the PR. Fast, focused, and ideal for PR reviews.

### `full-repo`
Scans the entire repository. Use for scheduled audits or initial setup.

### `directory`
Scans a specific directory. Use with `target-directory` for monorepos.

---

## Using as a Composite Action

You can also use FableBreaker AutoAgent as a direct action step:

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0

  - uses: ItsNotAILABS/FABLEBREAKER-BENCHMARK/fablebreaker-autoagent@main
    with:
      github-token: ${{ secrets.GITHUB_TOKEN }}
      scan-pattern: "*.py"
      severity-threshold: "medium"
      fail-on-critical: "true"
```

---

## Running Locally

You can also run the agent locally to preview what it would report:

```bash
# From the FABLEBREAKER-BENCHMARK repo root
python fablebreaker-autoagent/agent.py

# Or with custom settings
INPUT_SCAN_MODE=full-repo INPUT_SCAN_PATTERN="*.py" python fablebreaker-autoagent/agent.py
```

---

## How It Compares

| Feature | FableBreaker AutoAgent | CodeRabbit | GitHub CodeQL |
|---------|----------------------|------------|---------------|
| **Focus** | Correctness + adversarial + native cognition | General code review | Security vulnerabilities |
| **Engine pipeline** | ✅ 5 native engines | ❌ External LLM | ❌ Static analysis |
| **Self-hostable** | ✅ Yes | ❌ No | ✅ Yes |
| **Open source** | ✅ Fully | ❌ No | Partially |
| **PR comments** | ✅ | ✅ | ❌ (annotations) |
| **Security scanning** | ✅ | Limited | ✅ |
| **Adversarial probing** | ✅ Native engine | ❌ | ❌ |
| **Contamination detection** | ✅ Native engine | ❌ | ❌ |
| **Meta-evaluation** | ✅ Self-aware | ❌ | ❌ |
| **Custom rules** | ✅ (SDK skills + engines) | Limited | ✅ (QL queries) |
| **Free** | ✅ Always | Freemium | ✅ for public repos |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FableBreaker AutoAgent                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐   ┌──────────────────────────────────────┐    │
│  │  Trigger  │──▶│         Analysis Pipeline             │    │
│  │ (PR event)│   ├──────────────────────────────────────┤    │
│  └──────────┘   │  Layer 1: SDK Skills                  │    │
│        │         │    code_review, security, refactoring │    │
│        ▼         ├──────────────────────────────────────┤    │
│  ┌──────────┐   │  Layer 2: Native Engine Pipeline      │    │
│  │  Git Diff │   │    adversarial ──▶ correctness ──▶   │    │
│  │  (files)  │   │    contamination ──▶ certification   │    │
│  └──────────┘   │    ──▶ meta_evaluation                │    │
│                  └──────────────────────────────────────┘    │
│                                   │                          │
│                                   ▼                          │
│                          ┌────────────┐                      │
│                          │  PR Comment │                      │
│                          │  (GitHub)   │                      │
│                          └────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Skills & Engines

FableBreaker AutoAgent invokes these per file:

### SDK Skills (Layer 1)

| Skill | Purpose |
|-------|---------|
| `code_review` | Bug detection, logic errors, missed edge cases |
| `security` | Vulnerability scanning, injection risks, auth issues |
| `refactoring` | Structural improvement opportunities |
| `documentation` | Missing docstrings and coverage gaps |
| `self_analysis` | Meta-evaluation and blind spot detection |

### Native Engines (Layer 2)

| Engine | Purpose |
|--------|---------|
| `adversarial` | Generates adversarial pressure, probes exploitable patterns |
| `correctness` | Verifies semantic integrity of outputs |
| `contamination` | Detects benchmark gaming and data leakage patterns |
| `certification` | Evaluates certification readiness and compliance |
| `meta_evaluation` | Self-aware reasoning — evaluates the evaluation itself |

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on improving the AutoAgent.

---

<p align="center">
  <strong>ItsNotAI LABS</strong><br>
  <em>Proof before speed. Correctness before claims. Reproducibility before trust.</em>
</p>
