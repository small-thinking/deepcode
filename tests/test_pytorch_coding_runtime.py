import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.evaluators.ml_coding import _pytorch_resource_limiter, _resource_limiter
from deepcode.problem_store import ProblemStore


class PytorchCodingRuntimeTest(unittest.TestCase):
    def evaluate(self, code, timeout=10):
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem={"evaluation": {"type": "ml_coding"}},
            tests=[{"name": "torch check", "test": "print('ok')", "expected_output": "ok"}],
            environment={"runtime": "pytorch", "timeout_seconds": timeout},
        ))

    def test_runs_cpu_forward_backward_and_optimizer_step(self):
        result = self.evaluate(
            "import os\n"
            "import torch\n"
            "assert os.environ['DEEPCODE_TORCH_DEVICE'] == 'cpu'\n"
            "assert torch.get_num_threads() == 1\n"
            "layer = torch.nn.Linear(2, 1, bias=False, device='cpu')\n"
            "torch.nn.init.zeros_(layer.weight)\n"
            "optimizer = torch.optim.SGD(layer.parameters(), lr=0.1)\n"
            "x = torch.tensor([[1., 2.]])\n"
            "loss = (layer(x) - 1).square().mean()\n"
            "loss.backward()\n"
            "assert torch.allclose(layer.weight.grad, torch.tensor([[-2., -4.]]))\n"
            "optimizer.step()\n"
            "assert torch.allclose(layer(x), torch.tensor([[1.]]))\n"
        )
        self.assertEqual(result["status"], "passed", result)

    def test_wall_timeout_still_stops_pytorch_runtime(self):
        result = self.evaluate("while True:\n    pass", timeout=0.2)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Timed out after 0.2 seconds", result["results"][0]["actual_output"])

    def test_rejects_unknown_runtime(self):
        with self.assertRaisesRegex(ValueError, "Unsupported ML coding runtime"):
            evaluate_submission(EvaluationRequest(
                code="", problem={}, tests=[], environment={"runtime": "unknown"}
            ))

    def test_problem_store_validates_runtime_metadata(self):
        for runtime in ("python", "pytorch", "unknown", [], None):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / "tiny-torch"
                directory.mkdir()
                problem = {
                    "id": "1", "title": "Tiny", "category": "ML Coding", "difficulty": "easy",
                    "prompt": "Return a tensor", "starter_code": "", "example": {},
                    "environment": {"runtime": runtime, "timeout_seconds": 10},
                }
                (directory / "problem.json").write_text(json.dumps(problem))
                store = ProblemStore(Path(tmp))
                if runtime in ("python", "pytorch"):
                    self.assertEqual(store.get_problem("tiny-torch")["environment"]["runtime"], runtime)
                else:
                    with self.assertRaisesRegex(ValueError, "environment.runtime"):
                        store.get_problem("tiny-torch")

    @unittest.skipUnless(os.name == "posix", "POSIX resource limits")
    def test_pytorch_limits_allow_import_and_follow_configured_timeout(self):
        import resource

        with patch("resource.setrlimit") as set_limit:
            _pytorch_resource_limiter(10.5)()
        set_limit.assert_any_call(resource.RLIMIT_CPU, (12, 12))
        set_limit.assert_any_call(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
        set_limit.assert_any_call(resource.RLIMIT_CORE, (0, 0))
        if hasattr(resource, "RLIMIT_AS"):
            self.assertNotIn(resource.RLIMIT_AS, [call.args[0] for call in set_limit.call_args_list])

    @unittest.skipUnless(os.name == "posix", "POSIX resource limits")
    def test_default_runtime_keeps_existing_cpu_and_memory_limits(self):
        import resource

        with patch("resource.setrlimit") as set_limit:
            _resource_limiter()()
        set_limit.assert_any_call(resource.RLIMIT_CPU, (3, 3))
        if hasattr(resource, "RLIMIT_AS"):
            set_limit.assert_any_call(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)


if __name__ == "__main__":
    unittest.main()
