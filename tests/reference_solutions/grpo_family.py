"""Small policy-objective kernels; no generation engine or reference KL."""
import torch


def clipped_gain(ratio, advantages, clip_low, clip_high):
    clipped = ratio.clamp(1 - clip_low, 1 + clip_high)
    return torch.minimum(ratio * advantages, clipped * advantages)


def family_advantages(rewards, variant="grpo", eps=1e-6):
    rewards = rewards.detach()
    centered = rewards - rewards.mean(dim=-1, keepdim=True)
    if variant == "dr_grpo":
        return centered
    return centered / (rewards.std(dim=-1, correction=0, keepdim=True) + eps)


def family_policy_loss(logp, old_logp, rewards, response_mask, variant="grpo",
                       clip_low=0.2, clip_high=0.2, max_length=None, eps=1e-6):
    advantages = family_advantages(rewards, variant, eps)
    lengths = response_mask.sum(dim=-1)
    # Exclude padding before exp, so extreme padding cannot cause overflow.
    delta = (logp - old_logp.detach()).masked_fill(~response_mask, 0)
    if variant == "gspo":
        ratio = (delta.sum(dim=-1) / lengths).exp()
        return -clipped_gain(ratio, advantages, clip_low, clip_high).mean()
    ratio = delta.exp()
    gain = clipped_gain(ratio, advantages[..., None], clip_low, clip_high)
    gain = gain.masked_fill(~response_mask, 0)
    if variant == "dr_grpo":
        return -(gain.sum(dim=-1) / max_length).mean()
    if variant == "dapo":
        return -gain.sum() / lengths.sum()
    return -(gain.sum(dim=-1) / lengths).mean()


def soft_overlong_rewards(rewards, lengths, max_length, buffer_length):
    """DAPO reward shaping: buffer_length is the linear ramp width below the cap."""
    penalty = ((max_length - buffer_length - lengths.detach()).to(rewards.dtype)
               / buffer_length).clamp(-1, 0)
    return rewards.detach() + penalty
