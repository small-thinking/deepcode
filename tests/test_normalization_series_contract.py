"""Exercise the authored checks without writing personal practice state."""
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/normalization_series.py').read_text()
FOLDERS = ('524-layer-norm-forward', '525-batch-norm-training-forward', '526-rms-norm-forward')


class NormalizationSeriesContractTest(unittest.TestCase):
    def test_reference_passes_each_real_evaluator(self):
        store = ProblemStore(ROOT / 'problems')
        for folder in FOLDERS:
            problem = store.get_problem(json.loads((ROOT / 'problems' / folder / 'problem.json').read_text())['slug'])
            with self.subTest(slug=problem['slug']):
                result = evaluate_submission(EvaluationRequest(
                    code=REFERENCE, problem=problem, tests=problem['tests'], environment=problem['environment']))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(problem['tests']), result)

    def test_checks_reject_common_normalization_mistakes(self):
        mutations = (
            ('sample variance in LayerNorm', 0, 0, 'x.var(dim=-1, correction=0, keepdim=True)', 'x.var(dim=-1, correction=1, keepdim=True)'),
            ('wrong LayerNorm axis', 0, 0, 'x.mean(dim=-1, keepdim=True)', 'x.mean(dim=0, keepdim=True)'),
            ('epsilon outside root', 0, 1, 'torch.sqrt(variance + eps)', '(torch.sqrt(variance) + eps)'),
            ('sample variance in BatchNorm', 1, 0, 'x.var(dim=0, correction=0, keepdim=True)', 'x.var(dim=0, correction=1, keepdim=True)'),
            ('wrong BatchNorm axis', 1, 0, 'x.mean(dim=0, keepdim=True)', 'x.mean(dim=-1, keepdim=True)'),
            ('centered RMSNorm', 2, 0, 'return x / torch.sqrt', 'return (x - x.mean(dim=-1, keepdim=True)) / torch.sqrt'),
            ('RMS reduced across batch', 2, 0, 'x.square().mean(dim=-1, keepdim=True)', 'x.square().mean(dim=0, keepdim=True)'),
        )
        for name, folder_index, check_index, old, new in mutations:
            with self.subTest(name=name):
                self.assertIn(old, REFERENCE)
                namespace = {}
                exec(compile(REFERENCE.replace(old, new), name, 'exec'), namespace)
                checks = json.loads((ROOT / 'problems' / FOLDERS[folder_index] / 'tests.json').read_text())
                with self.assertRaises((AssertionError, RuntimeError)):
                    exec(checks[check_index]['test'], namespace)


if __name__ == '__main__':
    unittest.main()
