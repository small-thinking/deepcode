import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
STORE = ProblemStore(ROOT / "problems")


class AbridgeDecodeSumFixtureTest(unittest.TestCase):
    def evaluate(self, slug, code):
        problem = STORE.get_problem(slug)
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        )), len(problem["tests"])

    def test_decode_reference_passes_all_visible_cases(self):
        code = (ROOT / "problems/457-nested-bracket-repeat-decoder/solution.py").read_text()
        result, count = self.evaluate("nested-bracket-repeat-decoder", code)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], count)

    def test_decode_single_digit_only_parser_is_rejected(self):
        code = (ROOT / "problems/457-nested-bracket-repeat-decoder/solution.py").read_text()
        code = code.replace("count = count * 10 + int(char)", "count = int(char)")
        result, count = self.evaluate("nested-bracket-repeat-decoder", code)
        self.assertLess(result["passed"], count)

    def test_sum_reference_passes_all_visible_cases(self):
        code = (ROOT / "problems/458-sum-multiples-three-five-seven/solution.py").read_text()
        result, count = self.evaluate("sum-multiples-three-five-seven", code)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], count)

    def test_sum_double_counting_is_rejected(self):
        code = """def sum_multiples(n):
    total = 0
    for value in range(1, n + 1):
        for divisor in (3, 5, 7):
            if value % divisor == 0:
                total += value
    return total
"""
        result, count = self.evaluate("sum-multiples-three-five-seven", code)
        self.assertLess(result["passed"], count)


if __name__ == "__main__":
    unittest.main()
