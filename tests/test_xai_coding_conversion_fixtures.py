import unittest
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
CASES = [(159, "streaming-window-kth"), (339, "satellite-link-assignment")]


class XaiCodingConversionFixturesTest(unittest.TestCase):
    def test_reference_solutions_pass_visible_cases(self):
        for problem_id, slug in CASES:
            with self.subTest(slug=slug), TemporaryDirectory() as temp_dir:
                folder = ROOT / "problems" / f"{problem_id}-{slug}"
                problem_root = Path(temp_dir) / "problems"
                problem_root.mkdir()
                copytree(folder, problem_root / folder.name)
                problem = ProblemStore(problem_root).get_problem(slug)
                result = evaluate_submission(
                    EvaluationRequest(
                        code=(folder / "solution.py").read_text(encoding="utf-8"),
                        problem=problem,
                        tests=problem["tests"],
                        environment=problem["environment"],
                        runtime=problem.get("_runtime", {}),
                    )
                )
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]), result)


if __name__ == "__main__":
    unittest.main()
