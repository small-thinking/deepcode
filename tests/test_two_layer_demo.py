"""Independent numerical checks for the browser walkthrough's actual math."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

import numpy as np


DEMO = Path(__file__).resolve().parents[1] / "problems/110-two-layer-numpy-network/assets/backprop-walkthrough.html"


class TwoLayerDemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if cls.node is None:
            raise unittest.SkipTest("Node is required to execute the browser demo math")
        html = DEMO.read_text()
        cls.math = html.split("// BEGIN MATH", 1)[1].split("// END MATH", 1)[0]

    def compute(self, x=1, label=0, repeats=1, lr=0.1):
        script = self.math + "\nconsole.log(JSON.stringify(compute(" + json.dumps([x, label, repeats, lr])[1:-1] + ")));"
        result = subprocess.run([self.node, "-e", script], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    @staticmethod
    def numpy_loss(x, y, parameters):
        hidden = np.maximum(x @ parameters["W1"] + parameters["b1"], 0)
        logits = hidden @ parameters["W2"] + parameters["b2"]
        shifted = logits - logits.max(axis=1, keepdims=True)
        return np.mean(np.log(np.exp(shifted).sum(axis=1)) - shifted[np.arange(len(y)), y])

    def test_gradients_match_independent_finite_differences(self):
        # Exercise both sides of the first hidden unit's ReLU threshold,
        # staying away from the nondifferentiable point itself.
        for input_value, label in [(1.0, 0), (-0.7, 2), (0.3, 1)]:
            with self.subTest(x=input_value, label=label):
                result = self.compute(input_value, label)
                x, y = np.array(result["X"]), np.array(result["y"])
                parameters = {key: np.array(value, dtype=float) for key, value in result["parameters"].items()}
                self.assertAlmostEqual(result["loss"], self.numpy_loss(x, y, parameters), places=12)
                for key, value in parameters.items():
                    numerical = np.zeros_like(value)
                    for index in np.ndindex(value.shape):
                        old = value[index]
                        value[index] = old + 1e-6
                        upper = self.numpy_loss(x, y, parameters)
                        value[index] = old - 1e-6
                        lower = self.numpy_loss(x, y, parameters)
                        value[index] = old
                        numerical[index] = (upper - lower) / 2e-6
                    np.testing.assert_allclose(result["gradients"][key], numerical, atol=1e-8, rtol=1e-6, err_msg=key)

    def test_repeating_batch_preserves_mean_loss_and_parameter_gradients(self):
        original = self.compute()
        repeated = self.compute(repeats=4)
        self.assertEqual(len(repeated["X"]), 4 * len(original["X"]))
        self.assertAlmostEqual(original["loss"], repeated["loss"], places=12)
        for key in original["gradients"]:
            np.testing.assert_allclose(original["gradients"][key], repeated["gradients"][key], atol=1e-12)
        np.testing.assert_allclose(np.array(repeated["G"])[:3] * 4, original["G"], atol=1e-12)

    def test_sgd_updates_all_parameters_and_recomputes_loss(self):
        for learning_rate in [0, 0.1, 0.5]:
            with self.subTest(lr=learning_rate):
                result = self.compute(lr=learning_rate)
                updated = {key: np.array(value) for key, value in result["updatedParameters"].items()}
                for key, initial in result["parameters"].items():
                    expected = np.array(initial) - learning_rate * np.array(result["gradients"][key])
                    np.testing.assert_allclose(updated[key], expected, atol=1e-12)
                expected_loss = self.numpy_loss(np.array(result["X"]), np.array(result["y"]), updated)
                self.assertAlmostEqual(result["updatedLoss"], expected_loss, places=12)
                self.assertLessEqual(result["updatedLoss"], result["loss"] + 1e-12)


if __name__ == "__main__":
    unittest.main()
