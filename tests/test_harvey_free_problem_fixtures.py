import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "harvey_free.py"
).read_text(encoding="utf-8")


class HarveyFreeProblemFixtureTest(unittest.TestCase):
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

    def test_citation_highlighting_reference_solution_passes(self):
        self._assert_reference_solution_passes("source-attribution-highlighter")

    def test_in_memory_unix_file_system_reference_solution_passes(self):
        self._assert_reference_solution_passes("in-memory-unix-file-system")

    def test_text_editor_reference_solution_passes(self):
        self._assert_reference_solution_passes("text-editor")


if __name__ == "__main__":
    unittest.main()
