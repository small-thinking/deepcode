import torch
from torch import nn


class RewardModel(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.head = nn.Linear(input_dim, 1, bias=False)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.head(features).squeeze(-1)


def bt_loss(chosen_scores, rejected_scores):
    d = chosen_scores - rejected_scores
    return torch.logaddexp(torch.zeros_like(d), -d).mean()


def train_reward_model(pairs, epochs=20, batch_size=4, lr=0.1):
    chosen = torch.stack([c for c, _ in pairs])
    rejected = torch.stack([r for _, r in pairs])
    model = RewardModel(chosen.shape[1])
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    def evaluate_loss():
        with torch.no_grad():
            return bt_loss(model(chosen), model(rejected)).item()

    loss_history = [evaluate_loss()]
    for _ in range(epochs):
        for start in range(0, len(pairs), batch_size):
            c = chosen[start:start + batch_size]
            r = rejected[start:start + batch_size]
            loss = bt_loss(model(c), model(r))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
        loss_history.append(evaluate_loss())
    return model, loss_history
