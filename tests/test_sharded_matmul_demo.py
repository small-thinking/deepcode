import json
import shutil
import subprocess
import unittest
from pathlib import Path

import numpy as np

from deepcode.problem_store import ProblemStore
from deepcode.server import resolve_problem_demo

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'sharded-matrix-multiplication'


class ShardedMatmulDemoTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for demo arithmetic')
    def test_live_math_matches_dense_reference_and_finite_differences(self):
        problem = ProblemStore(ROOT / 'problems').get_problem(SLUG)
        demo = problem['interactive_demos'][0]
        self.assertEqual(demo['section'], 'interactive_demo')
        path = resolve_problem_demo(f"/problem-demos/{SLUG}/{demo['path']}", ROOT / 'problems')
        source = path.read_text(encoding='utf-8')
        core = source.split('const B=', 1)[1].split('let stage=', 1)[0]
        script = 'const B=' + core + '''
const cases = [];
for (const value of [-2, 0, 1, 3]) {
  for (const split of [1, 2, 3]) cases.push({value, split, ...calculate(value, split)});
}
console.log(JSON.stringify(cases));
'''
        result = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
        b = np.array([[1, 0, 2, -1], [0, 1, 1, 2], [1, -1, 0, 1]], dtype=float)
        dy = np.array([[1, 2, -1, 1], [0, 1, 2, -1]], dtype=float)
        eps = 1e-6
        for case in json.loads(result.stdout):
            with self.subTest(value=case['value'], split=case['split']):
                a = np.array(case['a'], dtype=float)
                split = case['split']
                np.testing.assert_allclose(case['y'], a @ b)
                np.testing.assert_allclose(case['da'], dy @ b.T)
                np.testing.assert_allclose(case['dbs'][0], (a.T @ dy)[:, :split])
                np.testing.assert_allclose(case['dbs'][1], (a.T @ dy)[:, split:])
                for i, (start, end) in enumerate([(0, split), (split, 4)]):
                    np.testing.assert_allclose(case['ys'][i], (a @ b)[:, start:end])
                    np.testing.assert_allclose(case['das'][i], dy[:, start:end] @ b[:, start:end].T)
                for index in np.ndindex(a.shape):
                    plus, minus = a.copy(), a.copy()
                    plus[index] += eps
                    minus[index] -= eps
                    numeric = (np.sum((plus @ b) * dy) - np.sum((minus @ b) * dy)) / (2 * eps)
                    self.assertAlmostEqual(numeric, case['da'][index[0]][index[1]], places=6)
                for index in np.ndindex(b.shape):
                    plus, minus = b.copy(), b.copy()
                    plus[index] += eps
                    minus[index] -= eps
                    numeric = (np.sum((a @ plus) * dy) - np.sum((a @ minus) * dy)) / (2 * eps)
                    owner = int(index[1] >= split)
                    local = index[1] - (split if owner else 0)
                    self.assertAlmostEqual(numeric, case['dbs'][owner][index[0]][local], places=6)


if __name__ == '__main__':
    unittest.main()
