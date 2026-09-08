"""Contract checks: alternate legal implementations pass; representative mistakes fail."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMPY_REFERENCE = (ROOT / 'tests/reference_solutions/canva_datadog_luma_coding_gaps.py').read_text()
TORCH_REFERENCE = (ROOT / 'tests/reference_solutions/canva_datadog_luma_torch_coding_gaps.py').read_text()


def run_cases(directory, source):
    namespace = {}
    exec(compile(source, '<audit implementation>', 'exec'), namespace)
    failures = []
    cases = json.loads((ROOT / 'problems' / directory / 'tests.json').read_text())
    for case in cases:
        try:
            exec(compile(case['test'], case['name'], 'exec'), namespace.copy())
        except Exception as error:
            failures.append((case['name'], type(error).__name__))
    return failures


class MLQualityAuditFixtures(unittest.TestCase):
    def test_reference_implementations_pass_all_four_contracts(self):
        for directory, source in (
            ('366-binary-focal-loss', NUMPY_REFERENCE),
            ('367-grouped-query-attention', NUMPY_REFERENCE),
            ('371-diffusion-training-step-debug', TORCH_REFERENCE),
            ('372-image-crop-augmentations', NUMPY_REFERENCE),
        ):
            with self.subTest(directory=directory):
                self.assertEqual(run_cases(directory, source), [])

    def test_relu_and_functional_activation_are_legal(self):
        functional = '''
class TinyDenoiser(nn.Module):
    def __init__(self, channels, hidden_channels):
        super().__init__()
        self.first = nn.Conv2d(channels, hidden_channels, 1)
        self.second = nn.Conv2d(hidden_channels, channels, 1)
    def forward(self, images):
        return self.second(torch.relu(self.first(images)))
'''
        for source in (TORCH_REFERENCE.replace('nn.SiLU()', 'nn.ReLU()'), TORCH_REFERENCE + functional):
            with self.subTest(functional=source.endswith(functional)):
                self.assertEqual(run_cases('371-diffusion-training-step-debug', source), [])

    def test_crops_may_return_views_and_need_not_validate_invalid_inputs(self):
        # This implementation handles precisely the declared valid domain.
        # It intentionally has no dtype/shape/RNG error policy or copy requirement.
        source = '''
import numpy as np

def center_crop(image, crop_h, crop_w):
    top = (image.shape[0] - crop_h) // 2
    left = (image.shape[1] - crop_w) // 2
    return image[top:top + crop_h, left:left + crop_w]

def random_crop(image, crop_h, crop_w, rng):
    top = rng.integers(image.shape[0] - crop_h + 1)
    left = rng.integers(image.shape[1] - crop_w + 1)
    return image[top:top + crop_h, left:left + crop_w]

def random_crop_paste_on_white(image, crop_h, crop_w, rng):
    crop = random_crop(image, crop_h, crop_w, rng)
    white = 1 if np.issubdtype(image.dtype, np.floating) else np.iinfo(image.dtype).max
    result = np.full_like(image, white)
    top = rng.integers(image.shape[0] - crop_h + 1)
    left = rng.integers(image.shape[1] - crop_w + 1)
    for y in range(crop_h):
        for x in range(crop_w):
            result[top + y, left + x] = crop[y, x]
    return result
'''
        self.assertEqual(run_cases('372-image-crop-augmentations', source), [])

    def test_gqa_rejects_missing_scale_batch_leakage_and_query_broadcast(self):
        mutants = {
            'missing scale': NUMPY_REFERENCE.replace(' / math.sqrt(width)', ''),
            'first batch reused': NUMPY_REFERENCE + '''
_correct_gqa = grouped_query_attention
def grouped_query_attention(query, key, value):
    result = _correct_gqa(query, key, value)
    return np.repeat(result[:1], len(result), axis=0)
''',
            'first query token reused': NUMPY_REFERENCE + '''
_correct_gqa = grouped_query_attention
def grouped_query_attention(query, key, value):
    result = _correct_gqa(query, key, value)
    return np.repeat(result[:, :, :1], result.shape[2], axis=2)
''',
        }
        for name, source in mutants.items():
            with self.subTest(mutant=name):
                failures = run_cases('367-grouped-query-attention', source)
                self.assertIn(('scales feature dot products and keeps batches and query tokens separate', 'AssertionError'), failures)

    def test_diffusion_rejects_wrong_objective_mixing_and_updates(self):
        mutants = {
            'missing square roots': TORCH_REFERENCE.replace('alpha.sqrt() * clean + (1.0 - alpha).sqrt() * noise', 'alpha * clean + (1.0 - alpha) * noise'),
            'predict clean instead of noise': TORCH_REFERENCE.replace('(prediction - noise) ** 2', '(prediction - clean) ** 2'),
            'sum instead of mean': TORCH_REFERENCE.replace('torch.mean((prediction - noise)', 'torch.sum((prediction - noise)'),
            'stale gradients': TORCH_REFERENCE.replace('optimizer.zero_grad(set_to_none=True)', 'pass'),
            'step twice': TORCH_REFERENCE.replace('    optimizer.step()', '    optimizer.step()\n    optimizer.step()'),
            'no update': TORCH_REFERENCE.replace('    optimizer.step()', '    pass'),
        }
        for name, source in mutants.items():
            with self.subTest(mutant=name):
                failures = run_cases('371-diffusion-training-step-debug', source)
                self.assertIn(('normalizes and mixes inputs, predicts noise, and makes exactly one correct gradient update', 'AssertionError'), failures)

    def test_crop_rejects_excluded_last_origin_and_wrong_float_white(self):
        mutants = {
            'last origin excluded': NUMPY_REFERENCE.replace('rng.integers(height - crop_h + 1)', 'rng.integers(height - crop_h)').replace('rng.integers(width - crop_w + 1)', 'rng.integers(width - crop_w)'),
            'integer white for float images': NUMPY_REFERENCE.replace('canvas = np.ones(image.shape, dtype=image.dtype)', 'canvas = np.full(image.shape, 255.0, dtype=image.dtype)'),
        }
        for name, source in mutants.items():
            with self.subTest(mutant=name):
                self.assertTrue(run_cases('372-image-crop-augmentations', source))


if __name__ == '__main__':
    unittest.main()
