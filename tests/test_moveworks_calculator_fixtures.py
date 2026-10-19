import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]


class MoveworksCalculatorFixtureTest(unittest.TestCase):
    def evaluate(self, slug, code=None):
        problem = ProblemStore(ROOT / "problems").get_problem(slug)
        if code is None:
            folder = next((ROOT / "problems").glob(f"*-{slug}"))
            code = (folder / "solution.py").read_text()
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        ))

    def test_reference_solutions_pass_visible_contracts(self):
        for slug in ("basic-calculator-ii", "basic-calculator-iii"):
            with self.subTest(slug=slug):
                result = self.evaluate(slug)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], result["total"])

    def test_calculator_ii_rejects_floor_division_for_negative_terms(self):
        code = (ROOT / "problems/520-basic-calculator-ii/solution.py").read_text()
        code = code.replace("-quotient if term < 0 else quotient", "term // number")
        result = self.evaluate("basic-calculator-ii", code)
        self.assertNotEqual(result["status"], "passed", result)

    def test_calculator_iii_rejects_real_division_in_integer_mode(self):
        code = (ROOT / "problems/521-basic-calculator-iii/solution.py").read_text()
        code = code.replace("decimal=False", "decimal=True")
        result = self.evaluate("basic-calculator-iii", code)
        self.assertNotEqual(result["status"], "passed", result)

    def test_decimal_follow_up_rejects_silently_accepted_invalid_input(self):
        code = (ROOT / "problems/521-basic-calculator-iii/solution.py").read_text()
        code += (
            "\n_original_decimal = calculate_decimal\n"
            "def calculate_decimal(s):\n"
            "    try:\n"
            "        return _original_decimal(s)\n"
            "    except ValueError:\n"
            "        return 0.0\n"
        )
        result = self.evaluate("basic-calculator-iii", code)
        self.assertNotEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
