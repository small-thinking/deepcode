import unittest
from types import SimpleNamespace
from unittest.mock import patch


class TorchDeviceTest(unittest.TestCase):
    def test_prefers_cuda_when_available(self):
        from deepcode.evaluators.torch_device import preferred_torch_device

        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: True),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: True)),
        )

        with patch("deepcode.evaluators.torch_device.torch", fake_torch):
            self.assertEqual(preferred_torch_device(), "cuda")

    def test_uses_mps_when_cuda_is_not_available(self):
        from deepcode.evaluators.torch_device import preferred_torch_device

        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: False),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: True)),
        )

        with patch("deepcode.evaluators.torch_device.torch", fake_torch):
            self.assertEqual(preferred_torch_device(), "mps")

    def test_falls_back_to_cpu_when_no_accelerator_is_available(self):
        from deepcode.evaluators.torch_device import preferred_torch_device

        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: False),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
        )

        with patch("deepcode.evaluators.torch_device.torch", fake_torch):
            self.assertEqual(preferred_torch_device(), "cpu")

    def test_falls_back_to_cpu_when_mps_backend_is_missing(self):
        from deepcode.evaluators.torch_device import preferred_torch_device

        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: False),
            backends=SimpleNamespace(),
        )

        with patch("deepcode.evaluators.torch_device.torch", fake_torch):
            self.assertEqual(preferred_torch_device(), "cpu")

    def test_adds_preferred_device_without_mutating_runtime(self):
        from deepcode.evaluators.torch_device import runtime_with_preferred_torch_device

        runtime = {"data_path": "/tmp/data"}

        with patch("deepcode.evaluators.torch_device.preferred_torch_device", return_value="mps"):
            enriched = runtime_with_preferred_torch_device(runtime)

        self.assertEqual(enriched["torch_device"], "mps")
        self.assertEqual(enriched["data_path"], "/tmp/data")
        self.assertNotIn("torch_device", runtime)


if __name__ == "__main__":
    unittest.main()
