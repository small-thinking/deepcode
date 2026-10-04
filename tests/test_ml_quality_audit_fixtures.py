"""Contract checks: alternate legal implementations pass; representative mistakes fail."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMPY_REFERENCE = (ROOT / 'tests/reference_solutions/canva_datadog_luma_coding_gaps.py').read_text()


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
    def test_reference_implementations_pass_remaining_contracts(self):
        for directory, source in (
            ('366-binary-focal-loss', NUMPY_REFERENCE),
            ('367-grouped-query-attention', NUMPY_REFERENCE),
        ):
            with self.subTest(directory=directory):
                self.assertEqual(run_cases(directory, source), [])


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


if __name__ == '__main__':
    unittest.main()
