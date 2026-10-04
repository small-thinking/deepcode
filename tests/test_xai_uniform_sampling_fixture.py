import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUG = "uniform-sampling-without-replacement"
PROBLEM_DIR = ROOT / "problems" / f"469-{SLUG}"


class XaiUniformSamplingFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_visible_cases(self):
        with TemporaryDirectory() as temp_dir:
            problem_root = Path(temp_dir) / "problems"
            problem_root.mkdir()
            copytree(PROBLEM_DIR, problem_root / PROBLEM_DIR.name)
            problem = ProblemStore(problem_root).get_problem(SLUG)
            result = evaluate_submission(
                EvaluationRequest(
                    code=(PROBLEM_DIR / "solution.py").read_text(encoding="utf-8"),
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
