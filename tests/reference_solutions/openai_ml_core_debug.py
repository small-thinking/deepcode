import math

import torch
from torch import nn
import torch.nn.functional as F


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


class MaskedEncoder(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        if embed_dim % num_heads:
            raise ValueError("embed_dim must divide num_heads")
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, x, valid_mask):
        batch, length, width = x.shape
        qkv = self.qkv(x).view(batch, length, 3, self.num_heads, self.head_dim)
        q, k, v = qkv.unbind(dim=2)
        q, k, v = (part.transpose(1, 2) for part in (q, k, v))
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_dim)
        key_mask = valid_mask[:, None, None, :]
        weights = torch.softmax(scores.masked_fill(~key_mask, float("-inf")), dim=-1)
        weights = torch.where(key_mask, weights, torch.zeros_like(weights))
        context = (weights @ v).transpose(1, 2).reshape(batch, length, width)
        encoded = self.proj(context)
        encoded = encoded * valid_mask.unsqueeze(-1).to(encoded.dtype)
        return encoded, weights


class MaskedEncoderClassifier(nn.Module):
    def __init__(self, encoder, num_labels, pooling="mean"):
        super().__init__()
        if pooling not in {"mean", "max"}:
            raise ValueError("pooling must be mean or max")
        self.encoder = encoder
        self.pooling = pooling
        self.head = nn.Linear(encoder.embed_dim, num_labels)

    def forward(self, x, valid_mask):
        encoded, _ = self.encoder(x, valid_mask)
        mask = valid_mask.unsqueeze(-1)
        if self.pooling == "mean":
            pooled = (encoded * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
        else:
            pooled = encoded.masked_fill(~mask, float("-inf")).max(dim=1).values
            pooled = torch.where(torch.isfinite(pooled), pooled, torch.zeros_like(pooled))
        return self.head(pooled)


def shift_targets(targets, bos_id):
    return torch.cat([torch.full_like(targets[:, :1], bos_id), targets[:, :-1]], dim=1)


def masked_cross_entropy(logits, targets, pad_id):
    flat_logits = logits.reshape(-1, logits.shape[-1])
    flat_targets = targets.reshape(-1)
    return F.cross_entropy(flat_logits, flat_targets, ignore_index=pad_id)


class ReverseModel(nn.Module):
    def __init__(self, vocab_size, embed_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.output = nn.Linear(embed_dim, vocab_size)

    def forward(self, source, decoder_input):
        source_summary = self.embedding(source).mean(dim=1, keepdim=True)
        return self.output(self.embedding(decoder_input) + source_summary)


@torch.no_grad()
def greedy_decode(model, source, bos_id, eos_id, max_steps):
    decoded = torch.full((source.shape[0], 1), bos_id, dtype=source.dtype, device=source.device)
    finished = torch.zeros(source.shape[0], dtype=torch.bool, device=source.device)
    for _ in range(max_steps):
        next_token = model(source, decoded)[:, -1].argmax(dim=-1)
        if eos_id is not None:
            next_token = torch.where(finished, torch.full_like(next_token, eos_id), next_token)
            finished |= next_token.eq(eos_id)
        decoded = torch.cat([decoded, next_token[:, None]], dim=1)
        if eos_id is not None and bool(finished.all()):
            break
    return decoded


class BinaryMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))

    def forward(self, x):
        return self.layers(x)


def binary_accuracy(logits, labels):
    targets = labels.reshape(-1).to(logits.dtype)
    predictions = (logits.reshape(-1) > 0).to(logits.dtype)
    return float((predictions == targets).float().mean().item())


def train_binary_mlp(features, labels, hidden_dim=8, lr=0.1, epochs=50):
    model = BinaryMLP(features.shape[1], hidden_dim)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    targets = labels.reshape(-1, 1).to(features.dtype)
    loss = torch.tensor(float("nan"))
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = F.binary_cross_entropy_with_logits(model(features), targets)
        loss.backward()
        optimizer.step()
    accuracy = binary_accuracy(model(features), targets)
    return model, float(loss.item()), accuracy
