import unittest
from pathlib import Path
from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/uber_general.py').read_text()
SLUGS = ['bounded-convex-minimization', 'longest-bounded-difference-subarray', 'robots-by-blocker-distances', 'sorted-squares-and-kth-square', 'phone-keypad-combination-count', 'static-and-streaming-islands']


class UberGeneralFixtureTest(unittest.TestCase):
    def test_reference_solutions(self):
        store = ProblemStore(ROOT / 'problems')
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                result = evaluate_submission(EvaluationRequest(
                    code=REFERENCE, problem=problem, tests=problem['tests'],
                    environment=problem['environment'], runtime=problem.get('_runtime', {})))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(problem['tests']))


if __name__ == '__main__':
    unittest.main()
