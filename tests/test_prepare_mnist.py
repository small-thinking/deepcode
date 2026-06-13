import gzip
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_mnist.py"


def _load_prepare_mnist():
    spec = importlib.util.spec_from_file_location("prepare_mnist", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_idx_images(path: Path, count: int, rows: int, cols: int, values: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as file:
        file.write(struct.pack(">IIII", 2051, count, rows, cols))
        file.write(bytes(values))


def _write_idx_labels(path: Path, labels: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as file:
        file.write(struct.pack(">II", 2049, len(labels)))
        file.write(bytes(labels))


def _storage_nbytes(tensor: torch.Tensor) -> int:
    return tensor.untyped_storage().nbytes()


class PrepareMnistTest(unittest.TestCase):
    def test_reads_idx_gzip_images_and_labels(self):
        prepare_mnist = _load_prepare_mnist()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            images_path = root / "images.gz"
            labels_path = root / "labels.gz"
            _write_idx_images(images_path, count=2, rows=2, cols=2, values=[0, 255, 128, 64, 1, 2, 3, 4])
            _write_idx_labels(labels_path, [7, 3])

            images = prepare_mnist.read_idx_images(images_path)
            labels = prepare_mnist.read_idx_labels(labels_path)

        self.assertEqual(tuple(images.shape), (2, 1, 2, 2))
        self.assertEqual(images.dtype, torch.float32)
        self.assertAlmostEqual(float(images[0, 0, 0, 1]), 1.0)
        self.assertEqual(labels.tolist(), [7, 3])
        self.assertEqual(labels.dtype, torch.long)

    def test_prepare_mnist_from_local_source_writes_tensor_files(self):
        prepare_mnist = _load_prepare_mnist()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source"
            output_dir = root / "output"
            _write_idx_images(
                source_dir / "train-images-idx3-ubyte.gz",
                count=3,
                rows=2,
                cols=2,
                values=[0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23],
            )
            _write_idx_labels(source_dir / "train-labels-idx1-ubyte.gz", [0, 1, 2])
            _write_idx_images(
                source_dir / "t10k-images-idx3-ubyte.gz",
                count=2,
                rows=2,
                cols=2,
                values=[30, 31, 32, 33, 40, 41, 42, 43],
            )
            _write_idx_labels(source_dir / "t10k-labels-idx1-ubyte.gz", [3, 4])

            summary = prepare_mnist.prepare_mnist(
                base_url=str(source_dir),
                output_dir=output_dir,
                train_size=2,
                val_size=1,
            )
            train = torch.load(output_dir / "train.pt", weights_only=True)
            val = torch.load(output_dir / "val.pt", weights_only=True)
            metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["train_examples"], 2)
        self.assertEqual(summary["val_examples"], 1)
        self.assertEqual(tuple(train["images"].shape), (2, 1, 2, 2))
        self.assertEqual(_storage_nbytes(train["images"]), train["images"].numel() * train["images"].element_size())
        self.assertEqual(train["labels"].tolist(), [0, 1])
        self.assertEqual(tuple(val["images"].shape), (1, 1, 2, 2))
        self.assertEqual(_storage_nbytes(val["images"]), val["images"].numel() * val["images"].element_size())
        self.assertEqual(val["labels"].tolist(), [3])
        self.assertEqual(metadata["source"], str(source_dir))


if __name__ == "__main__":
    unittest.main()
