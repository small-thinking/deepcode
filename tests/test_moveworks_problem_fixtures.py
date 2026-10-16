import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests" / "reference_solutions" / "moveworks_coding.py").read_text()
SLUGS = ("hangman-next-letter", "shortest-unique-substring-highlighting")


class MoveworksProblemFixtureTest(unittest.TestCase):
    def test_reference_solutions_pass_visible_contracts(self):
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

    def test_scoring_reference_passes_visible_contract(self):
        problem = ProblemStore(ROOT / "problems").get_problem("string-distinctiveness-scoring")
        code = (ROOT / "problems/513-string-distinctiveness-scoring/solution.py").read_text()
        result = evaluate_submission(EvaluationRequest(
            code=code, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
