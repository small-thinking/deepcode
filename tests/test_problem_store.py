import json
import tempfile
import unittest
from pathlib import Path

from deepcode.problem_store import ProblemStore


class ProblemStoreTest(unittest.TestCase):
    def test_loads_problem_folders_and_sorts_by_numeric_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "mean-prediction",
                {
                    "id": "20",
                    "slug": "mean-prediction",
                    "title": "Mean Prediction",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["baseline"],
                    "prompt": "Return the mean.",
                    "starter_code": "def predict_mean(values):\n    pass\n",
                    "example": {
                        "input": "values = [1, 2, 3]",
                        "output": "2.0",
                        "reasoning": "The arithmetic mean is 2.",
                    },
                    "environment": {
                        "language": "python",
                        "timeout_seconds": 2,
                        "packages": [],
                        "comparator": "numeric",
                    },
                },
                [{"name": "basic", "test": "print(predict_mean([1, 2, 3]))", "expected_output": "2.0"}],
            )
            self._write_problem(
                root,
                "dot-product",
                {
                    "id": "3",
                    "slug": "dot-product",
                    "title": "Dot Product",
                    "category": "Linear Algebra",
                    "difficulty": "medium",
                    "tags": ["vectors"],
                    "prompt": "Return a dot product.",
                    "starter_code": "def dot_product(a, b):\n    pass\n",
                    "example": {
                        "input": "a = [1, 2], b = [3, 4]",
                        "output": "11",
                        "reasoning": "1 * 3 + 2 * 4 = 11.",
                    },
                    "environment": {
                        "language": "python",
                        "timeout_seconds": 2,
                        "packages": [],
                        "comparator": "exact",
                    },
                },
                [{"name": "basic", "test": "print(dot_product([1, 2], [3, 4]))", "expected_output": "11"}],
            )

            store = ProblemStore(root)

            self.assertEqual([problem["id"] for problem in store.list_problems()], ["3", "20"])
            self.assertEqual(store.categories(), ["Linear Algebra", "Machine Learning"])
            self.assertEqual(store.get_problem("mean-prediction")["tests"][0]["name"], "basic")
            self.assertEqual(store.get_problem("20")["slug"], "mean-prediction")

    def test_filters_problem_list_by_category_difficulty_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "linear-regression",
                {
                    "id": "14",
                    "slug": "linear-regression",
                    "title": "Linear Regression Baseline",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["regression"],
                    "prompt": "Fit a line.",
                    "starter_code": "def fit_baseline(x, y):\n    pass\n",
                    "example": {"input": "x = [1]", "output": "1", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                },
                [{"name": "basic", "test": "print(fit_baseline([1], [1]))", "expected_output": "1"}],
            )
            self._write_problem(
                root,
                "matrix-dot",
                {
                    "id": "1",
                    "slug": "matrix-dot",
                    "title": "Matrix Dot",
                    "category": "Linear Algebra",
                    "difficulty": "easy",
                    "tags": ["matrix"],
                    "prompt": "Multiply.",
                    "starter_code": "def matrix_dot(a, b):\n    pass\n",
                    "example": {"input": "a = [[1]], b = [2]", "output": "[2]", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                },
                [{"name": "basic", "test": "print(matrix_dot([[1]], [2]))", "expected_output": "[2]"}],
            )

            store = ProblemStore(root)

            filtered = store.list_problems(category="Machine Learning", difficulty="easy", search="baseline")

            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["slug"], "linear-regression")
            self.assertNotIn("tests", filtered[0])
            self.assertNotIn("starter_code", filtered[0])

    def _write_problem(self, root, folder, problem, tests):
        problem_dir = root / folder
        problem_dir.mkdir()
        (problem_dir / "problem.json").write_text(json.dumps(problem), encoding="utf-8")
        (problem_dir / "tests.json").write_text(json.dumps(tests), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
