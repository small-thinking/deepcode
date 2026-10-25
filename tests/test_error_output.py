import tempfile
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission, stream_evaluation_events
from deepcode.evaluators.errors import format_python_error
from deepcode.runner import run_submission
from deepcode.playground import run_playground


class ErrorOutputTest(unittest.TestCase):
    def test_coding_failure_keeps_only_editor_frames_and_cause(self):
        code = (
            "import torch\n"
            "from torch import nn\n\n"
            "def score(features):\n"
            "    return nn.Linear(2, 1)(features)\n"
        )
        result = run_submission(code, [{
            "test": "def helper():\n    score((1, 2))\nhelper()",
            "expected_output": "ok",
        }], runtime="pytorch", timeout_seconds=10)
        output = result["results"][0]["actual_output"]
        self.assertEqual(result["status"], "failed")
        self.assertIn("Line 5 in score", output)
        self.assertIn("return nn.Linear(2, 1)(features)", output)
        self.assertIn("TypeError: linear()", output)
        for noise in ("site-packages", "submission_test.py", "helper", "_call_impl", "deepcode-run-", "Traceback"):
            self.assertNotIn(noise, output)

    def test_syntax_error_has_editor_line_and_caret(self):
        result = run_submission("def broken():\n    return (1 + )\n", [{"test": "broken()", "expected_output": "ok"}])
        output = result["results"][0]["actual_output"]
        self.assertIn("Line 2", output)
        self.assertIn("return (1 + )", output)
        self.assertIn("^", output)
        self.assertIn("SyntaxError", output)
        self.assertNotIn("submission_test.py", output)

    def test_check_failure_never_displays_generated_code_or_line(self):
        result = evaluate_submission(EvaluationRequest(
            code="def answer():\n    return 4\n\n\n",
            problem={"evaluation": {"type": "ml_modeling"}},
            tests=[{"test": "secret_harness_detail = answer()\nassert secret_harness_detail == 5"}],
            environment={"timeout_seconds": 2},
        ))
        case = result["results"][0]
        self.assertEqual(case["actual_output"], "Test check\nAssertionError: Expected 5, got 4")
        self.assertEqual(case["assertion_mismatch"], {"actual": "4", "expected": "5", "message": None})

    def test_exception_chaining_retains_both_causes_and_editor_lines(self):
        code = (
            "def broken():\n"
            "    try:\n"
            "        int('bad')\n"
            "    except ValueError as exc:\n"
            "        raise RuntimeError('cannot train') from exc\n"
        )
        result = run_playground(code + "broken()\n", timeout_seconds=2)
        output = result["stderr"]
        self.assertIn("ValueError: invalid literal", output)
        self.assertIn("RuntimeError: cannot train", output)
        self.assertIn("direct cause", output)
        self.assertIn("Line 3 in broken", output)
        self.assertIn("Line 5 in broken", output)
        self.assertNotIn("deepcode-playground-", output)

    def test_streamed_torch_failure_matches_final_output_and_keeps_live_logs(self):
        events = stream_evaluation_events(EvaluationRequest(
            code=("import torch\nfrom torch import nn\nimport sys\n"
                  "def broken():\n"
                  "    print('training started', file=sys.stderr)\n"
                  "    print('epoch 1')\n"
                  "    return nn.Linear(2, 1)((1, 2))\n"),
            problem={"evaluation": {"type": "ml_torch_modeling"}},
            tests=[{"test": "broken()"}], environment={"timeout_seconds": 10},
        ))
        self.assertEqual(next(events)["type"], "check_started")
        # Both ordinary stderr and stdout arrive before the formatted traceback.
        logs = [next(events), next(events)]
        self.assertEqual({e["text"].strip() for e in logs}, {"training started", "epoch 1"})
        remaining = list(events)
        error = next(e["text"] for e in remaining if e["type"] == "log")
        self.assertIn("Line 7 in broken", error)
        self.assertIn("TypeError: linear()", error)
        self.assertNotIn("site-packages", error)
        self.assertNotIn("submission_check.py", error)
        self.assertEqual(remaining[-1]["result"]["results"][0]["actual_output"], "training started\n" + error.strip())

    def test_formatter_filters_each_traceback_after_warning_prelude(self):
        raw = ('warning before failure\nTraceback (most recent call last):\n'
               '  File "/tmp/run.py", line 4, in helper\n    hidden()\n'
               '  File "/tmp/run.py", line 2, in score\n    fail()\n'
               '  File "/lib/library.py", line 8, in fail\n    internal()\n'
               'ValueError: bad shape\n  more diagnostic details\n')
        output = format_python_error(raw, "def score():\n    fail()\n", "/tmp/run.py")
        self.assertEqual(output, "warning before failure\nLine 2 in score\n    fail()\nValueError: bad shape\n  more diagnostic details")

    def test_no_editor_frame_still_keeps_exception_message(self):
        raw = ('Traceback (most recent call last):\n'
               '  File "/lib/library.py", line 9, in import_model\n    internal()\n'
               'ImportError: missing backend\n')
        self.assertEqual(format_python_error(raw, "import model", "/tmp/run.py"), "Python execution\nImportError: missing backend")

    def test_exception_groups_filter_nested_frames_in_results_and_streams(self):
        code = (
            "import json\n"
            "def broken():\n"
            "    try:\n"
            "        json.loads('bad')\n"
            "    except ValueError as exc:\n"
            "        raise ExceptionGroup('training', [exc, TypeError('bad input')]) from None\n"
        )
        request = EvaluationRequest(
            code=code, problem={"evaluation": {"type": "ml_modeling"}},
            tests=[{"test": "broken()"}], environment={"timeout_seconds": 2},
        )
        events = list(stream_evaluation_events(request))
        outputs = [
            evaluate_submission(request)["results"][0]["actual_output"],
            "".join(e["text"] for e in events if e["type"] == "log"),
            run_submission(code, [{"test": "broken()", "expected_output": "ok"}])["results"][0]["actual_output"],
        ]
        for output in outputs:
            with self.subTest(output=output):
                self.assertIn("ExceptionGroup: training", output)
                self.assertIn("JSONDecodeError", output)
                self.assertIn("TypeError: bad input", output)
                self.assertIn("Line 4 in broken", output)
                self.assertIn("Line 6 in broken", output)
                self.assertNotIn('File "', output)
                self.assertNotIn("submission_", output)
                self.assertNotIn("decoder.py", output)

    def test_plain_stderr_is_preserved(self):
        self.assertEqual(format_python_error("custom diagnostic\n", "pass", "/tmp/run.py"), "custom diagnostic")


class ErrorOutputAcrossEvaluatorsTest(unittest.TestCase):
    def test_all_executable_problem_families_share_editor_focused_errors(self):
        cases = [
            ("ml_coding", "python", "import json", "json.loads('bad')", "JSONDecodeError"),
            ("ml_coding", "python", "import numpy as np", "np.ones(2).reshape(3)", "ValueError"),
            ("ml_coding", "pytorch", "import torch", "torch.nn.Linear(2, 1)((1, 2))", "TypeError"),
            ("ml_modeling", "python", "import json", "json.loads('bad')", "JSONDecodeError"),
            ("ml_modeling", "sklearn", "from sklearn.model_selection import train_test_split", "train_test_split([1])", "ValueError"),
            ("ml_torch_modeling", "python", "import torch", "torch.nn.Linear(2, 1)((1, 2))", "TypeError"),
            ("ml_torch_lab", "python", "import torch", "torch.nn.Linear(2, 1)((1, 2))", "TypeError"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "harness.py").write_text("# private scoring setup\nbroken()\n")
            for kind, runtime, imports, operation, error in cases:
                with self.subTest(kind=kind, runtime=runtime, operation=operation):
                    # Mixed indentation and trailing blank lines must preserve editor lines.
                    code = f"{imports}\n\ndef broken():\n\treturn {operation}\n\n\n"
                    request = EvaluationRequest(
                        code=code,
                        problem={"evaluation": {"type": kind, "harness": "harness.py"}},
                        tests=[] if kind == "ml_torch_lab" else [{"test": "broken()", "expected_output": "ok"}],
                        environment={"runtime": runtime, "timeout_seconds": 15},
                        runtime={"problem_dir": str(root)},
                    )
                    result = evaluate_submission(request)
                    events = list(stream_evaluation_events(request))
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(events[-1]["result"]["status"], "failed")
                    outputs = [result["results"][0]["actual_output"], events[-1]["result"]["results"][0]["actual_output"]]
                    outputs.extend(e["text"] for e in events if e["type"] == "log")
                    for output in outputs:
                        self.assertIn("Line 4 in broken", output)
                        self.assertIn(operation, output)
                        self.assertIn(error, output)
                        for noise in ('File "', "site-packages", "submission_", "private scoring setup"):
                            self.assertNotIn(noise, output)

    def test_caught_tracebacks_are_consistent_between_live_and_final_logs(self):
        code = (
            "import traceback\n"
            "try:\n"
            "    int('bad')\n"
            "except ValueError:\n"
            "    traceback.print_exc()\n"
        )
        for kind in ("ml_coding", "ml_modeling"):
            with self.subTest(kind=kind):
                request = EvaluationRequest(
                    code=code, problem={"evaluation": {"type": kind}},
                    tests=[{"test": "print('ok')", "expected_output": "ok"}],
                    environment={"timeout_seconds": 2},
                )
                events = list(stream_evaluation_events(request))
                output = events[-1]["result"]["results"][0]["actual_output"]
                self.assertIn("ValueError", output)
                self.assertIn("Line 3", output)
                self.assertNotIn("submission_", output)
                for event in events:
                    if event["type"] == "log":
                        self.assertNotIn("submission_", event["text"])
        playground = run_playground(code, timeout_seconds=2)
        self.assertEqual(playground["status"], "completed")
        self.assertIn("Line 3", playground["stderr"])
        self.assertNotIn("deepcode-playground-", playground["stderr"])
