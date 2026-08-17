import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (ROOT / "tests" / "reference_solutions" / "reddit_free.py").read_text(encoding="utf-8")


class RedditFreeProblemFixtureTest(unittest.TestCase):
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

    def test_moderator_list_hierarchy_reference_solution_passes(self):
        self._assert_reference_solution_passes("moderator-list-hierarchy")

    def test_report_chain_reference_solution_passes(self):
        self._assert_reference_solution_passes("report-chain")

    def test_word_search_ii_reference_solution_passes(self):
        self._assert_reference_solution_passes("word-search-ii")

    def test_merge_chat_message_windows_reference_solution_passes(self):
        self._assert_reference_solution_passes("merge-chat-message-windows")


if __name__ == "__main__":
    unittest.main()
