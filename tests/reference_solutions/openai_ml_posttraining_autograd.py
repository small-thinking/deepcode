import torch
import torch.nn.functional as F


def posterior_true_labels(prior, confusion, annotations, temperature=1.0):
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if confusion.ndim != 3 or annotations.ndim != 2:
        raise ValueError("expected confusion and annotations tensors")
    log_posterior = prior.log().expand(annotations.shape[0], -1).clone()
    for annotator in range(annotations.shape[1]):
        reported = annotations[:, annotator]
        present = reported.ge(0)
        if present.any():
            log_posterior[present] += confusion[annotator, :, reported[present]].transpose(0, 1).log()
    return torch.softmax(log_posterior / temperature, dim=-1)


def annotation_nll(logits, confusion, annotations):
    log_prior = F.log_softmax(logits, dim=-1)
    terms = []
    for annotator in range(annotations.shape[1]):
        reported = annotations[:, annotator]
        present = reported.ge(0)
        if present.any():
            likelihood = confusion[annotator, :, reported[present]].transpose(0, 1).log()
            terms.append(torch.logsumexp(log_prior[present] + likelihood, dim=-1))
    if not terms:
        raise ValueError("at least one annotation is required")
    return -torch.cat(terms).mean()


@torch.no_grad()
def evaluate_in_chunks(fn, inputs, chunk_size):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return torch.cat([fn(inputs[start : start + chunk_size]) for start in range(0, inputs.shape[0], chunk_size)])


def group_relative_advantages(rewards, group_size, eps=1e-6):
    if group_size <= 0 or rewards.numel() % group_size:
        raise ValueError("rewards must divide into non-empty groups")
    with torch.no_grad():
        groups = rewards.detach().reshape(-1, group_size)
        return ((groups - groups.mean(dim=1, keepdim=True)) / (groups.std(dim=1, keepdim=True, correction=0) + eps)).reshape(-1)


def gather_response_logprobs(logits, sequences, response_mask):
    if logits.shape[:2] != sequences.shape or sequences.shape != response_mask.shape:
        raise ValueError("logits, sequences, and mask must align")
    gathered = F.log_softmax(logits[:, :-1], dim=-1).gather(-1, sequences[:, 1:].unsqueeze(-1)).squeeze(-1)
    result = torch.zeros_like(response_mask, dtype=logits.dtype)
    result[:, 1:] = gathered
    return result * response_mask.to(result.dtype)


def masked_kl(policy_logits, reference_logits, response_mask):
    policy_log_probs = F.log_softmax(policy_logits, dim=-1)
    reference_log_probs = F.log_softmax(reference_logits.detach(), dim=-1)
    reference_probs = reference_log_probs.exp()
    per_token = (reference_probs * (reference_log_probs - policy_log_probs)).sum(dim=-1)
    weights = response_mask.to(per_token.dtype)
    return (per_token * weights).sum() / weights.sum().clamp_min(1)


def grpo_loss(logits, reference_logits, sequences, response_mask, rewards, group_size, beta=0.01):
    advantages = group_relative_advantages(rewards, group_size)
    selected = gather_response_logprobs(logits, sequences, response_mask)
    weights = response_mask.to(selected.dtype)
    policy_term = -((selected.sum(dim=1) * advantages).mean())
    return policy_term + beta * masked_kl(logits, reference_logits, response_mask)


def _sum_to_shape(gradient, shape):
    while gradient.ndim > len(shape):
        gradient = gradient.sum(dim=0)
    for axis, size in enumerate(shape):
        if size == 1 and gradient.shape[axis] != 1:
            gradient = gradient.sum(dim=axis, keepdim=True)
    return gradient


class MatMul(torch.autograd.Function):
    @staticmethod
    def forward(ctx, a, b):
        ctx.save_for_backward(a, b)
        return torch.matmul(a, b)

    @staticmethod
    def backward(ctx, grad_output):
        a, b = ctx.saved_tensors
        grad_a = torch.matmul(grad_output, b.transpose(-2, -1))
        grad_b = torch.matmul(a.transpose(-2, -1), grad_output)
        return _sum_to_shape(grad_a, a.shape), _sum_to_shape(grad_b, b.shape)


def matmul(a, b):
    return MatMul.apply(a, b)


def chain_forward(matrices):
    if not matrices:
        raise ValueError("matrices must be non-empty")
    result = matrices[0]
    for matrix in matrices[1:]:
        result = result @ matrix
    return result


def chain_backward(matrices, grad_output):
    if not matrices:
        raise ValueError("matrices must be non-empty")
    gradients = []
    for index, matrix in enumerate(matrices):
        left = torch.eye(matrix.shape[0], dtype=matrix.dtype, device=matrix.device)
        for prior in matrices[:index]:
            left = left @ prior
        right = torch.eye(matrix.shape[1], dtype=matrix.dtype, device=matrix.device)
        for later in matrices[index + 1 :]:
            right = right @ later
        gradients.append(left.transpose(-2, -1) @ grad_output @ right.transpose(-2, -1))
    return gradients
