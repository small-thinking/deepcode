import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
PROBLEM_DIR = ROOT / "problems" / "448-book-title-string-table"


class BookTitleStringTableFixtureTest(unittest.TestCase):
    def evaluate(self, code):
        problem = ProblemStore(ROOT / "problems").get_problem("book-title-string-table")
        return evaluate_submission(EvaluationRequest(
            code=code, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))

    def test_reference_passes_all_visible_cases(self):
        result = self.evaluate((PROBLEM_DIR / "solution.py").read_text())
        self.assertEqual(result["status"], "passed", result)
        problem = ProblemStore(ROOT / "problems").get_problem("book-title-string-table")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_missing_padding_is_rejected(self):
        code = (PROBLEM_DIR / "solution.py").read_text().replace("line.ljust(width)", "line")
        result = self.evaluate(code)
        self.assertNotEqual(result["status"], "passed", result)
        problem = ProblemStore(ROOT / "problems").get_problem("book-title-string-table")
        self.assertLess(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
