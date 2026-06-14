"""API reproducibility protocol models.

Mathematical models for deterministic API-driven test generation and
reproducible scoring in distributed evaluation settings.

Reference:
    Medina, F. (2026). API-Driven Reproducibility for Distributed Benchmark
    Execution. Journal of Reproducibility Methods, 1(1), 1-25.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ReproducibilityContext:
    """Immutable context for deterministic test generation."""

    seed: int
    version: str
    protocol_hash: str
    generator_config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "seed": self.seed,
            "version": self.version,
            "protocol_hash": self.protocol_hash,
            "generator_config": self.generator_config,
        }

    def calculate_context_hash(self) -> str:
        """Calculate SHA-256 hash of this context.

        Returns:
            Hex-encoded SHA-256 hash.

        Example:
            >>> ctx = ReproducibilityContext(12345, "1.0.0", "abc", {})
            >>> hash_val = ctx.calculate_context_hash()
            >>> len(hash_val) == 64  # SHA-256 produces 64 hex characters
            True
        """
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class ExecutionTrace:
    """Trace of a deterministic execution for reproducibility verification."""

    context: ReproducibilityContext
    test_case_hashes: list[str]
    result_hash: str
    timing_info: Optional[dict[str, float]] = None

    def verify_determinism(self, other: ExecutionTrace) -> bool:
        """Verify that two executions are deterministic.

        Two executions are deterministic if they have:
        1. The same context hash
        2. The same test case hashes in the same order
        3. The same result hash

        Args:
            other: Another execution trace to compare.

        Returns:
            True if executions are deterministic, False otherwise.

        Example:
            >>> ctx = ReproducibilityContext(123, "1.0", "abc", {})
            >>> trace1 = ExecutionTrace(ctx, ["hash1"], "result1")
            >>> trace2 = ExecutionTrace(ctx, ["hash1"], "result1")
            >>> trace1.verify_determinism(trace2)
            True
        """
        return (
            self.context.calculate_context_hash()
            == other.context.calculate_context_hash()
            and self.test_case_hashes == other.test_case_hashes
            and self.result_hash == other.result_hash
        )


def calculate_reproducibility_score(
    executions: list[ExecutionTrace],
) -> float:
    """Calculate reproducibility score across multiple executions.

    Score = (number of matching pairs) / (total possible pairs)

    Args:
        executions: List of execution traces to compare.

    Returns:
        Reproducibility score from 0.0 (no reproducibility) to 1.0 (perfect).

    Example:
        >>> ctx = ReproducibilityContext(123, "1.0", "abc", {})
        >>> traces = [
        ...     ExecutionTrace(ctx, ["h1"], "r1"),
        ...     ExecutionTrace(ctx, ["h1"], "r1"),
        ...     ExecutionTrace(ctx, ["h1"], "r1"),
        ... ]
        >>> calculate_reproducibility_score(traces)
        1.0
    """
    if len(executions) < 2:
        return 1.0  # Trivially reproducible with 0 or 1 execution

    matching_pairs = 0
    total_pairs = 0

    for i in range(len(executions)):
        for j in range(i + 1, len(executions)):
            total_pairs += 1
            if executions[i].verify_determinism(executions[j]):
                matching_pairs += 1

    return matching_pairs / total_pairs if total_pairs > 0 else 1.0


def generate_api_request_hash(
    endpoint: str,
    parameters: dict[str, Any],
    version: str,
) -> str:
    """Generate deterministic hash for an API request.

    Args:
        endpoint: API endpoint name.
        parameters: Request parameters (must be JSON-serializable).
        version: API version string.

    Returns:
        SHA-256 hash of the canonical request representation.

    Example:
        >>> hash1 = generate_api_request_hash("/score", {"seed": 123}, "1.0")
        >>> hash2 = generate_api_request_hash("/score", {"seed": 123}, "1.0")
        >>> hash1 == hash2  # Same inputs = same hash
        True
    """
    request = {"endpoint": endpoint, "parameters": parameters, "version": version}

    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_api_reproducibility(
    request_hash: str,
    expected_result_hash: str,
    actual_result_hash: str,
) -> tuple[bool, str]:
    """Verify that an API call produced reproducible results.

    Args:
        request_hash: Hash of the API request (from generate_api_request_hash).
        expected_result_hash: Hash of expected result from reference execution.
        actual_result_hash: Hash of actual result from current execution.

    Returns:
        Tuple of (is_reproducible, message).

    Example:
        >>> req_hash = "abc123"
        >>> result_hash = "def456"
        >>> is_repro, msg = verify_api_reproducibility(req_hash, result_hash, result_hash)
        >>> is_repro
        True
    """
    if expected_result_hash == actual_result_hash:
        return True, "API call produced reproducible result"

    return False, (
        f"Non-reproducible result for request {request_hash[:8]}...: "
        f"expected {expected_result_hash[:8]}..., "
        f"got {actual_result_hash[:8]}..."
    )


def calculate_protocol_stability_metric(
    version_traces: dict[str, list[ExecutionTrace]],
) -> float:
    """Calculate protocol stability across versions.

    Measures how consistently the protocol produces the same results
    across different versions (for the same semantic inputs).

    Args:
        version_traces: Dictionary mapping version string to execution traces.

    Returns:
        Stability score from 0.0 (unstable) to 1.0 (perfectly stable).

    Example:
        >>> ctx1 = ReproducibilityContext(123, "1.0", "abc", {})
        >>> ctx2 = ReproducibilityContext(123, "2.0", "def", {})
        >>> traces = {
        ...     "1.0": [ExecutionTrace(ctx1, ["h1"], "r1")],
        ...     "2.0": [ExecutionTrace(ctx2, ["h1"], "r1")],
        ... }
        >>> score = calculate_protocol_stability_metric(traces)
        >>> 0.0 <= score <= 1.0
        True
    """
    if len(version_traces) < 2:
        return 1.0  # Trivially stable with 0 or 1 version

    # Compare result hashes across versions
    versions = sorted(version_traces.keys())
    matching_results = 0
    total_comparisons = 0

    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            v1_traces = version_traces[versions[i]]
            v2_traces = version_traces[versions[j]]

            # Compare first trace from each version (assumes same seed)
            if v1_traces and v2_traces:
                total_comparisons += 1
                if v1_traces[0].result_hash == v2_traces[0].result_hash:
                    matching_results += 1

    return matching_results / total_comparisons if total_comparisons > 0 else 1.0


def generate_deterministic_sequence(
    seed: int,
    length: int,
    protocol_version: str,
) -> list[int]:
    """Generate deterministic pseudo-random sequence for test generation.

    Uses seed and protocol version to produce reproducible random numbers.

    Args:
        seed: Random seed.
        length: Number of values to generate.
        protocol_version: Protocol version for versioned determinism.

    Returns:
        List of deterministic pseudo-random integers.

    Example:
        >>> seq1 = generate_deterministic_sequence(12345, 5, "1.0")
        >>> seq2 = generate_deterministic_sequence(12345, 5, "1.0")
        >>> seq1 == seq2  # Same seed = same sequence
        True
    """
    # Combine seed and version into a deterministic initial state
    state = hashlib.sha256(
        f"{seed}:{protocol_version}".encode("utf-8")
    ).digest()

    sequence = []
    for _ in range(length):
        # Hash-based PRNG (not cryptographically secure, but deterministic)
        state = hashlib.sha256(state).digest()
        # Convert first 8 bytes to integer
        value = int.from_bytes(state[:8], byteorder="big")
        sequence.append(value)

    return sequence


def measure_execution_variance(
    traces: list[ExecutionTrace],
) -> dict[str, float]:
    """Measure variance in execution timing across reproducible runs.

    Args:
        traces: List of execution traces with timing information.

    Returns:
        Dictionary with variance metrics for each timed operation.

    Example:
        >>> ctx = ReproducibilityContext(123, "1.0", "abc", {})
        >>> traces = [
        ...     ExecutionTrace(ctx, [], "r", {"op1": 1.0, "op2": 2.0}),
        ...     ExecutionTrace(ctx, [], "r", {"op1": 1.1, "op2": 2.1}),
        ... ]
        >>> variance = measure_execution_variance(traces)
        >>> "op1" in variance
        True
    """
    if not traces:
        return {}

    # Collect timing data per operation
    operation_times: dict[str, list[float]] = {}

    for trace in traces:
        if trace.timing_info:
            for op, time in trace.timing_info.items():
                if op not in operation_times:
                    operation_times[op] = []
                operation_times[op].append(time)

    # Calculate variance for each operation
    variances = {}
    for op, times in operation_times.items():
        if len(times) > 1:
            mean = sum(times) / len(times)
            variance = sum((t - mean) ** 2 for t in times) / len(times)
            variances[op] = variance
        else:
            variances[op] = 0.0

    return variances
