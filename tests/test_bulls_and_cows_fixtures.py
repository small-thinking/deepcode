import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests/reference_solutions/bulls_and_cows.py").read_text()


class BullsAndCowsFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("bulls-and-cows")

    def evaluate(self, code, tests=None):
        return evaluate_submission(EvaluationRequest(
            code=code, problem=self.problem,
            tests=self.problem["tests"] if tests is None else tests,
            environment=self.problem["environment"],
            runtime=self.problem.get("_runtime", {}),
        ))

    def test_reference_passes_visible_contract(self):
        result = self.evaluate(REFERENCE)
        self.assertEqual(result["passed"], len(self.problem["tests"]), result)
        self.assertEqual(result["status"], "passed", result)

    def test_empty_starter_does_not_pass(self):
        self.assertEqual(self.evaluate(self.problem["starter_code"])["passed"], 0)

    def test_duplicate_case_rejects_membership_counting(self):
        code = '''
class Solution:
    def getHint(self, secret, guess):
        bulls = sum(a == b for a, b in zip(secret, guess))
        cows = sum(a != b and b in secret for a, b in zip(secret, guess))
        return f"{bulls}A{cows}B"
'''
        cases = [case for case in self.problem["tests"] if case["name"].startswith("Limit cows")]
        self.assertTrue(cases)
        self.assertNotEqual(self.evaluate(code, cases)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
