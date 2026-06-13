"""Tokenomics Measurement and Benchmarking Framework.

This module formalizes the measurement layer for Tokenomics — a cognitive
resource allocation doctrine for AI systems. It evaluates whether an AI system
produces greater useful cognition per token, not merely fewer tokens.

Components:
    - Token Value Function (token_value)
    - Cognitive Return Metrics (cognitive_return)
    - Salience Allocation Equations (salience)
    - Compression Efficiency Metrics (compression)
    - Benchmark Tasks (benchmark)
    - Runtime Measurement Loop (runtime_loop)
"""

from .token_value import TokenValueFunction, token_value
from .cognitive_return import CognitiveReturnMetrics, cognitive_return_per_token
from .salience import SalienceEngine, salience_score, allocate_budget
from .compression import CompressionMetrics, compression_efficiency
from .benchmark import BenchmarkRunner, tokenomic_gain
from .runtime_loop import RuntimeMeasurementLoop

__all__ = [
    "TokenValueFunction",
    "token_value",
    "CognitiveReturnMetrics",
    "cognitive_return_per_token",
    "SalienceEngine",
    "salience_score",
    "allocate_budget",
    "CompressionMetrics",
    "compression_efficiency",
    "BenchmarkRunner",
    "tokenomic_gain",
    "RuntimeMeasurementLoop",
]
