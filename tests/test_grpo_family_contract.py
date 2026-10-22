"""Test the curriculum through the actual evaluator and reject specific math mistakes."""
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/522-grpo-family-objectives"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/grpo_family.py").read_text()


class GrpoFamilyContractTest(unittest.TestCase):
    def test_reference_passes_real_evaluator(self):
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE, problem=PROBLEM, tests=CHECKS,
            environment=PROBLEM["environment"],
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_buffer_length_keyword_and_legacy_positional_signature(self):
        namespace = {}
        exec(REFERENCE, namespace)
        torch = namespace["torch"]
        shaped = namespace["soft_overlong_rewards"](
            rewards=torch.ones((1, 4)), lengths=torch.tensor([[6, 8, 10, 11]]),
            max_length=10, buffer_length=4,
        )
        torch.testing.assert_close(shaped, torch.tensor([[1., .5, 0., 0.]]))
        # Existing saved solutions keep working with positional visible checks.
        legacy = REFERENCE.replace("buffer_length", "cache_length")
        result = evaluate_submission(EvaluationRequest(
            code=legacy, problem=PROBLEM, tests=CHECKS[10:11],
            environment=PROBLEM["environment"],
        ))
        self.assertEqual(result["passed"], 1, result)

    def test_specific_wrong_algorithms_fail_hand_computed_checks(self):
        # Values and gradients in tests.json are independent, hand-computed oracles.
        mutations = (
            ("sample std", "correction=0", "correction=1", 0),
            ("retain std in Dr", 'if variant == "dr_grpo":\n        return centered',
             'if variant == "dr_grpo":\n        return centered / (rewards.std(dim=-1, correction=0, keepdim=True) + eps)', 2),
            ("padded width instead of C", "/ max_length).mean()", "/ logp.shape[-1]).mean()", 2),
            ("group means instead of batch tokens", "return -gain.sum() / lengths.sum()",
             "return -(gain.sum(-1) / lengths.sum(-1)).mean()", 3),
            ("clamp without minimum", "torch.minimum(ratio * advantages, clipped * advantages)",
             "clipped * advantages", 4),
            ("symmetric upper bound", "1 + clip_high", "1 + clip_low", 5),
            ("arithmetic GSPO ratio", "(delta.sum(dim=-1) / lengths).exp()",
             "(delta.exp() * response_mask).sum(dim=-1) / lengths", 6),
            ("raw sequence ratio", "(delta.sum(dim=-1) / lengths).exp()",
             "delta.sum(dim=-1).exp()", 6),
            ("detach current", "delta = (logp - old_logp.detach())",
             "delta = (logp.detach() - old_logp.detach())", 1),
            ("old gradients", "logp - old_logp.detach()", "logp - old_logp", 1),
            ("one-shot length penalty", ").clamp(-1, 0)", ").lt(0).to(rewards.dtype).neg()", 10),
        )
        for name, old, new, index in mutations:
            with self.subTest(name=name):
                self.assertIn(old, REFERENCE)
                namespace = {}
                exec(compile(REFERENCE.replace(old, new), name, "exec"), namespace)
                with self.assertRaises((AssertionError, RuntimeError)):
                    exec(CHECKS[index]["test"], namespace)

    def test_curriculum_is_discoverable_and_not_company_attributed(self):
        store = ProblemStore(ROOT / "problems")
        problem = store.get_problem(PROBLEM["slug"])
        self.assertEqual(problem["companies"], ["General"])
        self.assertNotIn("interview_frequency", problem)
        self.assertEqual(len(problem["tests"]), len(CHECKS))
        self.assertIn("grpo-family-objectives", store.get_problem("grpo-response-logprob-training")["prompt"])
        self.assertIn("grpo-family-objectives", store.get_problem("grpo-training-loop-debugging")["prompt"])


if __name__ == "__main__":
    unittest.main()
