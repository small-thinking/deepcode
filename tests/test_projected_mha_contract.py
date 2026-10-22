"""Check that the MHA fixtures accept valid implementations and catch coverage gaps."""
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'problems/388-pytorch-projected-multihead-attention'


class ProjectedMHAContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = json.loads((FOLDER / 'problem.json').read_text())
        cls.cases = json.loads((FOLDER / 'tests.json').read_text())
        cls.reference = (FOLDER / 'solution.py').read_text()

    def evaluate(self, code, cases):
        return evaluate_submission(EvaluationRequest(
            code=code, problem=self.problem, tests=cases,
            environment=self.problem['environment'], runtime={},
        ))

    def test_separate_qkv_splits_and_explicit_head_merge_are_supported(self):
        packed = (
            '        q, k, v = self.W_qkv(x).reshape(b, t, 3, self.n_heads, self.head_dim)'
            '.permute(2, 0, 3, 1, 4)'
        )
        separate = '''        q, k, v = self.W_qkv(x).chunk(3, dim=-1)
        q, k, v = [a.reshape(b, t, self.n_heads, self.head_dim).transpose(1, 2) for a in (q, k, v)]'''
        self.assertIn(packed, self.reference)
        code = self.reference.replace(packed, separate).replace(
            '.transpose(1, 2).reshape(b, t, c)',
            '.transpose(1, 2).contiguous().view(b, t, c)',
        )
        result = self.evaluate(code, self.cases)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], len(self.cases))

    def test_added_cases_reject_bugs_that_the_original_cases_allowed(self):
        variants = (
            (
                'hardcoded two heads',
                self.reference.replace('self.n_heads = n_heads', 'self.n_heads = 2')
                              .replace('self.head_dim = dim // n_heads', 'self.head_dim = dim // 2'),
                'different head counts, head widths, and float32/float64 inputs',
            ),
            (
                'mask shared across heads',
                self.reference.replace(
                    '        if mask is not None:\n',
                    '        if mask is not None and mask.ndim == 4:\n'
                    '            mask = mask[:, :1]\n'
                    '        if mask is not None:\n',
                ),
                'per-head and per-query mask broadcasting plus combined causal-padding masks',
            ),
            (
                'parameter mutation',
                self.reference.replace(
                    '        b, t, c = x.shape',
                    '        self.W_o.weight.data.mul_(1.01)\n        b, t, c = x.shape',
                ),
                'forward preserves inputs, masks, and learned parameters across calls',
            ),
            (
                'mask mutation',
                self.reference.replace(
                    '        if mask is not None:\n',
                    '        if mask is not None:\n            mask[..., -1] = True\n',
                ),
                'forward preserves inputs, masks, and learned parameters across calls',
            ),
            (
                'unstable softmax',
                self.reference.replace(
                    'scores.softmax(dim=-1)',
                    '(scores.exp() / scores.exp().sum(dim=-1, keepdim=True))',
                ),
                'large finite attention scores use numerically stable softmax',
            ),
        )
        for name, code, case_name in variants:
            with self.subTest(name=name):
                self.assertNotEqual(code, self.reference)
                original = self.evaluate(code, self.cases[:3])
                self.assertEqual(original['status'], 'passed', original)
                added = self.evaluate(code, [case for case in self.cases if case['name'] == case_name])
                self.assertEqual(added['total'], 1)
                self.assertEqual(added['status'], 'failed', added)


if __name__ == '__main__':
    unittest.main()
