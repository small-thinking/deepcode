from __future__ import annotations

from pathlib import Path
from typing import Any

from deepcode.evaluators.base import EvaluationRequest
from deepcode.evaluators.ml_modeling import run_modeling_checks, stream_modeling_checks
from deepcode.evaluators.ml_torch_modeling import _torch_resource_limiter


class MlTorchLabEvaluator:
    name = "ml_torch_lab"

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        return run_modeling_checks(
            code=request.code,
            tests=_lab_tests(request),
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=request.runtime,
            resource_limiter_factory=_torch_resource_limiter,
        )

    def stream_evaluate(self, request: EvaluationRequest):
        yield from stream_modeling_checks(
            code=request.code,
            tests=_lab_tests(request),
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=request.runtime,
            resource_limiter_factory=_torch_resource_limiter,
        )


def _lab_tests(request: EvaluationRequest) -> list[dict[str, Any]]:
    tests = list(request.tests)
    if request.runtime.get("skip_hidden_harness"):
        return tests

    harness_code = _load_harness(request)
    evaluation = request.problem.get("evaluation", {})
    harness_test: dict[str, Any] = {
        "name": evaluation.get("harness_name", "lab scoring") if isinstance(evaluation, dict) else "lab scoring",
        "input": "local dataset",
        "test": harness_code,
        "expected_output": (
            evaluation.get("expected_output", "Metric threshold met")
            if isinstance(evaluation, dict)
            else "Metric threshold met"
        ),
    }
    if isinstance(evaluation, dict) and evaluation.get("harness_timeout_seconds") is not None:
        harness_test["timeout_seconds"] = evaluation["harness_timeout_seconds"]
    tests.append(harness_test)
    return tests


def _load_harness(request: EvaluationRequest) -> str:
    evaluation = request.problem.get("evaluation", {})
    if not isinstance(evaluation, dict):
        raise ValueError("Lab evaluator requires `evaluation` metadata")

    harness = evaluation.get("harness")
    if not isinstance(harness, str) or not harness.strip():
        raise ValueError("Lab evaluator requires `evaluation.harness`")

    harness_path = Path(harness)
    if harness_path.is_absolute() or ".." in harness_path.parts:
        raise ValueError("Lab evaluator `evaluation.harness` must be problem-relative")

    problem_dir = request.runtime.get("problem_dir")
    if not problem_dir:
        raise ValueError("Lab evaluator requires a runtime problem directory")

    full_path = Path(problem_dir) / harness_path
    if not full_path.is_file():
        raise ValueError(f"Lab harness not found: {harness}")
    return full_path.read_text(encoding="utf-8")
