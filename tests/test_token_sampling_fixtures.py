import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

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
        )
        self.assertEqual(result["status"], "failed", result)

    def test_fixture_rejects_applying_top_p_before_top_k(self):
        self.assert_fixture_rejects(
            "combined top-p uses the renormalized top-k distribution",
            """
def sample_token(logits, top_k=None, top_p=1.0, temperature=1.0):
    values = np.asarray(logits, dtype=float)
    ordered = np.argsort(-values, kind="stable")
    weights = np.exp((values[ordered] - values.max()) / temperature)
    probabilities = weights / weights.sum()
    count = min(len(ordered), np.searchsorted(np.cumsum(probabilities), top_p) + 1)
    ordered = ordered[:count]
    probabilities = probabilities[:count]
    if top_k:
        ordered = ordered[:top_k]
        probabilities = probabilities[:top_k]
    return int(np.random.choice(ordered, p=probabilities / probabilities.sum()))
""",
        )

    def test_fixture_rejects_uniform_top_k_sampling(self):
        self.assert_fixture_rejects(
            "top-k samples proportionally instead of uniformly or greedily",
            """
def top_k_sample(logits, top_k, temperature=1.0):
    ordered = np.argsort(-np.asarray(logits), kind="stable")[:top_k]
    return int(np.random.choice(ordered))
""",
        )

    def test_fixture_rejects_uniform_top_p_sampling(self):
        self.assert_fixture_rejects(
            "top-p-only sampling follows conditional probabilities",
            """
def top_p_sample(logits, top_p, temperature=1.0):
    values = np.asarray(logits, dtype=float)
    ordered = np.argsort(-values, kind="stable")
    weights = np.exp((values[ordered] - values.max()) / temperature)
    count = np.searchsorted(np.cumsum(weights / weights.sum()), top_p) + 1
    return int(np.random.choice(ordered[:count]))
""",
        )

    def test_reference_keeps_all_candidates_when_top_p_is_one(self):
        namespace = {}
        exec(self.reference, namespace)
        # Inspect our reference sampler without requiring students to use choice.
        with patch("numpy.random.choice", return_value=np.int64(2)) as draw:
            token = namespace["sample_token"]([0.0, -40.0, -41.0], top_p=1.0)
        self.assertEqual(token, 2)
        self.assertIsInstance(token, int)
        np.testing.assert_array_equal(draw.call_args.args[0], [0, 1, 2])
        self.assertTrue((draw.call_args.kwargs["p"] > 0).all())


if __name__ == "__main__":
    unittest.main()
