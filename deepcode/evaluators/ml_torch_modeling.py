from __future__ import annotations

from typing import Any

from deepcode.evaluators.base import EvaluationRequest
from deepcode.evaluators.ml_modeling import run_modeling_checks


class MlTorchModelingEvaluator:
    name = "ml_torch_modeling"

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        return run_modeling_checks(
            code=request.code,
            tests=request.tests,
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=request.runtime,
        )
