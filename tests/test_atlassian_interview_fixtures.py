import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/atlassian_interviews.py').read_text()
CODING = ['atlassian-streaming-moving-average', 'atlassian-tennis-court-assignment',
          'atlassian-commodity-price-checkpoints', 'atlassian-closest-common-group']
DESIGN = ['atlassian-cross-product-rag', 'atlassian-product-search', 'atlassian-work-log-agent',
          'atlassian-product-feed-recommendations', 'atlassian-search-answer-augmentation']


class AtlassianInterviewFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ProblemStore(ROOT / 'problems')

    def evaluate(self, slug, code=REFERENCE, case_name=None):
        p = self.store.get_problem(slug)
        cases = p['tests'] if case_name is None else [t for t in p['tests'] if case_name in t['name']]
        self.assertTrue(cases)
        return evaluate_submission(EvaluationRequest(code=code, problem=p, tests=cases,
            environment=p['environment'], runtime=p.get('_runtime', {})))

    def test_coding_references_pass_through_production_evaluator(self):
        for slug in CODING:
            with self.subTest(slug=slug):
                result = self.evaluate(slug)
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['passed'], len(self.store.get_problem(slug)['tests']))

    def test_design_exercises_have_written_answers_and_no_code_tests(self):
        for slug in DESIGN:
            with self.subTest(slug=slug):
                p = self.store.get_problem(slug)
                self.assertEqual(p['evaluation']['type'], 'system_design')
                self.assertFalse(p['tests'])
                self.assertNotIn('starter_code', p)
                self.assertTrue(p['response']['reference_answer'].strip())

    def test_weighted_average_case_rejects_uniform_weights(self):
        code = REFERENCE + '\nWeightedMovingAverage = MovingAverage\n'
        self.assertNotEqual(self.evaluate(CODING[0], code, 'Increasing weights')['status'], 'passed')

    def test_court_checks_accept_alternative_optimal_ids_and_reject_ignored_maintenance(self):
        code = REFERENCE + '\n_original_assign = assign_courts\ndef assign_courts(bookings, maintenance=0):\n    result = _original_assign(bookings, maintenance)\n    k = len(set(result))\n    return [k - 1 - court for court in result]\n'
        self.assertEqual(self.evaluate(CODING[1], code)['status'], 'passed')
        code = REFERENCE + '\n_original_assign = assign_courts\ndef assign_courts(bookings, maintenance=0):\n    return _original_assign(bookings, 0)\n'
        self.assertNotEqual(self.evaluate(CODING[1], code, 'changes the optimum')['status'], 'passed')

    def test_price_cases_reject_returning_latest_value_for_old_checkpoint(self):
        code = REFERENCE + '\nCommodityPrices.get_price = lambda self, timestamp, checkpoint: self.current.get(timestamp)\n'
        self.assertNotEqual(self.evaluate(CODING[2], code, 'Inclusive checkpoints')['status'], 'passed')

    def test_group_case_rejects_using_only_the_first_two_employees(self):
        code = REFERENCE + '\n_original_group = closest_common_group\ndef closest_common_group(parent, employee_groups, employees):\n    return _original_group(parent, employee_groups, employees[:2])\n'
        self.assertNotEqual(self.evaluate(CODING[3], code, 'later employee')['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
