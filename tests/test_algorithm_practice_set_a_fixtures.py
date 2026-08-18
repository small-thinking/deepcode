import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_a.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetAFixtureTest(unittest.TestCase):
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

    def test_message_cooldown_logger_reference_solution_passes(self):
        self._assert_reference_solution_passes("message-cooldown-logger")

    def test_post_click_logistic_baseline_reference_solution_passes(self):
        self._assert_reference_solution_passes("post-click-logistic-baseline")

    def test_word_transformation_chain_reference_solution_passes(self):
        self._assert_reference_solution_passes("word-transformation-chain")


if __name__ == "__main__":
    unittest.main()
