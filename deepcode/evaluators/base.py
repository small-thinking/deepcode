from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generator, Protocol


class UnsupportedEvaluatorError(ValueError):
    """Raised when a problem asks for an evaluator that is not registered."""


@dataclass(frozen=True)
class EvaluationRequest:
    code: str
    problem: dict[str, Any]
    tests: list[dict[str, Any]]
    environment: dict[str, Any]
    runtime: dict[str, Any] = field(default_factory=dict)

    @property
    def evaluation_type(self) -> str:
        evaluation = self.problem.get("evaluation", {})
        if isinstance(evaluation, dict):
            return str(evaluation.get("type", "ml_coding"))
        return "ml_coding"


class Evaluator(Protocol):
    name: str

    def evaluate(self, request: EvaluationRequest) -> dict[str, Any]:
        """Evaluate a submitted solution and return an API-safe result payload."""


class StreamingEvaluator(Evaluator, Protocol):
    def stream_evaluate(self, request: EvaluationRequest) -> Generator[dict[str, Any], None, None]:
        """Evaluate a submitted solution and yield API-safe progress events."""
