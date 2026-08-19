import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_algorithms_a.py"
).read_text(encoding="utf-8")


class AnthropicAlgorithmsAFixtureTest(unittest.TestCase):
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

    def test_shard_mode_median_reducer_reference_solution_passes(self):
        self._assert_reference_solution_passes("shard-mode-median-reducer")

    def test_greedy_longest_match_tokenizer_reference_solution_passes(self):
        self._assert_reference_solution_passes("greedy-longest-match-tokenizer")

    def test_stack_snapshot_trace_builder_reference_solution_passes(self):
        self._assert_reference_solution_passes("stack-snapshot-trace-builder")

    def test_dense_matmul_arithmetic_intensity_reference_solution_passes(self):
        self._assert_reference_solution_passes("dense-matmul-arithmetic-intensity")


if __name__ == "__main__":
    unittest.main()
