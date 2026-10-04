import unittest
from pathlib import Path

import numpy as np

from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]


class MatrixDebuggingStarterTest(unittest.TestCase):
    def test_starter_runs_and_exposes_distinct_numerical_defects(self):
        problem = ProblemStore(ROOT / "problems").get_problem(
            "matrix-framework-debugging"
        )
        namespace = {}
        exec(problem["starter_code"], namespace)
        matrix_type = namespace["Matrix"]

        ordinary = matrix_type([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(ordinary.sum(), 21)
        np.testing.assert_array_equal(
            ordinary.transpose().to_ndarray(), [[1, 4], [2, 5], [3, 6]]
        )

        zeros = matrix_type.zeros(2, 3)
        zeros.set(0, 1, 9)
        self.assertNotEqual(zeros.to_ndarray()[1, 1], 0)

        decimals = np.array([[1.5, -2.25], [3.75, 4.5]])
        converted = matrix_type.from_ndarray(decimals)
        self.assertFalse(np.array_equal(converted.to_ndarray(), decimals))
        self.assertFalse(np.array_equal(ordinary.sum(axis=0), [5, 7, 9]))

        cloned = ordinary.copy()
        cloned.set(0, 0, 99)
        self.assertNotEqual(ordinary.to_ndarray()[0, 0], 1)


if __name__ == "__main__":
    unittest.main()
