import torch
from torch.nn import functional as F


def dpo_loss(policy_chosen_logps, policy_rejected_logps,
             ref_chosen_logps, ref_rejected_logps, beta=0.1):
    policy_gap = policy_chosen_logps - policy_rejected_logps
    reference_gap = ref_chosen_logps.detach() - ref_rejected_logps.detach()
    logits = beta * (policy_gap - reference_gap)
    return -F.logsigmoid(logits).mean()
