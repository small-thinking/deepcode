import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUGS = ["clip-symmetric-contrastive-loss", "alien-dictionary-order"]


class UberSeptemberFixtures(unittest.TestCase):
    def test_new_reference_solutions_pass_every_visible_case(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                problem_dir = next((ROOT / "problems").glob(f"*-{slug}"))
                result = evaluate_submission(
                    EvaluationRequest(
                        code=(problem_dir / "solution.py").read_text(encoding="utf-8"),
                        problem=problem,
                        tests=problem["tests"],
                        environment=problem["environment"],
                        runtime=problem.get("_runtime", {}),
                    )
                )
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))

    def test_clip_solution_can_rely_on_the_positive_dimension_precondition(self):
        problem = ProblemStore(ROOT / "problems").get_problem("clip-symmetric-contrastive-loss")
        solution = """import math

import torch
import torch.nn.functional as F


def clip_contrastive_loss(image_embeddings, text_embeddings, temperature=0.07, normalize=True):
    if image_embeddings.ndim != 2 or text_embeddings.ndim != 2:
        raise ValueError("invalid input of embeddings")
    img_N, img_D = image_embeddings.shape
    text_N, text_D = text_embeddings.shape
    if not (img_N == text_N and img_D == text_D):
        raise ValueError("invalid input with mismatched dimension")
    if temperature <= 0 or not math.isfinite(temperature):
        raise ValueError("temperature should be a valid value")
    if normalize:
        image_embeddings = F.normalize(image_embeddings, p=2, dim=1)
        text_embeddings = F.normalize(text_embeddings, p=2, dim=1)
    matrix = image_embeddings @ text_embeddings.T / temperature
    targets = torch.arange(img_N)
    i2t_loss = F.cross_entropy(matrix, targets)
    t2i_loss = F.cross_entropy(matrix.T, targets)
    return (i2t_loss + t2i_loss) / 2
"""

        result = evaluate_submission(
            EvaluationRequest(
                code=solution,
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
