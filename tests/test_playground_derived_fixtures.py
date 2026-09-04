"""Run authored solutions through the same subprocess evaluator used by the UI."""
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]


class PlaygroundDerivedFixturesTest(unittest.TestCase):
    def test_reference_solutions_pass_visible_contracts(self):
        for problem_id in (388, 389, 390, 391):
            with self.subTest(problem_id=problem_id):
                folder = next((ROOT / 'problems').glob(f'{problem_id}-*'))
                problem = json.loads((folder / 'problem.json').read_text())
                tests = json.loads((folder / 'tests.json').read_text())
                result = evaluate_submission(EvaluationRequest(
                    code=(folder / 'solution.py').read_text(),
                    problem=problem,
                    tests=tests,
                    environment=problem['environment'],
                    runtime={},
                ))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(tests))


if __name__ == '__main__':
    unittest.main()
