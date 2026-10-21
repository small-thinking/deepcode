"""Verify the two API workouts through the real runner and their visual arithmetic."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

import numpy as np

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ("490-numpy-classifier-workout", "491-torch-sequence-workout")

# A DOM stub tests the offline computation, not layout or browser integration.
DEMO_HARNESS = r"""
const fs = require('node:fs'), vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    value: '', checked: false, textContent: '', innerHTML: '', disabled: false,
    addEventListener() {}, getBoundingClientRect() { return {height: 900}; }
  });
  return elements.get(id);
}
const document = {getElementById: element, querySelector: () => element('root'),
  querySelectorAll: () => [], documentElement: {dataset: {}, style: {setProperty() {}}}};
const window = {addEventListener() {}};
const parent = {postMessage() {}};
const context = vm.createContext({document, window, parent,
  ResizeObserver: class {observe() {}}});
for (const [key,value] of Object.entries(input.controls)) element(key).value = String(value);
element('constant').checked = !!input.constant;
const html = fs.readFileSync(input.path, 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(script, context);
const results = vm.runInContext(`(() => {
  const data = calculate();
  const scenes = names.map((_,i) => {stage=i; render(); return makeScene(data)});
  return JSON.stringify({data, scenes});
})()`, context);
process.stdout.write(results);
"""


def load(folder):
    path = ROOT / "problems" / folder
    return path, json.loads((path / "problem.json").read_text()), json.loads((path / "tests.json").read_text())


class ArrayWorkoutFixturesTest(unittest.TestCase):
    def test_solutions_pass_real_runner_and_starters_are_unfinished(self):
        for folder in FOLDERS:
            with self.subTest(folder=folder):
                path, problem, tests = load(folder)
                request = dict(problem=problem, tests=tests, environment=problem["environment"])
                result = evaluate_submission(EvaluationRequest(code=(path / "solution.py").read_text(), **request))
                self.assertEqual(result["passed"], len(tests), result)
                first = evaluate_submission(EvaluationRequest(
                    code=problem["starter_code"], problem=problem, tests=tests[:1],
                    environment=problem["environment"],
                ))
                self.assertEqual(first["passed"], 0, first)

    def test_pooling_name_accepts_legacy_drafts_without_hiding_new_helper_errors(self):
        path, problem, tests = load(FOLDERS[1])
        code = (path / "solution.py").read_text()
        pooling_tests = [case for case in tests if case["name"].startswith("[Part 4]")]
        legacy = code.replace("masked_mean = masked_mean_pooling\n", "")
        legacy = legacy.replace("masked_mean_pooling", "masked_mean")
        broken_new = code + "\ndef masked_mean_pooling(x, mask):\n    return None\n"
        for variant, expected in ((legacy, len(pooling_tests)), (broken_new, 0)):
            with self.subTest(legacy=variant == legacy):
                result = evaluate_submission(EvaluationRequest(
                    code=variant, problem=problem, tests=pooling_tests,
                    environment=problem["environment"],
                ))
                self.assertEqual(result["passed"], expected, result)

    def test_catalog_declares_scoped_coding_demos(self):
        store = ProblemStore(ROOT / "problems")
        for folder in FOLDERS:
            path, metadata, _ = load(folder)
            problem = store.get_problem(metadata["slug"])
            self.assertEqual(problem["companies"], ["General"])
            self.assertIn("api-workout", problem["tags"])
            demo, = problem["interactive_demos"]
            self.assertEqual(demo["section"], "interactive_demo")
            self.assertEqual(demo["presentation"]["theme"], "sync")
            html = (path / demo["path"]).read_text()
            self.assertNotRegex(html, r"[\u4e00-\u9fff]")
            self.assertNotRegex(html, r"(?:https?://|fetch\(|localStorage|sessionStorage)")

    def demo(self, folder, controls, constant=False):
        if not shutil.which("node"):
            self.skipTest("Node.js is required to check the offline demo arithmetic")
        path = ROOT / "problems" / folder / "assets" / "array-workout.html"
        result = subprocess.run(["node", "-e", DEMO_HARNESS], input=json.dumps({
            "path": str(path), "controls": controls, "constant": constant,
        }), text=True, capture_output=True, timeout=15, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["scenes"]), 13)
        for scene in payload["scenes"]:
            self.assertIn('<svg ', scene["figure"])
            self.assertNotRegex(scene["figure"] + scene["equation"], r"NaN|Infinity|undefined")
        return payload["data"]

    def test_numpy_demo_matches_reference_at_control_boundaries(self):
        path, _, _ = load(FOLDERS[0])
        scope = {}
        exec((path / "solution.py").read_text(), scope)
        for feature, constant, rate in ((1, False, .2), (-2, True, .05), (6, False, .8)):
            with self.subTest(feature=feature, constant=constant, rate=rate):
                data = self.demo(FOLDERS[0], dict(feature=feature, rate=rate, row=2, column=1), constant)
                x = np.asarray(data["x"])
                mean, scale = scope["fit_standardizer"](x)
                np.testing.assert_allclose(data["mu"], mean[0])
                np.testing.assert_allclose(data["scale"], scale[0])
                z = scope["standardize"](x, mean, scale)
                np.testing.assert_allclose(data["z"], z)
                w, b, y = np.array(data["w"]), np.array(data["b"]), np.array(data["y"])
                logits = scope["linear_logits"](z, w, b)
                p = scope["softmax"](logits)
                np.testing.assert_allclose(data["logits"], logits)
                np.testing.assert_allclose(data["p"], p)
                self.assertAlmostEqual(data["loss"], scope["cross_entropy"](p, y))
                dw, db = scope["linear_gradients"](z, p, y)
                np.testing.assert_allclose(data["dw"], dw)
                np.testing.assert_allclose(data["db"], db, atol=1e-15)
                w1, b1 = scope["sgd_step"](w, b, dw, db, rate)
                np.testing.assert_allclose(data["updated"], w1)
                np.testing.assert_allclose(data["updatedB"], b1)
                metrics = scope["classification_metrics"](p, y, 1)
                np.testing.assert_array_equal(data["conf"], metrics["confusion"])
                self.assertAlmostEqual(data["accuracy"], metrics["accuracy"])
                ew, eb = scope["train_epoch"](z, y, w, b, rate, 2, 7)
                np.testing.assert_allclose(data["epoch"][-1]["w"], ew)
                np.testing.assert_allclose(data["epoch"][-1]["b"], eb)

    def test_torch_demo_matches_autograd_and_padding_invariance(self):
        import torch
        path, _, _ = load(FOLDERS[1])
        scope = {}
        exec((path / "solution.py").read_text(), scope)
        for length, padding, temperature in ((2, 9, 1), (1, -10, .25), (3, 10, 3)):
            with self.subTest(length=length, padding=padding, temperature=temperature):
                controls = dict(length=length, padding=padding, temperature=temperature, row=1, column=1)
                data = self.demo(FOLDERS[1], controls)
                x = torch.tensor(data["x"], dtype=torch.float64)
                lengths = torch.tensor(data["lengths"])
                mask = scope["valid_token_mask"](lengths, 3)
                np.testing.assert_array_equal(data["mask"], mask.numpy())
                pooled = scope["masked_mean_pooling"](x, mask)
                np.testing.assert_allclose(data["pooled"], pooled.numpy())
                model = torch.nn.Linear(2, 2, dtype=torch.float64)
                with torch.no_grad():
                    model.weight.copy_(torch.tensor(data["weight"], dtype=torch.float64))
                    model.bias.copy_(torch.tensor(data["bias"], dtype=torch.float64))
                logits = model(pooled)
                np.testing.assert_allclose(data["logits"], logits.detach().numpy())
                p = scope["class_probabilities"](logits, temperature)
                np.testing.assert_allclose(data["p"], p.detach().numpy())
                labels = torch.tensor(data["labels"])
                result_loss = scope["classification_loss"](logits, labels)
                self.assertAlmostEqual(data["loss"], result_loss.item())
                result_loss.backward()
                np.testing.assert_allclose(data["dw"], model.weight.grad.numpy(), atol=1e-15)
                np.testing.assert_allclose(data["db"], model.bias.grad.numpy(), atol=1e-15)
                np.testing.assert_allclose(data["nextW"], (model.weight - .2 * model.weight.grad).detach().numpy())
                np.testing.assert_allclose(data["nextB"], (model.bias - .2 * model.bias.grad).detach().numpy())
                other = self.demo(FOLDERS[1], {**controls, "padding": -padding})
                np.testing.assert_allclose(data["pooled"], other["pooled"])
                np.testing.assert_allclose(data["logits"], other["logits"])


if __name__ == "__main__":
    unittest.main()
