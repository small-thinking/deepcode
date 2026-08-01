import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "openai_multipart.py"
).read_text(encoding="utf-8")


class OpenAIMultipartProblemFixtureTest(unittest.TestCase):
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

    def test_infection_spread_simulation_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-simulation")

    def test_session_tracker_reference_solution_passes(self):
        self._assert_reference_solution_passes("session-tracker")

    def test_durable_kv_store_reference_solution_passes(self):
        self._assert_reference_solution_passes("durable-in-memory-kv-store")

    def test_sharded_matmul_reference_solution_passes(self):
        self._assert_reference_solution_passes("sharded-matrix-multiplication")

    def test_versioned_social_graph_reference_solution_passes(self):
        self._assert_reference_solution_passes("versioned-social-graph")


if __name__ == "__main__":
    unittest.main()
