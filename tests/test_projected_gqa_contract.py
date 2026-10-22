"""Verify that GQA fixtures reject coverage gaps without prescribing a head expansion API."""
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'problems/390-pytorch-projected-grouped-query-attention'


class ProjectedGQAContractTest(unittest.TestCase):
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

    def test_expand_based_head_sharing_passes_all_cases(self):
        code = self.reference
        for tensor in ('k', 'v'):
            original = (
                f'        {tensor} = {tensor}.repeat_interleave('
                'self.n_heads // self.n_kv_heads, dim=1)'
            )
            expanded = (
                f'        {tensor} = {tensor}[:, :, None].expand('
                'b, self.n_kv_heads, self.n_heads // self.n_kv_heads, t, self.head_dim'
                ').reshape(b, self.n_heads, t, self.head_dim)'
            )
            self.assertIn(original, code)
            code = code.replace(original, expanded)
        result = self.evaluate(code, self.cases)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], len(self.cases))

    def test_added_cases_reject_bugs_that_original_cases_allowed(self):
        variants = (
            (
                'hardcoded head width',
                self.reference.replace('self.head_dim = dim // n_heads', 'self.head_dim = 2'),
                'varied Q/KV head counts, group sizes, dtypes, and shared-KV gradients',
            ),
            (
                'intermediate GQA assumes groups of two',
                self.reference.replace(
                    'self.n_heads // self.n_kv_heads',
                    '(2 if 1 < self.n_kv_heads < self.n_heads else self.n_heads // self.n_kv_heads)',
                ),
                'varied Q/KV head counts, group sizes, dtypes, and shared-KV gradients',
            ),
            (
                'mask shared across Q heads',
                self.reference.replace(
                    '        if mask is not None:\n',
                    '        if mask is not None and mask.ndim == 4:\n'
                    '            mask = mask[:, :1]\n'
                    '        if mask is not None:\n',
                ),
                'per-query-head mask broadcasting and combined causal-padding masks',
            ),
            (
                'parameter mutation',
                self.reference.replace(
                    '        b, t, c = x.shape',
                    '        self.W_o.weight.data.mul_(1.01)\n        b, t, c = x.shape',
                ),
                'forward preserves inputs, masks, and parameters across calls',
            ),
            (
                'mask mutation',
                self.reference.replace(
                    '        if mask is not None:\n',
                    '        if mask is not None:\n            mask[..., -1] = True\n',
                ),
                'forward preserves inputs, masks, and parameters across calls',
            ),
            (
                'unstable softmax',
                self.reference.replace(
                    'scores.softmax(dim=-1)',
                    '(scores.exp() / scores.exp().sum(dim=-1, keepdim=True))',
                ),
                'large finite grouped-attention scores use stable softmax',
            ),
        )
        for name, code, case_name in variants:
            with self.subTest(name=name):
                self.assertNotEqual(code, self.reference)
                original = self.evaluate(code, self.cases[:4])
                self.assertEqual(original['status'], 'passed', original)
                added = self.evaluate(code, [case for case in self.cases if case['name'] == case_name])
                self.assertEqual(added['total'], 1)
                self.assertEqual(added['status'], 'failed', added)
                self.assertNotIn('Timed out', added['results'][0]['actual_output'])


if __name__ == '__main__':
    unittest.main()
