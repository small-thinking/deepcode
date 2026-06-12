from __future__ import annotations

from deepcode.evaluators.base import EvaluationRequest, Evaluator, UnsupportedEvaluatorError
from deepcode.evaluators.ml_coding import MlCodingEvaluator


_EVALUATORS: dict[str, Evaluator] = {
    MlCodingEvaluator.name: MlCodingEvaluator(),
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
