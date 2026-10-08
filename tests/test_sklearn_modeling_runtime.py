import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission, stream_evaluation_events


class SklearnModelingRuntimeTest(unittest.TestCase):
    def request(self, code, timeout=10):
        return EvaluationRequest(
            code=code,
            problem={"evaluation": {"type": "ml_modeling"}},
            tests=[{"name": "sklearn check", "test": "print('ok')"}],
            environment={"runtime": "sklearn", "timeout_seconds": timeout},
        )

    def test_fits_and_predicts_in_normal_and_streaming_evaluator(self):
        code = """import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_info

assert os.environ['OMP_NUM_THREADS'] == '1'
assert all(pool['num_threads'] == 1 for pool in threadpool_info())
x = pd.DataFrame({'feature': [-3., -2., 2., 3.]})
model = LogisticRegression().fit(x, [0, 0, 1, 1])
assert model.predict(pd.DataFrame({'feature': [-4., 4.]})).tolist() == [0, 1]
"""
        request = self.request(code)
        result = evaluate_submission(request)
        self.assertEqual(result["status"], "passed", result)
        events = list(stream_evaluation_events(request))
        result = events[-1]["result"]
        self.assertEqual(result["status"], "passed", events)

    def test_wall_timeout_still_stops_normal_and_streaming_runs(self):
        request = self.request("while True:\n    pass", timeout=0.2)
        results = [
            evaluate_submission(request),
            list(stream_evaluation_events(request))[-1]["result"],
        ]
        for result in results:
            self.assertEqual(result["status"], "failed", result)
            self.assertIn("Timed out after 0.2 seconds", result["results"][0]["actual_output"])

    def test_rejects_unknown_modeling_runtime(self):
        request = EvaluationRequest(
            code="", problem={"evaluation": {"type": "ml_modeling"}}, tests=[],
            environment={"runtime": "unknown"},
        )
        with self.assertRaisesRegex(ValueError, "Unsupported ML modeling runtime"):
            evaluate_submission(request)


if __name__ == "__main__":
    unittest.main()
