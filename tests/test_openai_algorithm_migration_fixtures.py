import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "openai_algorithm_migration.py"
).read_text(encoding="utf-8")


class OpenAIAlgorithmMigrationFixtureTest(unittest.TestCase):
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

    def test_multi_source_infection_metrics_reference_solution_passes(self):
        self._assert_reference_solution_passes("multi-source-infection-metrics")

    def test_bounded_overlap_shard_rebalancer_reference_solution_passes(self):
        self._assert_reference_solution_passes("bounded-overlap-shard-rebalancer")

    def test_closed_interval_merge_reference_solution_passes(self):
        self._assert_reference_solution_passes("closed-interval-merge")

    def test_conway_grid_evolution_reference_solution_passes(self):
        self._assert_reference_solution_passes("conway-grid-evolution")


if __name__ == "__main__":
    unittest.main()
