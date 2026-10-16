import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests/reference_solutions/moveworks_expansion_coding.py").read_text()
SLUGS = (
    "citation-range-merging",
    "synonym-query-rewrites",
    "text-justification",
    "word-break-sentences",
)


class MoveworksExpansionFixtureTest(unittest.TestCase):
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

    def test_text_justification_rejects_missing_padding(self):
        problem = ProblemStore(ROOT / "problems").get_problem("text-justification")
        code = REFERENCE + "\n_correct_fullJustify = fullJustify\n" + (
            "def fullJustify(words, maxWidth):\n"
            "    return [line.rstrip() for line in _correct_fullJustify(words, maxWidth)]\n"
        )
        result = evaluate_submission(EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        ))
        self.assertNotEqual(result["status"], "passed", result)
        self.assertLess(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
