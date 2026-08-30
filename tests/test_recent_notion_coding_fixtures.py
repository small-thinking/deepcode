import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (ROOT / "tests" / "reference_solutions" / "recent_notion_coding.py").read_text(encoding="utf-8")
SLUGS = (
    "snapshot-set-historical-reads",
    "prefix-cache-state-manager",
    "rocket-engine-flight-time-ledger",
    "leased-work-queue",
)


class RecentNotionCodingFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_each_recent_notion_coding_contract(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
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


if __name__ == "__main__":
    unittest.main()
