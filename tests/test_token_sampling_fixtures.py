import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from deepcode.problem_store import ProblemStore
from deepcode.runner import run_submission


ROOT = Path(__file__).resolve().parents[1]


class TokenSamplingFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("top-p-nucleus-sampling")
        cls.reference = (
            ROOT / "tests/reference_solutions/top_k_top_p_sampling.py"
        ).read_text(encoding="utf-8")

    def assert_fixture_rejects(self, name, replacement):
        test = next(item for item in self.problem["tests"] if item["name"] == name)
        result = run_submission(
            code=self.reference + "\n" + replacement,
            tests=[test],
            timeout_seconds=self.problem["environment"]["timeout_seconds"],
            comparator=self.problem["environment"]["comparator"],
            runtime=self.problem["environment"]["runtime"],
        )
        self.assertEqual(result["status"], "failed", result)
        self.assertIn("AssertionError", result["results"][0]["actual_output"])

    def test_fixture_rejects_applying_top_p_before_top_k(self):
        self.assert_fixture_rejects(
            "combined top-p uses the renormalized top-k distribution",
            """
def sample_token(logits, top_k=None, top_p=1.0, temperature=1.0):
    ordered = torch.argsort(logits, descending=True, stable=True)
    probabilities = torch.softmax(logits[ordered] / temperature, dim=0)
    count = min(ordered.numel(), int((probabilities.cumsum(0) < top_p).sum()) + 1)
    ordered = ordered[:count]
    probabilities = probabilities[:count]
    if top_k:
        ordered = ordered[:top_k]
        probabilities = probabilities[:top_k]
    return int(ordered[torch.multinomial(probabilities, 1)].item())
""",
        )

    def test_fixture_rejects_uniform_top_k_sampling(self):
        self.assert_fixture_rejects(
            "top-k samples proportionally instead of uniformly or greedily",
            """
def top_k_sample(logits, top_k, temperature=1.0):
    ordered = torch.argsort(logits, descending=True, stable=True)[:top_k]
    return int(ordered[torch.randint(ordered.numel(), (1,))].item())
""",
        )

    def test_fixture_rejects_uniform_top_p_sampling(self):
        self.assert_fixture_rejects(
            "top-p-only sampling follows conditional probabilities",
            """
def top_p_sample(logits, top_p, temperature=1.0):
    ordered = torch.argsort(logits, descending=True, stable=True)
    probabilities = torch.softmax(logits[ordered] / temperature, dim=0)
    count = min(ordered.numel(), int((probabilities.cumsum(0) < top_p).sum()) + 1)
    return int(ordered[torch.randint(count, (1,))].item())
""",
        )

    def test_reference_keeps_all_candidates_when_top_p_is_one(self):
        namespace = {}
        exec(self.reference, namespace)
        # Inspect our reference without prescribing a student's sampling algorithm.
        with patch("torch.multinomial", return_value=torch.tensor([2])) as draw:
            token = namespace["sample_token"](torch.tensor([0.0, -40.0, -41.0]), top_p=1.0)
        self.assertEqual(token, 2)
        self.assertIsInstance(token, int)
        probabilities = draw.call_args.args[0]
        self.assertEqual(probabilities.numel(), 3)
        self.assertTrue((probabilities > 0).all())
        self.assertAlmostEqual(probabilities.sum().item(), 1.0)


if __name__ == "__main__":
    unittest.main()
