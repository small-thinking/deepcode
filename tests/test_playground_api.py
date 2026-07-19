import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepcode.api import ApiContext, handle_api_request
from deepcode.problem_store import ProblemStore


class PlaygroundApiTest(unittest.TestCase):
    def test_runs_playground_code(self):
        expected = {
            "status": "completed",
            "exit_code": 0,
            "stdout": "ok\n",
            "stderr": "",
            "duration_ms": 12,
            "timeout_seconds": 30,
            "output_truncated": False,
        }
        with tempfile.TemporaryDirectory() as tmp, patch("deepcode.api.run_playground", return_value=expected) as run:
            status, payload = handle_api_request(
                ApiContext(store=ProblemStore(Path(tmp))),
                "POST",
                "/api/playground/run",
                {},
                json.dumps({"code": 'print("ok")'}).encode("utf-8"),
            )

        self.assertEqual(status, 200)
        self.assertEqual(payload, expected)
        run.assert_called_once_with('print("ok")')

    def test_rejects_missing_code_and_other_methods(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = ApiContext(store=ProblemStore(Path(tmp)))
            status, payload = handle_api_request(context, "POST", "/api/playground/run", {}, b"{}")
            list_status, list_payload = handle_api_request(context, "POST", "/api/playground/run", {}, b"[]")
            method_status, method_payload = handle_api_request(context, "GET", "/api/playground/run", {}, None)

        self.assertEqual(status, 400)
        self.assertIn("non-empty", payload["error"])
        self.assertEqual(list_status, 400)
        self.assertIn("JSON object", list_payload["error"])
        self.assertEqual(method_status, 405)
        self.assertEqual(method_payload["error"], "Method not allowed")


if __name__ == "__main__":
    unittest.main()
