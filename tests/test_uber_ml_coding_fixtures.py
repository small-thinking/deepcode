import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
SLUGS = [
    'l1-k-medoids-pickup-locations',
    'linear-logistic-regression-training',
    'deterministic-markov-text-generator',
    'order-completion-slice-metric',
]


class UberMLCodingFixtures(unittest.TestCase):
    def test_reference_solutions(self):
        store = ProblemStore(ROOT / 'problems')
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                path = next((ROOT / 'problems').glob(f'*-{slug}'))
                result = evaluate_submission(EvaluationRequest(
                    code=(path / 'solution.py').read_text(),
                    problem=problem, tests=problem['tests'],
                    environment=problem['environment'], runtime=problem.get('_runtime', {}),
                ))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(problem['tests']))
