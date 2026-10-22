"""Validate the reward-model exercise through its runner and independent SGD checks."""
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/523-bradley-terry-reward-model-training"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/bradley_terry_reward_model.py").read_text()


class BradleyTerryRewardModelContractTest(unittest.TestCase):
    def test_reference_passes_real_evaluator(self):
        problem = ProblemStore(ROOT / "problems").get_problem(PROBLEM["slug"])
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_checks_accept_bias_options_and_initializations(self):
        for use_bias in (False, True):
            for initialization in ("", "nn.init.zeros_(self.head.weight)",
                                   "nn.init.constant_(self.head.weight, -0.4)"):
                constructor = f"self.head = nn.Linear(input_dim, 1, bias={use_bias})"
                if use_bias:
                    constructor += "\n        nn.init.constant_(self.head.bias, 0.7)"
                if initialization:
                    constructor += "\n        " + initialization
                code = REFERENCE.replace("self.head = nn.Linear(input_dim, 1)", constructor)
                for check in CHECKS:
                    with self.subTest(bias=use_bias, initialization=initialization,
                                      check=check["name"]):
                        namespace = {}
                        exec(compile(code, "bias and initialization variant", "exec"), namespace)
                        exec(check["test"], namespace)

    def test_checks_reject_common_loss_and_training_mistakes(self):
        mutations = (
            ("reversed preference", "chosen_scores - rejected_scores",
             "rejected_scores - chosen_scores", 1),
            ("lost singleton batch dimension", ".squeeze(-1)", ".squeeze()", 0),
            ("accumulated gradients", "optimizer.zero_grad(set_to_none=True)", "pass", 4),
            ("detached rejected branch", "bt_loss(model(c), model(r))",
             "bt_loss(model(c), model(r).detach())", 2),
            ("dropped final partial batch", "range(0, len(pairs), batch_size)",
             "range(0, len(pairs) - batch_size + 1, batch_size)", 4),
            ("logged last batch instead of epoch evaluation", "loss_history.append(evaluate_loss())",
             "loss_history.append(loss.item())", 4),
            ("incorrect shared bias update", "optimizer.step()",
             "optimizer.step()\n            with torch.no_grad():\n                model.head.bias.add_(lr)", 2),
        )
        for name, old, new, check_index in mutations:
            with self.subTest(name=name):
                self.assertIn(old, REFERENCE)
                namespace = {}
                exec(compile(REFERENCE.replace(old, new), name, "exec"), namespace)
                with self.assertRaises((AssertionError, RuntimeError)):
                    exec(CHECKS[check_index]["test"], namespace)


if __name__ == "__main__":
    unittest.main()
