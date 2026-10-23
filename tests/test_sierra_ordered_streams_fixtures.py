import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests/reference_solutions/sierra_ordered_streams.py").read_text()


class SierraOrderedStreamsFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("sierra-ordered-streams")

    def evaluate(self, code, cases=None):
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=self.problem,
            tests=self.problem["tests"] if cases is None else cases,
            environment=self.problem["environment"],
            runtime=self.problem.get("_runtime", {}),
        ))

    def test_reference_passes_all_visible_cases(self):
        result = self.evaluate(REFERENCE)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(self.problem["tests"]))

    def test_merge_is_not_concatenation(self):
        code = REFERENCE + """
class MergeStream(Stream):
    def __init__(self, streams):
        self.streams = iter(streams)
        self.current = iter(())

    def next(self):
        while True:
            try:
                return next(self.current)
            except StopIteration:
                self.current = next(self.streams)
"""
        case = next(t for t in self.problem["tests"] if "Merge finite" in t["name"])
        self.assertNotEqual(self.evaluate(code, [case])["status"], "passed")

    def test_lazy_case_rejects_eager_materialization(self):
        code = REFERENCE + """
class MergeStream(Stream):
    def __init__(self, streams):
        self.values = iter(sorted(value for stream in streams for value in stream))

    def next(self):
        return next(self.values)
"""
        case = next(t for t in self.problem["tests"] if "Read lazily" in t["name"])
        self.assertNotEqual(self.evaluate(code, [case])["status"], "passed")


if __name__ == "__main__":
    unittest.main()
