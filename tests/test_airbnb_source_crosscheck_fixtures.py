import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "airbnb_source_crosscheck.py"
).read_text(encoding="utf-8")


class AirbnbSourceCrosscheckFixtureTest(unittest.TestCase):
    def test_minimum_number_all_digits_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("minimum-number-all-digits")
        result = evaluate_submission(
            EvaluationRequest(
                code=REFERENCE_SOLUTION,
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
