from __future__ import annotations

import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from deepcode.evaluators.base import EvaluationRequest
from deepcode.evaluators.submission import normalize_python_indentation


NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", re.IGNORECASE)


class MlCodingEvaluator:
    name = "ml_coding"

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        return run_submission(
            code=request.code,
            tests=request.tests,
            timeout_seconds=request.environment.get("timeout_seconds", 2),
            comparator=request.environment.get("comparator", "exact"),
            runtime=request.environment.get("runtime", "python"),
        )


def run_submission(
    code: str,
    tests: list[dict[str, Any]],
    timeout_seconds: int | float = 2,
    comparator: str = "exact",
    runtime: str = "python",
) -> dict[str, Any]:
    if runtime not in ("python", "pytorch"):
        raise ValueError(f"Unsupported ML coding runtime: {runtime}")
    results = []
    for test in tests:
        actual_output = _run_single_test(code, test["test"], timeout_seconds, runtime)
        expected_output = str(test["expected_output"]).strip()
        passed = compare_output(actual_output, expected_output, comparator)
        results.append(
            {
                "name": test.get("name", "test"),
                "input": test.get("input", ""),
                "test": test["test"],
                "expected_output": expected_output,
                "actual_output": actual_output,
                "passed": passed,
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "status": "passed" if total and passed_count == total else "failed",
        "passed": passed_count,
        "total": total,
        "results": results,
    }


def compare_output(actual: str, expected: str, comparator: str = "exact", tolerance: float = 1e-4) -> bool:
    actual_norm = _normalize_text(actual)
    expected_norm = _normalize_text(expected)
    if actual_norm == expected_norm:
        return True

    if comparator != "numeric":
        return False

    actual_numbers = NUMBER_PATTERN.findall(actual_norm)
    expected_numbers = NUMBER_PATTERN.findall(expected_norm)
    if len(actual_numbers) != len(expected_numbers) or not actual_numbers:
        return False

    actual_shape = NUMBER_PATTERN.sub("#", actual_norm)
    expected_shape = NUMBER_PATTERN.sub("#", expected_norm)
    if actual_shape != expected_shape:
        return False

    for actual_value, expected_value in zip(actual_numbers, expected_numbers):
        actual_float = float(actual_value)
        expected_float = float(expected_value)
        if not math.isclose(actual_float, expected_float, rel_tol=tolerance, abs_tol=tolerance):
            return False
    return True


def _run_single_test(
    code: str, test_code: str, timeout_seconds: int | float, runtime: str = "python"
) -> str:
    script = _build_script(code, test_code)
    env = _runner_env()
    limiter = _resource_limiter
    if runtime == "pytorch":
        # Native libraries reserve much more virtual address space than their RSS.
        # A 512 MiB RLIMIT_AS prevents torch importing on Linux.
        env.update({
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "DEEPCODE_TORCH_DEVICE": "cpu",
        })
        limiter = lambda: _pytorch_resource_limiter(timeout_seconds)
    with tempfile.TemporaryDirectory(prefix="deepcode-run-") as tmp:
        script_path = Path(tmp) / "submission_test.py"
        script_path.write_text(script, encoding="utf-8")
        try:
            process = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                preexec_fn=limiter() if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return f"Timed out after {timeout_seconds} seconds"

    stdout = process.stdout.strip()
    stderr = process.stderr.strip()
    if process.returncode != 0:
        return stderr or stdout or f"Process exited with code {process.returncode}"
    if stderr:
        return f"{stdout}\n{stderr}".strip()
    return stdout


def _build_script(code: str, test_code: str) -> str:
    formatted_code = normalize_python_indentation(code)
    return f"{formatted_code.rstrip()}\n\n{test_code.rstrip()}\n"


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"-0(\.0+)?(?=\s|\]|\)|,|$)", r"0\1", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("[ ", "[").replace(" ]", "]")
    normalized = normalized.replace("( ", "(").replace(" )", ")")
    return normalized


def _runner_env() -> dict[str, str]:
    allowed = {}
    for key in ("PATH", "PYTHONPATH", "PYTHONHOME", "SYSTEMROOT"):
        if key in os.environ:
            allowed[key] = os.environ[key]
    allowed["PYTHONIOENCODING"] = "utf-8"
    allowed["PYTHONUNBUFFERED"] = "1"
    return allowed


def _resource_limiter():
    def limit_resources():
        try:
            import resource

            resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
            if hasattr(resource, "RLIMIT_AS"):
                resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except Exception:
            pass

    return limit_resources


def _pytorch_resource_limiter(timeout_seconds: int | float):
    def limit_resources():
        try:
            import resource

            cpu_seconds = max(1, math.ceil(timeout_seconds) + 1)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except Exception:
            pass

    return limit_resources
