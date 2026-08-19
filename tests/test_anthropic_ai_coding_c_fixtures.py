import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests" / "reference_solutions" / "anthropic_ai_coding_c.py").read_text(encoding="utf-8")
SLUGS = [
    "workspace-layout-state-reducer",
    "idempotent-worker-recovery",
    "sample-aspect-double-descent-diagnostic",
]


class AnthropicAICodingCFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_each_contract(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                result = evaluate_submission(EvaluationRequest(
                    code=REFERENCE,
                    problem=problem,
                    tests=problem["tests"],
                    environment=problem["environment"],
                    runtime=problem.get("_runtime", {}),
                ))
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))

    def test_grouped_policy_contract_has_an_anthropic_association(self):
        problem = ProblemStore(ROOT / "problems").get_problem("grpo-response-logprob-training")
        self.assertIn("Anthropic", problem["companies"])


if __name__ == "__main__":
    unittest.main()
