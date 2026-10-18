import math

import torch
from torch import nn


class TinyCausalLM(nn.Module):
    def __init__(self, vocab_size, embed_dim, max_seq_len):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_seq_len = max_seq_len
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_len, embed_dim)
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.output = nn.Linear(embed_dim, vocab_size)

    def forward(self, token_ids):
        batch, length = token_ids.shape
        if length > self.max_seq_len:
            raise ValueError("sequence exceeds max_seq_len")
        positions = torch.arange(length, device=token_ids.device)
        x = self.token_embedding(token_ids) + self.position_embedding(positions)[None, :, :]
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.embed_dim)
        allowed = torch.ones(length, length, device=x.device, dtype=torch.bool).tril()
        weights = torch.softmax(scores.masked_fill(~allowed, float("-inf")), dim=-1)
        return self.output(weights @ v)


class SequenceClassifier(nn.Module):
    def __init__(self, lm, num_labels):
        super().__init__()
        self.lm = lm
        self.head = nn.Linear(lm.vocab_size, num_labels)

    def forward(self, token_ids, valid_mask):
        states = self.lm(token_ids)
        weights = valid_mask.to(states.dtype).unsqueeze(-1)
        pooled = (states * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1)
        return self.head(pooled)


@torch.no_grad()
def greedy_generate(model, prompt, steps, use_cache=True):
    tokens = prompt.clone()
    for _ in range(steps):
        next_id = model(tokens).select(1, tokens.shape[1] - 1).argmax(dim=-1, keepdim=True)
        tokens = torch.cat([tokens, next_id], dim=1)
    return tokens
