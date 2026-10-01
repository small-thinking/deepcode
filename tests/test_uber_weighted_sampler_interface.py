import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUG = "uber-weighted-random-sampler"


class WeightedSamplerInterfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem(SLUG)
        cls.code = (ROOT / "problems" / f"429-{SLUG}" / "solution.py").read_text()

    def evaluate(self, code):
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=self.problem,
            tests=self.problem["tests"],
            environment=self.problem["environment"],
            runtime=self.problem.get("_runtime", {}),
        ))

    def test_independent_random_instance_is_accepted_without_injection(self):
        code = self.code.replace(
            "self.total = total",
            "self.total = total\n        self.generator = random.Random(777)",
        ).replace("unit = random.random()", "unit = self.generator.random()")
        result = self.evaluate(code)
        self.assertEqual(result["passed"], len(self.problem["tests"]), result)

    def test_uniform_choice_cannot_ignore_weights(self):
        result = self.evaluate(self.code.replace(
            "unit = random.random()",
            "return random.choice(self.values)\n        unit = random.random()",
        ))
        self.assertLess(result["passed"], len(self.problem["tests"]))


if __name__ == "__main__":
    unittest.main()
