#!/usr/bin/env python
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import struct
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import torch


DEFAULT_BASE_URL = "https://storage.googleapis.com/cvdf-datasets/mnist"
MNIST_FILES = {
    "train_images": "train-images-idx3-ubyte.gz",
    "train_labels": "train-labels-idx1-ubyte.gz",
    "val_images": "t10k-images-idx3-ubyte.gz",
    "val_labels": "t10k-labels-idx1-ubyte.gz",
}


def prepare_mnist(
    base_url: str = DEFAULT_BASE_URL,
    output_dir: str | Path = "data/mnist",
    train_size: int = 2048,
    val_size: int = 512,
    raw_dir: str | Path | None = None,
    force: bool = False,
) -> dict[str, int | str]:
    output_path = Path(output_dir)
    raw_path = Path(raw_dir) if raw_dir is not None else output_path / "raw"
    output_path.mkdir(parents=True, exist_ok=True)
    raw_path.mkdir(parents=True, exist_ok=True)

    local_files = {
        key: fetch_mnist_file(base_url=base_url, filename=filename, raw_dir=raw_path, force=force)
        for key, filename in MNIST_FILES.items()
    }

    train_images = read_idx_images(local_files["train_images"])[:train_size].clone()
    train_labels = read_idx_labels(local_files["train_labels"])[:train_size].clone()
    val_images = read_idx_images(local_files["val_images"])[:val_size].clone()
    val_labels = read_idx_labels(local_files["val_labels"])[:val_size].clone()

    torch.save({"images": train_images, "labels": train_labels}, output_path / "train.pt")
    torch.save({"images": val_images, "labels": val_labels}, output_path / "val.pt")

    summary: dict[str, int | str] = {
        "source": str(base_url),
        "output_dir": str(output_path),
        "train_examples": int(train_labels.numel()),
        "val_examples": int(val_labels.numel()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_path / "metadata.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def fetch_mnist_file(base_url: str, filename: str, raw_dir: Path, force: bool = False) -> Path:
    destination = raw_dir / filename
    if destination.exists() and not force:
        return destination

    source = _resolve_source(base_url, filename)
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https", "file"}:
        with urllib.request.urlopen(source) as response:
            _copy_stream(response, destination)
        return destination

    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"MNIST source file not found: {source_path}")
    shutil.copyfile(source_path, destination)
    return destination


def read_idx_images(path: str | Path) -> torch.Tensor:
    with _open_maybe_gzip(path) as file:
        magic, count, rows, cols = struct.unpack(">IIII", _read_exact(file, 16))
        if magic != 2051:
            raise ValueError(f"{path} is not an IDX image file")
        payload = _read_exact(file, count * rows * cols)

    images = torch.frombuffer(bytearray(payload), dtype=torch.uint8)
    return images.reshape(count, 1, rows, cols).to(dtype=torch.float32) / 255.0


def read_idx_labels(path: str | Path) -> torch.Tensor:
    with _open_maybe_gzip(path) as file:
        magic, count = struct.unpack(">II", _read_exact(file, 8))
        if magic != 2049:
            raise ValueError(f"{path} is not an IDX label file")
        payload = _read_exact(file, count)

    return torch.frombuffer(bytearray(payload), dtype=torch.uint8).to(dtype=torch.long)


def _resolve_source(base_url: str, filename: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme in {"http", "https", "file"}:
        return urllib.parse.urljoin(base_url.rstrip("/") + "/", filename)
    return str(Path(base_url) / filename)


def _copy_stream(source: BinaryIO, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as file:
        shutil.copyfileobj(source, file)


def _open_maybe_gzip(path: str | Path):
    file_path = Path(path)
    if file_path.suffix == ".gz":
        return gzip.open(file_path, "rb")
    return file_path.open("rb")


def _read_exact(file, size: int) -> bytes:
    payload = file.read(size)
    if len(payload) != size:
        raise ValueError("IDX file ended unexpectedly")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and prepare a small local MNIST torch dataset.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="MNIST gzip URL prefix or local directory.")
    parser.add_argument("--output", default="data/mnist", help="Directory for train.pt, val.pt, and metadata.json.")
    parser.add_argument("--raw-dir", default=None, help="Optional directory for raw IDX gzip files.")
    parser.add_argument("--train-size", type=int, default=2048, help="Number of train examples to save.")
    parser.add_argument("--val-size", type=int, default=512, help="Number of validation examples to save.")
    parser.add_argument("--force", action="store_true", help="Re-copy or re-download raw gzip files.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = prepare_mnist(
        base_url=args.base_url,
        output_dir=args.output,
        train_size=args.train_size,
        val_size=args.val_size,
        raw_dir=args.raw_dir,
        force=args.force,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
