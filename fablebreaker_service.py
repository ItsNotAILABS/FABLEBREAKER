from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
import uuid
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse

# Import the analysis engine for tokenomics endpoints
sys.path.insert(0, str(Path(__file__).resolve().parent / "fablebreaker"))

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "suites" / "fablebreaker"
MANIFEST = ROOT / "manifests" / "benchmark-manifest.json"

SERVICE_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

logger = logging.getLogger("fablebreaker_service")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Simple rate limiter state
_rate_lock = Lock()
_rate_window: dict[str, deque] = {}
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60


def check_rate_limit(client_ip: str) -> bool:
    """Return True if request is within rate limits."""
    now = time.time()
    with _rate_lock:
        if client_ip not in _rate_window:
            _rate_window[client_ip] = deque()
        window = _rate_window[client_ip]
        # Remove expired entries
        while window and window[0] < now - RATE_LIMIT_WINDOW_SECONDS:
            window.popleft()
        if len(window) >= RATE_LIMIT_REQUESTS:
            return False
        window.append(now)
        return True


def run_json(command: list[str], cwd: Path = SUITE) -> tuple[int, str]:
    """Execute a subprocess and return (returncode, output).

    Security note: command is always a list (no shell=True), and all user-provided
    values are validated/sanitized before being included in the command list.
    """
    proc = subprocess.run(  # noqa: S603 - command list is sanitized by callers
        command, cwd=cwd, text=True, capture_output=True, shell=False,
    )
    return proc.returncode, proc.stdout if proc.returncode == 0 else proc.stderr


class FableBreakerHandler(BaseHTTPRequestHandler):
    server_version = f"FableBreakerService/{SERVICE_VERSION}"

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Rate limit check
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.reply({"error": "rate_limit_exceeded", "retry_after_seconds": RATE_LIMIT_WINDOW_SECONDS}, status=429)
            return

        # Legacy routes (backward compatible)
        if path == "/health":
            self._handle_health()
            return
        if path == "/manifest":
            self._handle_manifest()
            return
        if path == "/score":
            query = parse_qs(parsed.query)
            dataset = query.get("dataset", ["dataset/public.jsonl"])[0]
            candidate = query.get("candidate", ["candidates.baseline_candidate"])[0]
            self._handle_score(dataset, candidate)
            return

        # Versioned API routes
        if path == f"{API_PREFIX}/health":
            self._handle_health()
            return
        if path == f"{API_PREFIX}/manifest":
            self._handle_manifest()
            return
        if path == f"{API_PREFIX}/status":
            self._handle_status()
            return
        if path == f"{API_PREFIX}/candidates":
            self._handle_candidates()
            return
        if path == f"{API_PREFIX}/families":
            self._handle_families()
            return
        if path == f"{API_PREFIX}/score":
            query = parse_qs(parsed.query)
            dataset = query.get("dataset", ["dataset/public.jsonl"])[0]
            candidate = query.get("candidate", ["candidates.baseline_candidate"])[0]
            self._handle_score(dataset, candidate)
            return
        if path == f"{API_PREFIX}/tokenomics/info":
            self._handle_tokenomics_info()
            return
        if path == f"{API_PREFIX}/tokenomics/families":
            self._handle_tokenomics_families()
            return
        if path == f"{API_PREFIX}/tokenomics/criteria":
            self._handle_tokenomics_criteria()
            return

        self.reply({
            "error": "not_found",
            "available_routes": {
                "legacy": ["/health", "/manifest", "/score"],
                "v1": [
                    f"{API_PREFIX}/health",
                    f"{API_PREFIX}/manifest",
                    f"{API_PREFIX}/status",
                    f"{API_PREFIX}/candidates",
                    f"{API_PREFIX}/families",
                    f"{API_PREFIX}/score",
                    f"{API_PREFIX}/tokenomics/info",
                    f"{API_PREFIX}/tokenomics/families",
                    f"{API_PREFIX}/tokenomics/criteria",
                ],
                "v1_post": [
                    f"{API_PREFIX}/score",
                    f"{API_PREFIX}/generate",
                    f"{API_PREFIX}/tokenomics/analyze",
                    f"{API_PREFIX}/tokenomics/score",
                    f"{API_PREFIX}/tokenomics/benchmark",
                ],
            },
        }, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.reply({"error": "rate_limit_exceeded", "retry_after_seconds": RATE_LIMIT_WINDOW_SECONDS}, status=429)
            return

        if path in ("/generate", f"{API_PREFIX}/generate"):
            self._handle_generate()
            return
        if path == f"{API_PREFIX}/score":
            self._handle_post_score()
            return
        if path == f"{API_PREFIX}/tokenomics/analyze":
            self._handle_tokenomics_analyze()
            return
        if path == f"{API_PREFIX}/tokenomics/score":
            self._handle_tokenomics_score()
            return
        if path == f"{API_PREFIX}/tokenomics/benchmark":
            self._handle_tokenomics_benchmark()
            return

        self.reply({"error": "not_found", "paths": [
            "/generate", f"{API_PREFIX}/generate", f"{API_PREFIX}/score",
            f"{API_PREFIX}/tokenomics/analyze", f"{API_PREFIX}/tokenomics/score",
            f"{API_PREFIX}/tokenomics/benchmark",
        ]}, status=404)

    def _handle_health(self) -> None:
        self.reply({
            "ok": True,
            "suite": "fablebreaker",
            "version": SERVICE_VERSION,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    def _handle_manifest(self) -> None:
        try:
            self.reply(json.loads(MANIFEST.read_text(encoding="utf-8")))
        except FileNotFoundError:
            self.reply({"error": "manifest_not_found"}, status=500)

    def _handle_status(self) -> None:
        dataset_dir = SUITE / "dataset"
        datasets = sorted(str(p.name) for p in dataset_dir.glob("*.jsonl")) if dataset_dir.exists() else []
        reports_dir = SUITE / "reports"
        reports = sorted(str(p.name) for p in reports_dir.glob("*.json")) if reports_dir.exists() else []
        self.reply({
            "service_version": SERVICE_VERSION,
            "suite_root": str(SUITE),
            "datasets_available": datasets,
            "reports_available": reports,
            "rate_limit": {
                "requests_per_window": RATE_LIMIT_REQUESTS,
                "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            },
        })

    def _handle_candidates(self) -> None:
        candidates_dir = SUITE / "candidates"
        candidates = []
        if candidates_dir.exists():
            for p in sorted(candidates_dir.glob("*.py")):
                if p.name.startswith("_"):
                    continue
                candidates.append({
                    "module": f"candidates.{p.stem}",
                    "filename": p.name,
                })
        self.reply({"candidates": candidates})

    def _handle_families(self) -> None:
        families = [
            {"name": "dynamic_match_storm", "description": "Chains of pattern matches with multiple tag paths"},
            {"name": "del_erasure_trap", "description": "Erase nodes hiding bomb expressions that must not evaluate"},
            {"name": "duplication_aliasing", "description": "Shared values through dup with deep pair projections"},
            {"name": "branch_balance", "description": "Alternating KEEP/DEL tags with erasure in dead branches"},
            {"name": "deep_pair_projection", "description": "Deeply nested pair construction and path projection"},
            {"name": "modular_arithmetic_net", "description": "Large repeat loops with modular arithmetic"},
            {"name": "overflow_corridor", "description": "Overflow-prone expressions with large integer arithmetic"},
            {"name": "nested_conditional_cascade", "description": "Deeply nested if_zero/match cascades with erasure traps"},
        ]
        self.reply({"families": families, "count": len(families)})

    def _handle_score(self, dataset: str, candidate: str) -> None:
        if not dataset.startswith("dataset/") or ".." in dataset:
            self.reply({"error": "dataset must stay under dataset/ with no path traversal"}, status=400)
            return
        if "/" in candidate or "\\" in candidate or ".." in candidate:
            self.reply({"error": "candidate must be a Python module path, not a filesystem path"}, status=400)
            return
        # Validate candidate is a safe module path (alphanumeric, dots, underscores only)
        if not all(c.isalnum() or c in "._" for c in candidate):
            self.reply({"error": "candidate contains invalid characters"}, status=400)
            return
        request_id = str(uuid.uuid4())[:8]
        logger.info("Score request %s: candidate=%s dataset=%s", request_id, candidate, dataset)
        start = time.time()
        code, output = run_json([sys.executable, "-m", "fablebreaker.scorer", "--dataset", dataset, "--candidate", candidate])
        elapsed = time.time() - start
        if code == 0:
            result = json.loads(output)
            result["request_id"] = request_id
            result["scoring_elapsed_seconds"] = round(elapsed, 3)
            self.reply(result)
        else:
            logger.error("Score request %s failed: %s", request_id, output)
            self.reply({"ok": False, "error": "scoring failed", "request_id": request_id}, status=500)

    def _handle_post_score(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        if size == 0:
            self.reply({"error": "request body required"}, status=400)
            return
        payload = json.loads(self.rfile.read(size))
        dataset = payload.get("dataset", "dataset/public.jsonl")
        candidate = payload.get("candidate", "candidates.baseline_candidate")
        self._handle_score(dataset, candidate)

    def _handle_generate(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(size) or b"{}")
        try:
            seed = int(payload.get("seed", 1701))
            count = int(payload.get("count", 240))
        except (TypeError, ValueError):
            self.reply({"error": "seed and count must be integers"}, status=400)
            return
        if not 0 <= seed <= 2**31 or not 1 <= count <= 10000:
            self.reply({"error": "seed must be 0..2^31, count must be 1..10000"}, status=400)
            return
        split = payload.get("split", "hidden")
        out = payload.get("out", f"dataset/{split}_seed_{seed}.jsonl")
        if split not in {"public", "hidden"}:
            self.reply({"error": "split must be public or hidden"}, status=400)
            return
        if not out.startswith("dataset/") or ".." in out:
            self.reply({"error": "out must stay under dataset/ with no path traversal"}, status=400)
            return
        code, output = run_json(
            [
                sys.executable,
                "-m",
                "fablebreaker.generator",
                "--out",
                out,
                "--count",
                str(count),
                "--seed",
                str(seed),
                "--split",
                split,
            ]
        )
        self.reply({"ok": code == 0, "out": out, "seed": seed, "count": count, "output": output}, status=200 if code == 0 else 500)

    # -----------------------------------------------------------------
    # Tokenomics API handlers
    # -----------------------------------------------------------------

    def _handle_tokenomics_info(self) -> None:
        """GET /api/v1/tokenomics/info — SDK and tokenomics system information."""
        from fablebreaker.sdk import FableBreakerSDK
        sdk = FableBreakerSDK()
        self.reply(sdk.info())

    def _handle_tokenomics_families(self) -> None:
        """GET /api/v1/tokenomics/families — Classification of all benchmark families."""
        from fablebreaker.engine import classify_family
        families = [
            "dynamic_match_storm", "del_erasure_trap", "duplication_aliasing",
            "branch_balance", "deep_pair_projection", "modular_arithmetic_net",
            "overflow_corridor", "nested_conditional_cascade",
        ]
        classifications = {}
        for family in families:
            c = classify_family(family)
            classifications[family] = {
                "task_type": c.task_type,
                "complexity": c.complexity.value,
                "risk": c.risk.value,
                "modules_needed": c.modules_needed,
            }
        self.reply({"families": classifications, "count": len(classifications)})

    def _handle_tokenomics_criteria(self) -> None:
        """GET /api/v1/tokenomics/criteria — Evaluation criteria definitions."""
        self.reply({
            "criteria": {
                "cognitive_return_per_token": "Useful cognition generated per total token spent",
                "compression_fidelity": "Degree to which compressed output preserves meaning",
                "action_conversion_rate": "Percentage of outputs that lead directly to correct action",
                "risk_preservation": "Ability to stay concise without hiding important uncertainty",
                "reuse_extraction_rate": "Frequency of converting interactions into reusable rules, templates, or memory",
                "context_hygiene": "Ability to avoid polluting context with irrelevant information",
                "adaptive_depth_accuracy": "Ability to expand or compress based on task stakes",
                "error_avoidance": "Ability to prevent math, scope, logic, or operational mistakes",
            },
            "scoring_formula": "Score = DQ + ACT + RISK + REUSE + ACCURACY - WASTE",
            "crpt_formula": "CRPT = (DQ + ACT + RISK + REUSE + LEARN) / TotalTokens",
            "tokenomic_gain_formula": "TokenomicGain = (Score_B / Tokens_B) - (Score_A / Tokens_A)",
        })

    def _handle_tokenomics_analyze(self) -> None:
        """POST /api/v1/tokenomics/analyze — Analyze a scoring result through tokenomics."""
        size = int(self.headers.get("Content-Length", "0"))
        if size == 0:
            self.reply({"error": "request body required with scoring_result"}, status=400)
            return
        payload = json.loads(self.rfile.read(size))

        scoring_result = payload.get("scoring_result")
        if not scoring_result:
            self.reply({"error": "scoring_result field required"}, status=400)
            return

        request_id = str(uuid.uuid4())[:8]
        logger.info("Tokenomics analyze request %s", request_id)

        try:
            from fablebreaker.engine import AnalysisEngine
            engine = AnalysisEngine()
            report = engine.analyze_scoring_result(scoring_result)
            result = report.to_dict()
            result["request_id"] = request_id
            self.reply(result)
        except Exception as exc:
            logger.error("Tokenomics analyze %s failed: %s", request_id, exc)
            self.reply({"error": str(exc), "request_id": request_id}, status=500)

    def _handle_tokenomics_score(self) -> None:
        """POST /api/v1/tokenomics/score — Score cognitive return for provided metrics."""
        size = int(self.headers.get("Content-Length", "0"))
        if size == 0:
            self.reply({"error": "request body required"}, status=400)
            return
        payload = json.loads(self.rfile.read(size))

        request_id = str(uuid.uuid4())[:8]

        try:
            from fablebreaker.tokenomics.cognitive_return import (
                CognitiveReturnMetrics, cognitive_return_per_token,
            )
            from fablebreaker.tokenomics.compression import compression_efficiency

            metrics = CognitiveReturnMetrics(
                decision_quality=float(payload.get("decision_quality", 0)),
                actionability=float(payload.get("actionability", 0)),
                risk_control=float(payload.get("risk_control", 0)),
                reuse_value=float(payload.get("reuse_value", 0)),
                learning_gain=float(payload.get("learning_gain", 0)),
            )
            prompt_tokens = int(payload.get("prompt_tokens", 0))
            output_tokens = int(payload.get("output_tokens", 0))
            crpt = cognitive_return_per_token(metrics, prompt_tokens, output_tokens)

            # Optional compression metrics
            ce = 0.0
            if "information_retained" in payload:
                ce = compression_efficiency(
                    float(payload.get("information_retained", 0)),
                    float(payload.get("action_clarity", 0)),
                    float(payload.get("risk_preserved", 0)),
                    output_tokens,
                )

            self.reply({
                "request_id": request_id,
                "cognitive_return": metrics.cognitive_return,
                "cognitive_return_normalized": metrics.normalized,
                "crpt": crpt,
                "compression_efficiency": ce,
                "prompt_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "total_tokens": prompt_tokens + output_tokens,
            })
        except (ValueError, TypeError) as exc:
            self.reply({"error": str(exc), "request_id": request_id}, status=400)

    def _handle_tokenomics_benchmark(self) -> None:
        """POST /api/v1/tokenomics/benchmark — Compare two scoring results."""
        size = int(self.headers.get("Content-Length", "0"))
        if size == 0:
            self.reply({"error": "request body required with baseline and tokenomic scoring results"}, status=400)
            return
        payload = json.loads(self.rfile.read(size))

        baseline_result = payload.get("baseline")
        tokenomic_result = payload.get("tokenomic")
        if not baseline_result or not tokenomic_result:
            self.reply({"error": "both 'baseline' and 'tokenomic' scoring results required"}, status=400)
            return

        request_id = str(uuid.uuid4())[:8]
        logger.info("Tokenomics benchmark request %s", request_id)

        try:
            from fablebreaker.engine import AnalysisEngine
            engine = AnalysisEngine()
            report_a = engine.analyze_scoring_result(baseline_result)
            report_b = engine.analyze_scoring_result(tokenomic_result)

            from fablebreaker.tokenomics.benchmark import tokenomic_gain
            gain = tokenomic_gain(
                score_b=sum(
                    fa.get("cognitive_return", 0)
                    for fa in report_b.family_analyses.values()
                ),
                tokens_b=max(1, sum(
                    fa.get("estimated_tokens", 1)
                    for fa in report_b.family_analyses.values()
                )),
                score_a=sum(
                    fa.get("cognitive_return", 0)
                    for fa in report_a.family_analyses.values()
                ),
                tokens_a=max(1, sum(
                    fa.get("estimated_tokens", 1)
                    for fa in report_a.family_analyses.values()
                )),
            )

            self.reply({
                "request_id": request_id,
                "baseline_report": report_a.to_dict(),
                "tokenomic_report": report_b.to_dict(),
                "tokenomic_gain": gain,
                "hypothesis_result": (
                    "CONFIRMED" if gain > 0
                    else "INCONCLUSIVE" if gain == 0
                    else "REJECTED"
                ),
            })
        except Exception as exc:
            logger.error("Tokenomics benchmark %s failed: %s", request_id, exc)
            self.reply({"error": str(exc), "request_id": request_id}, status=500)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        logger.debug(format, *args)

    def reply(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Service-Version", SERVICE_VERSION)
        self.send_header("X-Request-Time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")


def main() -> None:
    parser = argparse.ArgumentParser(description="FableBreaker Benchmark Certification Service")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8787, help="Listen port")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level))
    server = ThreadingHTTPServer((args.host, args.port), FableBreakerHandler)
    logger.info("FableBreaker service v%s listening on http://%s:%d", SERVICE_VERSION, args.host, args.port)
    logger.info("API prefix: %s", API_PREFIX)
    server.serve_forever()


if __name__ == "__main__":
    main()
