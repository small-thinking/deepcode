from __future__ import annotations

from typing import Any

from deepcode.evaluators.base import EvaluationRequest
from deepcode.evaluators.ml_modeling import run_modeling_checks, stream_modeling_checks
from deepcode.evaluators.torch_device import runtime_with_preferred_torch_device


class MlTorchModelingEvaluator:
    name = "ml_torch_modeling"

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        return run_modeling_checks(
            code=request.code,
            tests=request.tests,
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=runtime_with_preferred_torch_device(request.runtime),
            resource_limiter_factory=_torch_resource_limiter,
        )

    def stream_evaluate(self, request: EvaluationRequest):
        yield from stream_modeling_checks(
            code=request.code,
            tests=request.tests,
            timeout_seconds=request.environment.get("timeout_seconds", 5),
            runtime=runtime_with_preferred_torch_device(request.runtime),
            resource_limiter_factory=_torch_resource_limiter,
        )


def _torch_resource_limiter():
    def limit_resources():
        try:
            import resource

            resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
        except Exception:
            pass

    return limit_resources
