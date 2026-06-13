from __future__ import annotations

from typing import Any

import torch


def preferred_torch_device() -> str:
    if torch.cuda.is_available():
        return "cuda"

    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"

    return "cpu"


def runtime_with_preferred_torch_device(runtime: dict[str, Any] | None, device: str | None = None) -> dict[str, Any]:
    enriched = dict(runtime or {})
    enriched.setdefault("torch_device", device or preferred_torch_device())
    return enriched
