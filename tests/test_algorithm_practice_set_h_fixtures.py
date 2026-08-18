import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_h.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetHFixtureTest(unittest.TestCase):
    def _assert_reference_solution_passes(self, slug):
        problem = ProblemStore(ROOT / "problems").get_problem(slug)
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

    def test_weighted_dag_ski_score_reference_solution_passes(self):
        self._assert_reference_solution_passes("weighted-dag-ski-score")

    def test_maximum_profit_job_scheduling_reference_solution_passes(self):
        self._assert_reference_solution_passes("maximum-profit-job-scheduling")

    def test_prerequisite_installation_order_reference_solution_passes(self):
        self._assert_reference_solution_passes("prerequisite-installation-order")

    def test_ordered_split_stay_plans_reference_solution_passes(self):
        self._assert_reference_solution_passes("ordered-split-stay-plans")


if __name__ == "__main__":
    unittest.main()
