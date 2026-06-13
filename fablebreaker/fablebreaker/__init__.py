"""FableBreaker Bench — Correctness-first intelligence system.

The FableBreaker package provides:
    - ``astlang``: AST language with 18+ operations and deterministic evaluation
    - ``generator``: Seed-controlled adversarial test generation (8 families)
    - ``scorer``: Certification scoring with per-family breakdown
    - ``protocols``: Protocol SDK (14 published papers, 5 implementations)
    - ``tokenomics``: Tokenomics Measurement and Benchmarking Framework
    - ``engine``: Analysis engine routing pipeline (salience → budget → CRPT)
    - ``sdk``: Unified ``FableBreakerSDK`` entry point

Quick start::

    from fablebreaker.sdk import FableBreakerSDK

    sdk = FableBreakerSDK()
    report = sdk.analyze("dataset/public.jsonl", "candidates.baseline_candidate")
    print(sdk.export_report(report))

Foundation paper: https://doi.org/10.5281/zenodo.20589250
"""

from .sdk import FableBreakerSDK

__all__ = [
    "astlang",
    "generator",
    "scorer",
    "protocols",
    "tokenomics",
    "engine",
    "sdk",
    "FableBreakerSDK",
]
