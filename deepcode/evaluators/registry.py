from __future__ import annotations

from typing import Generator

from deepcode.evaluators.base import EvaluationRequest, Evaluator, UnsupportedEvaluatorError
from deepcode.evaluators.ml_coding import MlCodingEvaluator
from deepcode.evaluators.ml_modeling import MlModelingEvaluator
from deepcode.evaluators.ml_torch_lab import MlTorchLabEvaluator
from deepcode.evaluators.ml_torch_modeling import MlTorchModelingEvaluator


_EVALUATORS: dict[str, Evaluator] = {
    MlCodingEvaluator.name: MlCodingEvaluator(),
    MlModelingEvaluator.name: MlModelingEvaluator(),
    MlTorchLabEvaluator.name: MlTorchLabEvaluator(),
    MlTorchModelingEvaluator.name: MlTorchModelingEvaluator(),
}


def get_evaluator(evaluation_type: str) -> Evaluator:
    try:
        return _EVALUATORS[evaluation_type]
    except KeyError as error:
        known = ", ".join(sorted(_EVALUATORS))
        raise UnsupportedEvaluatorError(
            f"Unsupported evaluator `{evaluation_type}`. Registered evaluators: {known}"
        ) from error


def evaluate_submission(request: EvaluationRequest) -> dict:
    evaluator = get_evaluator(request.evaluation_type)
    return evaluator.evaluate(request)


def stream_evaluation_events(request: EvaluationRequest) -> Generator[dict, None, None]:
    evaluator = get_evaluator(request.evaluation_type)
    stream_evaluate = getattr(evaluator, "stream_evaluate", None)
    if callable(stream_evaluate):
        yield from stream_evaluate(request)
        return
    yield {"type": "run_finished", "result": evaluator.evaluate(request)}
