"""Check the embedded lesson's math independently of its SVG rendering."""
import json
import math
from pathlib import Path
import shutil
import subprocess
import unittest

import torch

from deepcode.problem_store import ProblemStore
from deepcode.server import resolve_problem_demo

ROOT = Path(__file__).resolve().parents[1]
SLUG = "bradley-terry-reward-model-training"
DEMO_PATH = ROOT / "problems/523-bradley-terry-reward-model-training/assets/bt-loss-lab.html"
SOURCE = DEMO_PATH.read_text(encoding="utf-8")
CORE = SOURCE.split("// BEGIN BT MATH", 1)[1].split("// END BT MATH", 1)[0]


class BTLossDemoTest(unittest.TestCase):
    def test_demo_uses_the_supported_coding_mount_and_scoped_asset(self):
        problem = ProblemStore(ROOT / "problems").get_problem(SLUG)
        demo = problem["interactive_demos"][0]
        self.assertEqual(demo["section"], "interactive_demo")
        self.assertEqual(demo["presentation"]["theme"], "sync")
        self.assertEqual(demo["presentation"]["height"], "content")
        self.assertEqual(resolve_problem_demo(
            f"/problem-demos/{SLUG}/{demo['path']}", ROOT / "problems"
        ), DEMO_PATH.resolve())

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_pair_values_and_score_gradients_match_pytorch_including_extremes(self):
        script = CORE + """
const rows=[];
for(const gap of [-20000,-6,-1,0,1,6,20000]) {
  for(const bias of [-3,0,3]) rows.push({gap,bias,...pairValues(gap,bias)});
}
console.log(JSON.stringify(rows));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        for row in json.loads(result.stdout):
            with self.subTest(gap=row["gap"], bias=row["bias"]):
                c = torch.tensor(row["chosen"], dtype=torch.float64, requires_grad=True)
                r = torch.tensor(row["rejected"], dtype=torch.float64, requires_grad=True)
                loss = torch.logaddexp(torch.zeros((), dtype=torch.float64), r - c)
                gc, gr = torch.autograd.grad(loss, (c, r))
                self.assertTrue(math.isfinite(row["loss"]))
                self.assertAlmostEqual(row["chosen"] - row["rejected"], row["gap"])
                self.assertAlmostEqual(row["loss"], loss.item(), places=12)
                self.assertAlmostEqual(row["logProbability"], -loss.item(), places=12)
                self.assertAlmostEqual(row["probability"], torch.sigmoid(c-r).item(), places=12)
                self.assertAlmostEqual(row["gradient"], gc.item(), places=12)
                self.assertAlmostEqual(-row["gradient"], gr.item(), places=12)

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_training_scenarios_match_independent_autograd_updates(self):
        script = CORE + """
const rows=[];
for(const scenario of Object.keys(scenarios)) {
  for(const initial of [-4,0,4]) {
    let w=initial;
    for(let i=0;i<400;i++) w=sgdStep(w,.1,scenario);
    rows.push({scenario,initial,w,...datasetValues(w,.7,scenario)});
  }
}
console.log(JSON.stringify(rows));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        fractions = {"separable": 1, "mixed": .75, "balanced": .5, "identical": 1}
        for row in json.loads(result.stdout):
            with self.subTest(scenario=row["scenario"], initial=row["initial"]):
                a, b = .5, .5 if row["scenario"] == "identical" else -.5
                n_a = int(4 * fractions[row["scenario"]])
                chosen = torch.tensor([a] * n_a + [b] * (4-n_a), dtype=torch.float64)
                rejected = torch.tensor([b] * n_a + [a] * (4-n_a), dtype=torch.float64)
                w = torch.tensor(float(row["initial"]), dtype=torch.float64, requires_grad=True)
                bias = torch.tensor(.7, dtype=torch.float64, requires_grad=True)
                for _ in range(400):
                    c, r = chosen * w + bias, rejected * w + bias
                    loss = torch.logaddexp(torch.zeros_like(c), r-c).mean()
                    gw, gb = torch.autograd.grad(loss, (w, bias))
                    self.assertAlmostEqual(gb.item(), 0, places=12)
                    w = (w - .1 * gw).detach().requires_grad_()
                c, r = chosen * w + bias, rejected * w + bias
                expected_loss = torch.logaddexp(torch.zeros_like(c), r-c).mean()
                self.assertAlmostEqual(row["w"], w.item(), places=11)
                self.assertAlmostEqual(row["loss"], expected_loss.item(), places=11)
                self.assertAlmostEqual(row["a"], a*w.item()+.7, places=11)
                self.assertAlmostEqual(row["b"], b*w.item()+.7, places=11)
                if row["scenario"] == "identical":
                    self.assertEqual(row["w"], row["initial"])
                    self.assertAlmostEqual(row["loss"], math.log(2), places=12)

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_conflict_optima_and_shared_bias_invariance(self):
        script = CORE + """
const rows=[];
for(const [scenario,w] of [['mixed',Math.log(3)],['balanced',0]]) {
  rows.push({scenario,w,low:datasetValues(w,-3,scenario),high:datasetValues(w,3,scenario)});
}
console.log(JSON.stringify(rows));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        for row in json.loads(result.stdout):
            with self.subTest(scenario=row["scenario"]):
                q = .75 if row["scenario"] == "mixed" else .5
                self.assertAlmostEqual(row["low"]["probability"], q, places=12)
                self.assertAlmostEqual(row["low"]["gradient"], 0, places=12)
                self.assertAlmostEqual(row["low"]["loss"], -q*math.log(q)-(1-q)*math.log(1-q), places=12)
                for key in ("probability", "loss", "gradient"):
                    self.assertEqual(row["low"][key], row["high"][key])


if __name__ == "__main__":
    unittest.main()
