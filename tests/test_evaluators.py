import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from deepcode.evaluators import (
    EvaluationRequest,
    UnsupportedEvaluatorError,
    evaluate_submission,
    get_evaluator,
    stream_evaluation_events,
)
from deepcode.evaluators import ml_torch_modeling


class EvaluatorRegistryTest(unittest.TestCase):
    def test_dispatches_ml_coding_evaluator(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def add_one(x):\n    return x + 1\n",
                problem={"evaluation": {"type": "ml_coding"}},
                tests=[{"name": "basic", "test": "print(add_one(4))", "expected_output": "5"}],
                environment={"timeout_seconds": 2, "comparator": "exact"},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 1)

    def test_rejects_unknown_evaluator(self):
        with self.assertRaises(UnsupportedEvaluatorError):
            get_evaluator("not_registered")

    def test_dispatches_ml_modeling_assertion_checks(self):
        self.assertEqual(get_evaluator("ml_modeling").name, "ml_modeling")

        result = evaluate_submission(
            EvaluationRequest(
                code="def square(x):\n    return x * x\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {
                        "name": "square behavior",
                        "input": "x = 4",
                        "test": "assert square(4) == 16\nprint('ok')",
                    }
                ],
                environment={"timeout_seconds": 2},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["results"][0]["expected_output"], "All assertions pass")
        self.assertEqual(result["results"][0]["actual_output"], "ok")

    def test_dispatches_ml_torch_modeling_assertion_checks(self):
        self.assertEqual(get_evaluator("ml_torch_modeling").name, "ml_torch_modeling")

        result = evaluate_submission(
            EvaluationRequest(
                code=(
                    "import torch\n\n"
                    "def double_tensor(values):\n"
                    "    return torch.tensor(values, dtype=torch.float32) * 2\n"
                ),
                problem={"evaluation": {"type": "ml_torch_modeling"}},
                tests=[
                    {
                        "name": "tiny torch tensor behavior",
                        "input": "values = [1.0, -2.0, 0.5]",
                        "test": (
                            "import torch\n"
                            "actual = double_tensor([1.0, -2.0, 0.5])\n"
                            "expected = torch.tensor([2.0, -4.0, 1.0])\n"
                            "assert torch.allclose(actual, expected)\n"
                            "print('ok')\n"
                        ),
                    }
                ],
                environment={"timeout_seconds": 10, "packages": ["torch"]},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["results"][0]["actual_output"], "ok")

    def test_ml_torch_lab_runs_hidden_harness_after_visible_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            results_dir = root / "eval-results"
            data_dir.mkdir()
            results_dir.mkdir()
            torch.save(
                (
                    torch.ones(4, 1, 2, 2, dtype=torch.float32),
                    torch.tensor([0, 1, 0, 1], dtype=torch.long),
                ),
                data_dir / "train.pt",
            )
            (root / "harness.py").write_text(
                "\n".join(
                    [
                        "from pathlib import Path",
                        "import os",
                        "import torch",
                        "data_path = Path(os.environ['DEEPCODE_DATA_PATH'])",
                        "images, labels = torch.load(data_path / 'train.pt')",
                        "model = train(images, labels)",
                        "assert getattr(model, 'was_trained', False)",
                        "print('metric: accuracy=0.7500')",
                    ]
                ),
                encoding="utf-8",
            )

            result = evaluate_submission(
                EvaluationRequest(
                    code=(
                        "class TinyModel:\n"
                        "    was_trained = True\n\n"
                        "def train(images, labels):\n"
                        "    return TinyModel()\n"
                    ),
                    problem={"evaluation": {"type": "ml_torch_lab", "harness": "harness.py"}},
                    tests=[{"name": "visible contract", "test": "assert callable(train)\nprint('visible ok')"}],
                    environment={"timeout_seconds": 10, "packages": ["torch"]},
                    runtime={
                        "problem_dir": str(root),
                        "data_path": str(data_dir),
                        "results_path": str(results_dir),
                    },
                )
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual([item["name"] for item in result["results"]], ["visible contract", "lab scoring"])
        self.assertIn("visible ok", result["results"][0]["actual_output"])
        self.assertIn("metric: accuracy=0.7500", result["results"][1]["actual_output"])

    def test_ml_torch_lab_can_skip_hidden_harness_for_visible_check_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "harness.py").write_text("raise AssertionError('hidden harness should not run')", encoding="utf-8")

            result = evaluate_submission(
                EvaluationRequest(
                    code="def train():\n    return None\n",
                    problem={"evaluation": {"type": "ml_torch_lab", "harness": "harness.py"}},
                    tests=[{"name": "visible only", "test": "assert callable(train)\nprint('visible ok')"}],
                    environment={"timeout_seconds": 10, "packages": ["torch"]},
                    runtime={"problem_dir": str(root), "skip_hidden_harness": True},
                )
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["results"][0]["name"], "visible only")

    def test_ml_torch_lab_exposes_preferred_torch_device_to_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "harness.py").write_text(
                "import os\n"
                "assert os.environ['DEEPCODE_TORCH_DEVICE'] == 'mps'\n"
                "print('device: ' + os.environ['DEEPCODE_TORCH_DEVICE'])\n",
                encoding="utf-8",
            )

            with patch("deepcode.evaluators.ml_torch_lab.preferred_torch_device", return_value="mps"):
                result = evaluate_submission(
                    EvaluationRequest(
                        code="def train():\n    return None\n",
                        problem={"evaluation": {"type": "ml_torch_lab", "harness": "harness.py"}},
                        tests=[{"name": "visible", "test": "assert callable(train)"}],
                        environment={"timeout_seconds": 10, "packages": ["torch"]},
                        runtime={"problem_dir": str(root)},
                    )
                )

        self.assertEqual(result["status"], "passed")
        self.assertIn("device: mps", result["results"][1]["actual_output"])

    def test_streams_ml_modeling_stdout_before_final_result(self):
        events = list(
            stream_evaluation_events(
                EvaluationRequest(
                    code="def train():\n    print('epoch 1 loss=0.50')\n",
                    problem={"evaluation": {"type": "ml_modeling"}},
                    tests=[
                        {
                            "name": "training log",
                            "test": "train()\nprint('done')\n",
                        }
                    ],
                    environment={"timeout_seconds": 2},
                )
            )
        )

        log_events = [event for event in events if event["type"] == "log"]
        self.assertEqual(events[0], {"type": "check_started", "index": 0, "name": "training log"})
        self.assertEqual(log_events[0]["stream"], "stdout")
        self.assertEqual(log_events[0]["text"], "epoch 1 loss=0.50\n")
        self.assertEqual(events[-1]["type"], "run_finished")
        self.assertEqual(events[-1]["result"]["status"], "passed")
        self.assertIn("done", events[-1]["result"]["results"][0]["actual_output"])

    def test_ml_torch_modeling_uses_torch_resource_limiter(self):
        request = EvaluationRequest(
            code="import torch\n",
            problem={"evaluation": {"type": "ml_torch_modeling"}},
            tests=[{"name": "noop", "test": "import torch\n"}],
            environment={"timeout_seconds": 10, "packages": ["torch"]},
        )

        with patch(
            "deepcode.evaluators.ml_torch_modeling.run_modeling_checks",
            return_value={"status": "passed"},
        ) as run_checks:
            result = ml_torch_modeling.MlTorchModelingEvaluator().evaluate(request)

        self.assertEqual(result["status"], "passed")
        self.assertIs(
            run_checks.call_args.kwargs["resource_limiter_factory"],
            ml_torch_modeling._torch_resource_limiter,
        )

    def test_ml_torch_modeling_exposes_preferred_torch_device_to_checks(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="import os\n\ndef selected_device():\n    return os.environ['DEEPCODE_TORCH_DEVICE']\n",
                problem={"evaluation": {"type": "ml_torch_modeling"}},
                tests=[
                    {
                        "name": "device env",
                        "test": "assert selected_device() in {'cuda', 'mps', 'cpu'}\nprint(selected_device())",
                    }
                ],
                environment={"timeout_seconds": 10, "packages": ["torch"]},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertIn(result["results"][0]["actual_output"], {"cuda", "mps", "cpu"})

    def test_ml_torch_modeling_shows_submission_focused_tracebacks(self):
        result = evaluate_submission(
            EvaluationRequest(
                code=(
                    "import torch\n"
                    "from torch import nn\n\n"
                    "class BrokenModule(nn.Module):\n"
                    "    def forward(self, x):\n"
                    "        return x.masked_fill(torch.ones(2, dtype=torch.bool), 0)\n"
                ),
                problem={"evaluation": {"type": "ml_torch_modeling"}},
                tests=[{"name": "shape mismatch", "test": "BrokenModule()(torch.ones(4))"}],
                environment={"timeout_seconds": 10, "packages": ["torch"]},
            )
        )

        actual_output = result["results"][0]["actual_output"]
        self.assertEqual(result["status"], "failed")
        self.assertIn('File "submission_check.py"', actual_output)
        self.assertIn("return x.masked_fill", actual_output)
        self.assertIn("RuntimeError", actual_output)
        self.assertNotIn("site-packages", actual_output)
        self.assertNotIn("torch/nn/modules/module.py", actual_output)
        self.assertNotIn("deepcode-modeling-", actual_output)

    def test_streamed_ml_modeling_tracebacks_hide_temp_paths(self):
        events = list(
            stream_evaluation_events(
                EvaluationRequest(
                    code="def boom():\n    raise RuntimeError('bad shape')\n",
                    problem={"evaluation": {"type": "ml_modeling"}},
                    tests=[{"name": "failure", "test": "boom()"}],
                    environment={"timeout_seconds": 2},
                )
            )
        )

        stderr_text = "".join(event["text"] for event in events if event["type"] == "log" and event["stream"] == "stderr")
        self.assertIn('File "submission_check.py"', stderr_text)
        self.assertNotIn("deepcode-modeling-", stderr_text)

    def test_ml_modeling_normalizes_mixed_tab_indentation(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def classify(value):\n\tif value > 0:\n        return 'positive'\n\treturn 'other'\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "positive", "test": "assert classify(1) == 'positive'"}],
                environment={"timeout_seconds": 2},
            )
        )

        self.assertEqual(result["status"], "passed")

    def test_ml_modeling_reports_assertion_failures_without_stopping(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def square(x):\n    return x + 1\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {"name": "fails", "test": "assert square(4) == 16"},
                    {"name": "passes", "test": "assert square(0) == 1"},
                ],
                environment={"timeout_seconds": 2},
            )
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["passed"], 1)
        self.assertFalse(result["results"][0]["passed"])
        self.assertIn("AssertionError", result["results"][0]["actual_output"])
        self.assertTrue(result["results"][1]["passed"])

    def test_ml_modeling_times_out_cleanly(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def wait_forever():\n    while True:\n        pass\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "timeout", "test": "wait_forever()"}],
                environment={"timeout_seconds": 1},
            )
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("Timed out", result["results"][0]["actual_output"])

    def test_ml_modeling_exposes_runtime_paths_to_checks(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def noop():\n    return None\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {
                        "name": "runtime paths",
                        "test": (
                            "import os\n"
                            "assert os.environ['DEEPCODE_PROBLEM_DIR'].endswith('/problem')\n"
                            "assert os.environ['DEEPCODE_DATA_PATH'].endswith('/problem/data')\n"
                            "assert os.environ['DEEPCODE_RESULTS_PATH'].endswith('/problem/eval-results')\n"
                            "noop()\n"
                        ),
                    }
                ],
                environment={"timeout_seconds": 2},
                runtime={
                    "problem_dir": "/tmp/problem",
                    "data_path": "/tmp/problem/data",
                    "results_path": "/tmp/problem/eval-results",
                },
            )
        )

        self.assertEqual(result["status"], "passed")


if __name__ == "__main__":
    unittest.main()
