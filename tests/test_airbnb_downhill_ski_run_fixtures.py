import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "airbnb_downhill_ski_run.py"
).read_text(encoding="utf-8")


class AirbnbDownhillSkiRunFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_all_downhill_ski_run_cases(self):
        problem = ProblemStore(ROOT / "problems").get_problem("longest-downhill-ski-run")
        self.assertEqual(problem["companies"], ["Airbnb"])
        self.assertEqual(
            problem["references"],
            [
                {
                    "label": "PracHub: Airbnb downhill ski-run interview question",
                    "url": "https://prachub.com/interview-questions/find-best-downhill-ski-run-from-a-start",
                }
            ],
        )
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
