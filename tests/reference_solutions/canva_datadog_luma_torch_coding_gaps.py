import math
import numbers

import torch
from torch import nn


class TinyDenoiser(nn.Module):
    def __init__(self, channels, hidden_channels):
        super().__init__()
        if type(channels) is not int or type(hidden_channels) is not int or channels <= 0 or hidden_channels <= 0:
            raise ValueError("channel counts must be positive integers")
        self.layers = nn.Sequential(
            nn.Conv2d(channels, hidden_channels, kernel_size=3, padding=1),
            nn.SiLU(),
            nn.Conv2d(hidden_channels, channels, kernel_size=3, padding=1),
        )

    def forward(self, noisy_images):
        return self.layers(noisy_images)


def diffusion_train_step(model, optimizer, clean_uint8, noise, alpha_bar):
    if not isinstance(clean_uint8, torch.Tensor) or clean_uint8.dtype != torch.uint8:
        raise ValueError("clean images must be uint8 tensors")
    if clean_uint8.ndim != 4 or clean_uint8.numel() == 0 or any(size == 0 for size in clean_uint8.shape):
        raise ValueError("clean images must be non-empty rank-four tensors")
    if not isinstance(noise, torch.Tensor) or not noise.is_floating_point() or noise.shape != clean_uint8.shape:
        raise ValueError("noise must be a same-shape floating tensor")
    if noise.device != clean_uint8.device or not torch.isfinite(noise).all():
        raise ValueError("noise must be finite and on the image device")
    if isinstance(alpha_bar, bool) or not isinstance(alpha_bar, numbers.Real) or not math.isfinite(alpha_bar) or not 0 <= alpha_bar <= 1:
        raise ValueError("alpha_bar must be finite and in [0, 1]")
    clean = clean_uint8.to(dtype=noise.dtype) / 127.5 - 1.0
    alpha = clean.new_tensor(float(alpha_bar))
    noisy = alpha.sqrt() * clean + (1.0 - alpha).sqrt() * noise
    prediction = model(noisy)
    if not isinstance(prediction, torch.Tensor) or prediction.shape != noise.shape:
        raise ValueError("model output must match noise shape")
    loss = torch.mean((prediction - noise) ** 2)
    if not torch.isfinite(loss):
        raise ValueError("loss must be finite")
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
    return float(loss.detach().item())


