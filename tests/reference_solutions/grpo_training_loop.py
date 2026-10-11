import torch
import torch.nn.functional as F


def sample_responses(logits, group_size, generator=None):
    probabilities = torch.softmax(logits, dim=-1)
    return torch.multinomial(probabilities, group_size, replacement=True, generator=generator)


def group_advantages(rewards, eps=1e-6):
    rewards = rewards.detach()
    centered = rewards - rewards.mean(dim=1, keepdim=True)
    return centered / (rewards.std(dim=1, keepdim=True, correction=0) + eps)


class GRPOTrainer:
    def __init__(self, policy_logits, learning_rate=0.1, beta=0.01,
                 clip_eps=0.2, eps=1e-6):
        self.policy_logits = torch.nn.Parameter(policy_logits.detach().clone())
        self.reference_logits = policy_logits.detach().clone()
        self.optimizer = torch.optim.SGD([self.policy_logits], lr=learning_rate)
        self.beta = beta
        self.clip_eps = clip_eps
        self.eps = eps

    def rollout(self, prompt_ids, reward_table, group_size, generator=None):
        with torch.no_grad():
            ids = prompt_ids.detach().clone()
            logits = self.policy_logits[ids]
            responses = sample_responses(logits, group_size, generator)
            rewards = reward_table.detach()[ids].gather(1, responses)
            old_logprobs = F.log_softmax(logits, dim=-1).gather(1, responses)
            return {
                "prompt_ids": ids,
                "responses": responses.clone(),
                "rewards": rewards.clone(),
                "old_logprobs": old_logprobs.clone(),
            }

    def loss(self, batch):
        ids = batch["prompt_ids"].detach()
        responses = batch["responses"].detach()
        old_logprobs = batch["old_logprobs"].detach()
        advantages = group_advantages(batch["rewards"], self.eps)

        current_logp = F.log_softmax(self.policy_logits[ids], dim=-1)
        chosen_logp = current_logp.gather(1, responses)
        ratio = torch.exp(chosen_logp - old_logprobs)
        clipped = ratio.clamp(1 - self.clip_eps, 1 + self.clip_eps)
        policy_loss = -torch.minimum(ratio * advantages, clipped * advantages).mean()

        reference_logp = F.log_softmax(self.reference_logits[ids], dim=-1)
        kl = (current_logp.exp() * (current_logp - reference_logp)).sum(-1).mean()
        return policy_loss + self.beta * kl

    def step(self, batch):
        self.optimizer.zero_grad()
        loss = self.loss(batch)
        value = float(loss.detach())
        loss.backward()
        self.optimizer.step()
        return value
