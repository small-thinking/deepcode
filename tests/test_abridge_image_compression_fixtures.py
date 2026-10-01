import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("flip-invert-smooth-binary-image", "run-length-string-compression")


class AbridgeImageCompressionFixtureTest(unittest.TestCase):
    def test_reference_solutions_pass(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                result = evaluate_submission(EvaluationRequest(
                    code=(Path(problem["_runtime"]["problem_dir"]) / "solution.py").read_text(encoding="utf-8"),
                    problem=problem, tests=problem["tests"],
                    environment=problem["environment"], runtime=problem.get("_runtime", {}),
                ))
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))

    def test_image_requires_snapshot_smoothing(self):
        problem = ProblemStore(ROOT / "problems").get_problem(SLUGS[0])
        wrong = """def flip_invert_smooth(image):
    rows, cols = len(image), len(image[0])
    result = [[1 - row[cols - 1 - col] for col in range(cols)] for row in image]
    for r in range(rows):
        for c in range(cols):
            values = [result[i][j] for i in range(max(0, r-1), min(rows, r+2)) for j in range(max(0, c-1), min(cols, c+2))]
            result[r][c] = sum(values) // len(values)
    return result
"""
        result = evaluate_submission(EvaluationRequest(
            code=wrong, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))
        self.assertNotEqual(result["status"], "passed", result)

    def test_compression_requires_string_and_multi_digit_count(self):
        problem = ProblemStore(ROOT / "problems").get_problem(SLUGS[1])
        wrong = """def compress_runs(s):
    out = []
    i = 0
    while i < len(s):
        j = i + 1
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(s[i])
        if j - i > 1:
            out.append(str((j - i) % 10))
        i = j
    return "".join(out)
"""
        result = evaluate_submission(EvaluationRequest(
            code=wrong, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))
        self.assertNotEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
