import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/fireworks_coding.py').read_text()
SLUGS = ('mutual-friend-recommendation-scores', 'log-fanout-attack-detector', 'gpu-fleet-idle-intervals')


class FireworksProblemFixtureTest(unittest.TestCase):
    def test_reference_solutions_pass_visible_contracts(self):
        store = ProblemStore(ROOT / 'problems')
        for slug in SLUGS:
            with self.subTest(slug=slug):
                p = store.get_problem(slug)
                result = evaluate_submission(EvaluationRequest(
                    code=REFERENCE, problem=p, tests=p['tests'],
                    environment=p['environment'], runtime=p.get('_runtime', {})))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(p['tests']))


if __name__ == '__main__':
    unittest.main()
