import ast
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "tests" / "reference_solutions" / "mistral_string_integer_addition.py"
REFERENCE = REFERENCE_PATH.read_text(encoding="utf-8")


class MistralStringIntegerAdditionFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_the_contract(self):
        problem = ProblemStore(ROOT / "problems").get_problem("string-integer-addition")
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        ))

        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_metadata_preserves_source_and_local_assumption_boundary(self):
        problem = ProblemStore(ROOT / "problems").get_problem("string-integer-addition")

        self.assertEqual(problem["companies"], ["Mistral AI"])
        self.assertEqual(
            problem["interview_frequency"]["Mistral AI"]["source_record_ids"],
            ["35c6ce51456d81d1bca2e9d40a40d46e"],
        )
        self.assertIn("nonnegative integers", problem["prompt"])
        self.assertIn("Do not convert an entire operand", problem["prompt"])
        self.assertTrue(any("thread-1144453-1-1.html" in item["url"] for item in problem["references"]))

    def test_reference_does_not_call_int(self):
        tree = ast.parse(REFERENCE)
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        self.assertNotIn("int", called_names)


if __name__ == "__main__":
    unittest.main()
