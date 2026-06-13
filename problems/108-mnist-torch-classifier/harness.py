import json
import os
import random
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


MIN_ACCURACY = 0.70
EPOCHS = 2
BATCH_SIZE = 128


def _runtime_path(env_name: str) -> Path:
    value = os.environ.get(env_name)
    assert value, f"{env_name} is not set"
    return Path(value)


def _load_split(path: Path) -> tuple[torch.Tensor, torch.Tensor]:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(payload, dict):
        images = payload["images"]
        labels = payload["labels"]
    else:
        images, labels = payload

    images = images.to(dtype=torch.float32)
    if images.numel() and float(images.max()) > 1.0:
        images = images / 255.0
    if images.ndim == 3:
        images = images.unsqueeze(1)
    labels = labels.to(dtype=torch.long)
    return images.contiguous(), labels.contiguous()


def _accuracy(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            predictions = model(images).argmax(dim=1)
            correct += int((predictions == labels).sum().item())
            total += int(labels.numel())
    return correct / max(total, 1)


torch.manual_seed(0)
random.seed(0)

data_path = _runtime_path("DEEPCODE_DATA_PATH")
train_images, train_labels = _load_split(data_path / "train.pt")
val_images, val_labels = _load_split(data_path / "val.pt")

generator = torch.Generator().manual_seed(0)
train_loader = DataLoader(
    TensorDataset(train_images, train_labels),
    batch_size=BATCH_SIZE,
    shuffle=True,
    generator=generator,
)
val_loader = DataLoader(TensorDataset(val_images, val_labels), batch_size=BATCH_SIZE, shuffle=False)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"dataset: train={len(train_labels)} val={len(val_labels)}")
print(f"device: {device}")

model = build_model()
assert isinstance(model, nn.Module), "build_model() must return torch.nn.Module"
model.to(device)

trained = train_model(model, train_loader, val_loader, epochs=EPOCHS, device=device)
if trained is not None:
    model = trained
assert isinstance(model, nn.Module), "train_model() must return None or torch.nn.Module"
model.to(device)

val_accuracy = _accuracy(model, val_loader, device)
print(f"metric: val_accuracy={val_accuracy:.4f}")

results_path = os.environ.get("DEEPCODE_RESULTS_PATH")
if results_path:
    output_dir = Path(results_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(
        json.dumps(
            {
                "val_accuracy": val_accuracy,
                "threshold": MIN_ACCURACY,
                "train_examples": int(train_labels.numel()),
                "val_examples": int(val_labels.numel()),
                "device": str(device),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

assert val_accuracy >= MIN_ACCURACY, f"expected val_accuracy >= {MIN_ACCURACY:.2f}, got {val_accuracy:.4f}"
print("Metric threshold met")
