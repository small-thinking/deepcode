import math

import torch
import torch.nn.functional as F


def clip_contrastive_loss(image_embeddings, text_embeddings, temperature=0.07, normalize=True):
    if image_embeddings.ndim != 2 or text_embeddings.ndim != 2:
        raise ValueError("embeddings must be rank-2")
    if image_embeddings.shape != text_embeddings.shape or image_embeddings.numel() == 0:
        raise ValueError("embedding shapes must match and be non-empty")
    if not math.isfinite(float(temperature)) or temperature <= 0:
        raise ValueError("temperature must be positive and finite")

    images = F.normalize(image_embeddings, dim=-1) if normalize else image_embeddings
    texts = F.normalize(text_embeddings, dim=-1) if normalize else text_embeddings
    logits = images @ texts.transpose(0, 1) / temperature
    labels = torch.arange(logits.shape[0], device=logits.device)
    image_loss = F.cross_entropy(logits, labels)
    text_loss = F.cross_entropy(logits.transpose(0, 1), labels)
    return (image_loss + text_loss) / 2
