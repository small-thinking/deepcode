import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBLEM_DIR = ROOT / "problems" / "402-linear-logistic-regression-training"


class RegressionTrainingDemoTests(unittest.TestCase):
    def test_demo_is_mounted_with_the_ml_coding_contract(self):
        problem = json.loads((PROBLEM_DIR / "problem.json").read_text(encoding="utf-8"))
        demo = problem["interactive_demos"][0]

        self.assertEqual(demo["section"], "interactive_demo")
        self.assertEqual(demo["presentation"]["theme"], "sync")
        self.assertEqual(demo["presentation"]["height"], "content")
        self.assertTrue((PROBLEM_DIR / demo["path"]).is_file())

    def test_demo_keeps_math_code_and_runtime_contract_visible(self):
        problem = json.loads((PROBLEM_DIR / "problem.json").read_text(encoding="utf-8"))
        demo_path = PROBLEM_DIR / problem["interactive_demos"][0]["path"]
        content = demo_path.read_text(encoding="utf-8")

        for required in (
            "One loop. Two models.",
            'data-model="linear"',
            'data-model="logistic"',
            'id="learning-rate"',
            'id="feature-scale"',
            'id="l2"',
            "np.logaddexp(0.0, z) - y * z",
            "dz = 2.0 * (z - y)",
            "dz = stable_sigmoid(z) - y",
            "grad_w = X.T @ dz / N + l2 * w",
            "grad_b = np.mean(dz)",
            "Bias is not regularized",
            "Toy data",
            "type: 'deepcode:interactive-demo-ready'",
            "type: 'deepcode:interactive-demo-height'",
            "event.source !== window.parent",
        ):
            with self.subTest(required=required):
                self.assertIn(required, content)

        self.assertNotIn("https://", content)
        self.assertNotIn("localStorage", content)


if __name__ == "__main__":
    unittest.main()
