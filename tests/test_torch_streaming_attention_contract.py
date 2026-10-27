"""Migration contracts for streaming entropy, tiled attention, and pure Q/K/V GQA."""
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = (
    '104-streaming-logit-entropy',
    '493-blockwise-online-softmax-attention',
    '367-grouped-query-attention',
)


def fixture(folder):
    path = ROOT / 'problems' / folder
    return (
        json.loads((path / 'problem.json').read_text()),
        json.loads((path / 'tests.json').read_text()),
        (path / 'solution.py').read_text(),
    )


def failures(folder, source, names=None):
    _, cases, _ = fixture(folder)
    namespace = {}
    exec(compile(source, '<contract candidate>', 'exec'), namespace)
    failed = []
    for case in cases:
        if names is not None and case['name'] not in names:
            continue
        try:
            exec(compile(case['test'], case['name'], 'exec'), namespace.copy())
        except Exception:
            failed.append(case['name'])
    return failed


class TorchStreamingAttentionContractTest(unittest.TestCase):
    def test_problem_local_references_pass_real_evaluators(self):
        for folder in FOLDERS:
            with self.subTest(folder=folder):
                problem, cases, source = fixture(folder)
                self.assertEqual(problem['evaluation']['type'], 'ml_torch_modeling')
                result = evaluate_submission(EvaluationRequest(
                    code=source, problem=problem, tests=cases,
                    environment=problem['environment'], runtime={},
                ))
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(cases), result)

    def test_tiled_contract_rejects_dense_sdpa_and_tile_local_softmax(self):
        folder = FOLDERS[1]
        _, _, reference = fixture(folder)
        guard_case = 'computes only bounded score tiles without attention helpers'
        variants = (
            ('dense', '''import torch
import math
def blockwise_attention(Q,K,V,block_size):
    return (Q@K.T/math.sqrt(Q.shape[1])).softmax(-1)@V
''', guard_case),
            ('SDPA', '''import torch
def blockwise_attention(Q,K,V,block_size):
    return torch.nn.functional.scaled_dot_product_attention(Q[None,None],K[None,None],V[None,None])[0,0]
''', guard_case),
            ('tile-local normalization', reference.replace(
                'tile_weights = (scores - new_maximum).exp()',
                'tile_weights = scores.softmax(dim=1)',
            ), 'matches a stable dense reference'),
        )
        for name, source, case in variants:
            with self.subTest(name=name):
                self.assertIn(case, failures(folder, source, {case}))

    def test_tensor_contracts_reject_detached_results(self):
        for folder, function, gradient_case in (
            (FOLDERS[0], 'streaming_entropy', 'batch and streaming gradients match dense entropy'),
            (FOLDERS[1], 'blockwise_attention', 'gradients and device match dense attention'),
            (FOLDERS[2], 'grouped_query_attention', 'shared-KV gradients and device match an independent per-head oracle'),
        ):
            with self.subTest(folder=folder):
                _, _, reference = fixture(folder)
                source = reference + f'''
_original = {function}
def {function}(*args, **kwargs):
    return _original(*args, **kwargs).detach()
'''
                self.assertIn(gradient_case, failures(folder, source, {gradient_case}))

    def test_streaming_contract_rejects_eager_block_collection(self):
        folder = FOLDERS[0]
        _, _, reference = fixture(folder)
        case = 'streaming releases previous blocks during a single pass'
        source = reference + """
_original = streaming_entropy
def streaming_entropy(blocks):
    return _original(list(blocks))
"""
        self.assertIn(case, failures(folder, source, {case}))

    def test_alternate_gqa_head_expansion_passes(self):
        folder = FOLDERS[2]
        _, _, source = fixture(folder)
        for name in ('key', 'value'):
            source = source.replace(
                f'{name}.repeat_interleave(repeat, dim=1)',
                f'{name}[:, :, None].expand(batch, {name}.shape[1], repeat, {name}.shape[2], width).reshape(batch, query_heads, {name}.shape[2], width)',
            )
        self.assertEqual(failures(folder, source), [])


if __name__ == '__main__':
    unittest.main()
