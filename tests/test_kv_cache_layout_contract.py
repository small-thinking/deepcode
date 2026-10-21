"""Accept both external cache layouts without weakening decoding correctness."""
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission


FOLDER = Path(__file__).resolve().parents[1] / "problems/389-pytorch-multihead-kv-cache"

# Keep the flat projected tensors before splitting; no copy or merge-back is needed.
MERGED_SOLUTION = '''import math
import torch
from torch import nn

class MHA(nn.Module):
    def __init__(self, n_heads, dim):
        super().__init__()
        assert n_heads > 0 and dim > 0 and dim % n_heads == 0
        self.n_heads, self.dim = n_heads, dim
        self.W_qkv = nn.Linear(dim, 3 * dim)
        self.W_o = nn.Linear(dim, dim)

    def forward(self, x, mask=None, kv_cache=None):
        b, t, d = x.shape
        q, k, v = self.W_qkv(x).chunk(3, dim=-1)
        if kv_cache is not None:
            k = torch.cat((kv_cache[0], k), dim=1)
            v = torch.cat((kv_cache[1], v), dim=1)
        cache = (k, v)
        length = k.shape[1]
        q = q.reshape(b, t, self.n_heads, d // self.n_heads).transpose(1, 2)
        k = k.reshape(b, length, self.n_heads, d // self.n_heads).transpose(1, 2)
        v = v.reshape(b, length, self.n_heads, d // self.n_heads).transpose(1, 2)
        scores = q @ k.transpose(-2, -1) / math.sqrt(d // self.n_heads)
        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))
        output = (scores.softmax(-1) @ v).transpose(1, 2).reshape(b, t, d)
        return self.W_o(output), cache
'''


class KVCacheLayoutContractTest(unittest.TestCase):
    def evaluate(self, code, cache_only=False):
        problem = json.loads((FOLDER / "problem.json").read_text())
        tests = json.loads((FOLDER / "tests.json").read_text())
        return evaluate_submission(EvaluationRequest(
            code=code, problem=problem, tests=tests[1:2] if cache_only else tests,
            environment=problem["environment"], runtime={},
        ))

    def test_both_layouts_pass_visible_contract(self):
        for name, code in (("split", (FOLDER / "solution.py").read_text()),
                           ("merged", MERGED_SOLUTION)):
            with self.subTest(layout=name):
                result = self.evaluate(code)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], 3)

    def test_incorrect_cache_implementations_still_fail(self):
        split = (FOLDER / "solution.py").read_text()
        variants = {
            "old sequence length": MERGED_SOLUTION.replace("length = k.shape[1]", "length = t"),
            "detached returned cache": MERGED_SOLUTION.replace("cache = (k, v)", "cache = (k.detach(), v.detach())"),
            "detached reused cache": MERGED_SOLUTION.replace("kv_cache[0]", "kv_cache[0].detach()").replace("kv_cache[1]", "kv_cache[1].detach()"),
            "wrong projected values": MERGED_SOLUTION.replace("cache = (k, v)", "cache = (k + 1, v)"),
            "mixed K/V layouts": MERGED_SOLUTION.replace("cache = (k, v)", "cache = (k, v.reshape(b, -1, self.n_heads, d // self.n_heads).transpose(1, 2))"),
            "cache overwritten in place": MERGED_SOLUTION.replace("k = torch.cat((kv_cache[0], k), dim=1)", "kv_cache[0].add_(1)\n            k = torch.cat((kv_cache[0], k), dim=1)"),
            "layout changes after prefill": split.replace(
                "return self.W_o(out), (k, v)",
                "return self.W_o(out), ((k, v) if kv_cache is None else tuple(z.transpose(1, 2).reshape(b, -1, c) for z in (k, v)))",
            ),
        }
        for name, code in variants.items():
            with self.subTest(bug=name):
                result = self.evaluate(code, cache_only=True)
                self.assertNotEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
