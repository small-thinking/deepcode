import ast
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "canva_datadog_luma_coding_gaps.py"
).read_text(encoding="utf-8")
TORCH_REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "canva_datadog_luma_torch_coding_gaps.py"
).read_text(encoding="utf-8")
SLUGS = (
    "flat-image-sanitization",
    "image-prediction-retry-lru",
    "binary-focal-loss",
    "grouped-query-attention",
    "async-query-pagination",
    "filtered-moving-window-sums",
    "streaming-time-range-log-store",
    "diffusion-training-step-debug",
    "image-crop-augmentations",
)


def reference_solution_for(problem):
    if problem["slug"] == "diffusion-training-step-debug":
        return TORCH_REFERENCE_SOLUTION
    return REFERENCE_SOLUTION


class CanvaDatadogLumaCodingGapFixtureTest(unittest.TestCase):
    def test_non_torch_contracts_do_not_import_torch(self):
        store = ProblemStore(ROOT / "problems")
        checked = 0
        for slug in SLUGS:
            problem = store.get_problem(slug)
            if problem["evaluation"]["type"] != "ml_modeling":
                continue
            with self.subTest(slug=slug):
                imports = []
                for node in ast.walk(ast.parse(reference_solution_for(problem))):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.append(node.module or "")
                self.assertFalse(any(name.split(".")[0] == "torch" for name in imports))
                checked += 1
        self.assertEqual(checked, 8)

    def test_reference_solution_passes_every_coding_contract(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                result = evaluate_submission(
                    EvaluationRequest(
                        code=reference_solution_for(problem),
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
