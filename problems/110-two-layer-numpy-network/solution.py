import torch


class TwoLayerNet:
    def __init__(self, input_dim, hidden_dim, output_dim, *, dtype=torch.float64, device="cpu"):
        generator = torch.Generator().manual_seed(0)
        self.W1 = (torch.randn(input_dim, hidden_dim, generator=generator, dtype=dtype)*.1).to(device)
        self.b1 = torch.zeros(hidden_dim, dtype=dtype, device=device)
        self.W2 = (torch.randn(hidden_dim, output_dim, generator=generator, dtype=dtype)*.1).to(device)
        self.b2 = torch.zeros(output_dim, dtype=dtype, device=device)

    def forward(self, X):
        hidden = (X @ self.W1 + self.b1).clamp_min(0)
        return (hidden @ self.W2 + self.b2).softmax(dim=-1)

    def loss(self, preds, y):
        selected = preds.gather(1, y[:, None]).squeeze(1)
        return -selected.clamp_min(1e-12).log().mean()

    def train_step(self, X, y, learning_rate=0.1):
        hidden_linear = X @ self.W1 + self.b1
        hidden = hidden_linear.clamp_min(0)
        probs = (hidden @ self.W2 + self.b2).softmax(dim=-1)
        grad_logits = probs.clone()
        grad_logits[torch.arange(len(y), device=y.device), y] -= 1
        grad_logits /= len(y)
        grad_W2 = hidden.T @ grad_logits
        grad_b2 = grad_logits.sum(dim=0)
        grad_hidden = grad_logits @ self.W2.T
        grad_hidden = grad_hidden * (hidden_linear > 0)
        grad_W1 = X.T @ grad_hidden
        grad_b1 = grad_hidden.sum(dim=0)
        self.W1 = self.W1 - learning_rate * grad_W1
        self.b1 = self.b1 - learning_rate * grad_b1
        self.W2 = self.W2 - learning_rate * grad_W2
        self.b2 = self.b2 - learning_rate * grad_b2
        return self.loss(self.forward(X), y)
