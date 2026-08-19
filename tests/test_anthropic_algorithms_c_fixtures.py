import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_algorithms_c.py"
).read_text(encoding="utf-8")


class AnthropicAlgorithmsCFixtureTest(unittest.TestCase):
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

    def test_prioritized_task_dependency_schedule_reference_solution_passes(self):
        self._assert_reference_solution_passes("prioritized-task-dependency-schedule")

    def test_crawl_frontier_budget_planner_reference_solution_passes(self):
        self._assert_reference_solution_passes("crawl-frontier-budget-planner")

    def test_file_inventory_profiler_reference_solution_passes(self):
        self._assert_reference_solution_passes("file-inventory-profiler")

    def test_threshold_image_components_reference_solution_passes(self):
        self._assert_reference_solution_passes("threshold-image-components")

    def test_canonical_url_discovery_graph_reference_solution_passes(self):
        self._assert_reference_solution_passes("canonical-url-discovery-graph")


if __name__ == "__main__":
    unittest.main()
