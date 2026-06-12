from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from deepcode.evaluators.base import EvaluationRequest
from deepcode.evaluators.ml_coding import _build_script, _resource_limiter, _runner_env


ResourceLimiterFactory = Callable[[], Callable[[], None]]


class MlModelingEvaluator:
    name = "ml_modeling"

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        return run_modeling_checks(
            code=request.code,
            tests=request.tests,
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=request.runtime,
        )


def run_modeling_checks(
    code: str,
    tests: list[dict[str, Any]],
    timeout_seconds: int | float = 5,
    runtime: dict[str, Any] | None = None,
    resource_limiter_factory: ResourceLimiterFactory | None = _resource_limiter,
) -> dict[str, Any]:
    results = []
    for test in tests:
        case_timeout = test.get("timeout_seconds", timeout_seconds)
        passed, actual_output = _run_single_check(
            code=code,
            test_code=test["test"],
            timeout_seconds=case_timeout,
            runtime=runtime or {},
            resource_limiter_factory=resource_limiter_factory,
        )
        results.append(
            {
                "name": test.get("name", "check"),
                "input": test.get("input", ""),
                "test": test["test"],
                "expected_output": str(test.get("expected_output", "All assertions pass")).strip(),
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


def _run_single_check(
    code: str,
    test_code: str,
    timeout_seconds: int | float,
    runtime: dict[str, Any],
    resource_limiter_factory: ResourceLimiterFactory | None,
) -> tuple[bool, str]:
    script = _build_script(code, test_code)
    with tempfile.TemporaryDirectory(prefix="deepcode-modeling-") as tmp:
        script_path = Path(tmp) / "submission_check.py"
        script_path.write_text(script, encoding="utf-8")
        try:
            process = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=tmp,
                env=_modeling_env(runtime),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                preexec_fn=resource_limiter_factory() if os.name == "posix" and resource_limiter_factory else None,
            )
        except subprocess.TimeoutExpired:
            return False, f"Timed out after {timeout_seconds} seconds"

    stdout = process.stdout.strip()
    stderr = process.stderr.strip()
    actual_output = _format_output(process.returncode, stdout, stderr)
    return process.returncode == 0, actual_output


def _modeling_env(runtime: dict[str, Any]) -> dict[str, str]:
    env = _runner_env()
    runtime_env_keys = {
        "problem_dir": "DEEPCODE_PROBLEM_DIR",
        "data_path": "DEEPCODE_DATA_PATH",
        "results_path": "DEEPCODE_RESULTS_PATH",
    }
    for runtime_key, env_key in runtime_env_keys.items():
        value = runtime.get(runtime_key)
        if value:
            env[env_key] = str(value)
    return env


def _format_output(returncode: int, stdout: str, stderr: str) -> str:
    if returncode != 0:
        return stderr or stdout or f"Process exited with code {returncode}"
    if stderr:
        return f"{stdout}\n{stderr}".strip()
    return stdout
