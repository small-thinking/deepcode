"""Maintainer-only reference functions for the normalization exercises."""
import torch


def layer_norm(x, gamma, beta, eps=1e-5):
    mean = x.mean(dim=-1, keepdim=True)
    variance = x.var(dim=-1, correction=0, keepdim=True)
    return (x - mean) / torch.sqrt(variance + eps) * gamma + beta


def batch_norm(x, gamma, beta, eps=1e-5):
    mean = x.mean(dim=0, keepdim=True)
    variance = x.var(dim=0, correction=0, keepdim=True)
    return (x - mean) / torch.sqrt(variance + eps) * gamma + beta


def rms_norm(x, gamma, eps=1e-5):
    return x / torch.sqrt(x.square().mean(dim=-1, keepdim=True) + eps) * gamma
