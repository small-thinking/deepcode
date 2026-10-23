import unittest
from pathlib import Path
from deepcode.problem_store import ProblemStore
from deepcode.evaluators import EvaluationRequest, evaluate_submission
ROOT = Path(__file__).resolve().parents[1]

class CanvaEvaluatorFixtureTest(unittest.TestCase):
    def test_reference_passes_visible_contract(self):
        problem = ProblemStore(ROOT / 'problems').get_problem('canva-confusion-matrix-evaluator')
        code = (ROOT / 'tests/reference_solutions/canva_evaluator.py').read_text()
        result = evaluate_submission(EvaluationRequest(code=code, problem=problem, tests=problem['tests'], environment=problem['environment'], runtime=problem.get('_runtime', {})))
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], len(problem['tests']))
