import math
import torch
from torch import nn


class GQA(nn.Module):
    def __init__(self, n_heads, dim, n_kv_heads):
        super().__init__()
        assert not (n_heads <= 0 or dim <= 0 or n_kv_heads <= 0 or dim % n_heads or n_heads % n_kv_heads), "invalid head counts or dimension"
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.dim = dim
        self.head_dim = dim // n_heads
        self.kv_dim = n_kv_heads * self.head_dim
        self.W_qkv = nn.Linear(dim, dim + 2 * self.kv_dim)
        self.W_o = nn.Linear(dim, dim)

    def forward(self, x, mask=None):
        b, t, c = x.shape
        q, k, v = self.W_qkv(x).split([self.dim, self.kv_dim, self.kv_dim], dim=-1)
        q = q.reshape(b, t, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.reshape(b, t, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = v.reshape(b, t, self.n_kv_heads, self.head_dim).transpose(1, 2)
        k = k.repeat_interleave(self.n_heads // self.n_kv_heads, dim=1)
        v = v.repeat_interleave(self.n_heads // self.n_kv_heads, dim=1)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))
        out = (scores.softmax(dim=-1) @ v).transpose(1, 2).reshape(b, t, c)
        return self.W_o(out)
