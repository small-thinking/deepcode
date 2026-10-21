import torch
import torch.nn.functional as F


def as_feature_tensor(values, like):
    return torch.as_tensor(values, dtype=like.dtype, device=like.device)


def channels_last(x):
    return x.permute(0, 2, 1)


def valid_token_mask(lengths, max_len):
    return torch.arange(max_len, device=lengths.device) < lengths[:, None]


def masked_mean_pooling(x, mask):
    """Average valid token vectors into one feature vector per sequence."""
    valid = x.masked_fill(~mask.unsqueeze(-1), 0)
    return valid.sum(dim=1) / mask.sum(dim=1, keepdim=True)


# Earlier helper name, retained for existing solutions.
masked_mean = masked_mean_pooling


def split_features(x, left_width):
    return x.split([left_width, x.shape[-1] - left_width], dim=-1)


def join_features(left, right):
    return torch.cat((left, right), dim=-1)


def class_logits(features, weight, bias):
    return F.linear(features, weight, bias)


def class_probabilities(logits, temperature):
    return F.softmax(logits / temperature, dim=-1)


def selected_log_probs(logits, labels):
    return F.log_softmax(logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)


def classification_loss(logits, labels):
    return F.cross_entropy(logits, labels)


def topk_predictions(logits, k):
    return torch.topk(logits, k, dim=-1).indices


def train_step(model, optimizer, x, lengths, labels):
    model.train()
    optimizer.zero_grad()
    mask = valid_token_mask(lengths, x.shape[1])
    pooled = masked_mean_pooling(x, mask)
    loss = classification_loss(model(pooled), labels)
    loss.backward()
    optimizer.step()
    return loss.detach()


def evaluate_batch(model, x, lengths, labels):
    model.eval()
    with torch.no_grad():
        mask = valid_token_mask(lengths, x.shape[1])
        logits = model(masked_mean_pooling(x, mask))
        predictions = logits.argmax(dim=-1)
        loss = classification_loss(logits, labels)
        accuracy = (predictions == labels).float().mean().item()
    return {
        "logits": logits,
        "predictions": predictions,
        "loss": loss,
        "accuracy": accuracy,
    }
