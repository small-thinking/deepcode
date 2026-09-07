import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/sample_wise_double_descent_experiment.py').read_text()


class SampleWiseDoubleDescentExperimentFixtureTest(unittest.TestCase):
    def test_reference_passes_visible_experiment_contract(self):
        problem = ProblemStore(ROOT / 'problems').get_problem('sample-wise-double-descent-experiment')
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE, problem=problem, tests=problem['tests'],
            environment=problem['environment'], runtime=problem.get('_runtime', {}),
        ))
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], len(problem['tests']))

    def test_oracle_rejects_unscaled_ridge_penalty(self):
        namespace = {}
        exec(REFERENCE.replace('(np.sqrt(n) * np.sqrt(lam))', 'np.sqrt(lam)'), namespace)
        problem = ProblemStore(ROOT / 'problems').get_problem('sample-wise-double-descent-experiment')
        with self.assertRaises(AssertionError):
            exec(problem['tests'][0]['test'], namespace)


if __name__ == '__main__':
    unittest.main()
