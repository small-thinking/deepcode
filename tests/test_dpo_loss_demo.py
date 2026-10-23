"""Check the embedded DPO explorer against independent PyTorch autograd."""
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
SLUG = "dpo-loss"
DEMO = ROOT / "problems/525-dpo-loss/assets/dpo-loss-lab.html"
CORE = DEMO.read_text().split("// BEGIN DPO MATH", 1)[1].split("// END DPO MATH", 1)[0]


def run_math(script):
    result = subprocess.run(["node", "-e", CORE + script], check=True,
                            capture_output=True, text=True)
    return json.loads(result.stdout)


class DpoLossDemoTest(unittest.TestCase):
    def test_demo_loads_through_supported_coding_mount(self):
        problem = ProblemStore(ROOT / "problems").get_problem(SLUG)
        demo = problem["interactive_demos"][0]
        self.assertEqual(demo["section"], "interactive_demo")
        self.assertEqual(demo["presentation"]["theme"], "sync")
        self.assertEqual(demo["presentation"]["height"], "content")
        self.assertEqual(resolve_problem_demo(
            f"/problem-demos/{SLUG}/{demo['path']}", ROOT / "problems"
        ), DEMO.resolve())

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_likelihood_loss_and_gradient_paths_match_autograd(self):
        rows = run_math("""
const rows=[];
for(const policy of [-10000,-6,-1,0,2,6,10000])
  for(const reference of [-10000,-3,0,3,10000])
    for(const beta of [.05,.5,1,10])
      for(const freeze of [false,true])
        rows.push({policy,reference,beta,freeze,...dpoValues(policy,reference,beta,freeze)});
console.log(JSON.stringify(rows));
""")
        for row in rows:
            with self.subTest(policy=row["policy"], reference=row["reference"],
                              beta=row["beta"], freeze=row["freeze"]):
                pc, pr, rc, rr = [torch.tensor(float(x), dtype=torch.float64,
                                             requires_grad=True) for x in (
                    row["policy"] / 2, -row["policy"] / 2,
                    row["reference"] / 2, -row["reference"] / 2,
                )]
                reference = rc - rr
                if row["freeze"]:
                    reference = reference.detach()
                z = row["beta"] * (pc - pr - reference)
                loss = -torch.nn.functional.logsigmoid(z)
                gradients = torch.autograd.grad(loss, (pc, pr, rc, rr), allow_unused=True)
                self.assertTrue(math.isfinite(row["loss"]))
                self.assertAlmostEqual(row["loss"], loss.item(), places=11)
                self.assertAlmostEqual(row["probability"], torch.sigmoid(z).item(), places=12)
                self.assertAlmostEqual(row["logit"], z.item(), places=11)
                for key, gradient in zip(("policyChosen", "policyRejected",
                                          "referenceChosen", "referenceRejected"), gradients):
                    expected = 0 if gradient is None else gradient.item()
                    self.assertAlmostEqual(row[key], expected, places=12)

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_scenarios_distinguish_absolute_order_from_relative_improvement(self):
        rows = run_math("""
console.log(JSON.stringify(Object.entries(presets).map(([name,p])=>
  ({name,...p,...dpoValues(p.policy,p.reference,p.beta)}))));
""")
        by_name = {row["name"]: row for row in rows}
        self.assertEqual(by_name["equal"]["probability"], .5)
        self.assertAlmostEqual(by_name["equal"]["loss"], math.log(2))
        self.assertLess(by_name["improved"]["policy"], 0)
        self.assertGreater(by_name["improved"]["margin"], 0)
        self.assertGreater(by_name["behind"]["policy"], 0)
        self.assertLess(by_name["behind"]["margin"], 0)

    @unittest.skipUnless(shutil.which("node"), "Node is required for demo arithmetic")
    def test_beta_changes_slope_but_not_loss_at_equal_gaps(self):
        rows = run_math("""
console.log(JSON.stringify([.05,.5,1,5,10].map(beta=>({beta,
  equal:dpoValues(2,2,beta),positive:dpoValues(3,1,beta),negative:dpoValues(1,3,beta)}))));
""")
        for row in rows:
            self.assertAlmostEqual(row["equal"]["loss"], math.log(2))
            self.assertAlmostEqual(row["equal"]["gradient"], -row["beta"] / 2)
        self.assertGreater(rows[-1]["positive"]["probability"], rows[1]["positive"]["probability"])
        self.assertLess(abs(rows[-1]["positive"]["gradient"]), abs(rows[1]["positive"]["gradient"]))
        self.assertGreater(rows[-1]["negative"]["loss"], rows[1]["negative"]["loss"])


if __name__ == "__main__":
    unittest.main()
