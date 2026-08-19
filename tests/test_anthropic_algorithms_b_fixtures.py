import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_algorithms_b.py"
).read_text(encoding="utf-8")


class AnthropicAlgorithmsBFixtureTest(unittest.TestCase):
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

    def test_feasible_recipe_dependency_closure_reference_solution_passes(self):
        self._assert_reference_solution_passes("feasible-recipe-dependency-closure")

    def test_idempotent_token_usage_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("idempotent-token-usage-ledger")

    def test_stable_prompt_affinity_routing_reference_solution_passes(self):
        self._assert_reference_solution_passes("stable-prompt-affinity-routing")

    def test_concurrent_template_registry_reference_solution_passes(self):
        self._assert_reference_solution_passes("concurrent-template-registry")


if __name__ == "__main__":
    unittest.main()
