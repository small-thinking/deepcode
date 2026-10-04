import ast
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (
    ROOT / "tests" / "reference_solutions" / "xai_matrix_transfer.py"
).read_text(encoding="utf-8")


class XAICatalogQualityTest(unittest.TestCase):
    def test_every_xai_associated_starter_parses(self):
        for path in (ROOT / "problems").glob("*/problem.json"):
            problem = json.loads(path.read_text(encoding="utf-8"))
            if "SpaceX AI" in problem.get("companies", []):
                with self.subTest(slug=problem["slug"]):
                    ast.parse(problem.get("starter_code", ""))

    def test_all_gather_and_ring_references_pass_same_contract(self):
        problem = ProblemStore(ROOT / "problems").get_problem(
            "data-parallel-fsdp-matrix-multiplication"
        )
        for pattern in ("all_gather", "ring"):
            with self.subTest(pattern=pattern):
                code = REFERENCE + f"\nfsdp_mat_mul = fsdp_mat_mul_{pattern}\n"
                result = evaluate_submission(
                    EvaluationRequest(
                        code=code,
                        problem=problem,
                        tests=problem["tests"],
                        environment=problem["environment"],
                        runtime=problem.get("_runtime", {}),
                    )
                )
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))
