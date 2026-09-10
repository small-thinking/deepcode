"""Exercise reference code and meaningful error variants through the real runner."""
import itertools
import runpy
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / 'tests/reference_solutions/coding_quality_20260908.py'
REFERENCE = REFERENCE_PATH.read_text()


class CodingQualityAuditTest(unittest.TestCase):
    def evaluate(self, slug, code=REFERENCE, case_index=None):
        problem = ProblemStore(ROOT / 'problems').get_problem(slug)
        cases = problem['tests'] if case_index is None else [problem['tests'][case_index]]
        return evaluate_submission(EvaluationRequest(code=code, problem=problem, tests=cases,
            environment=problem['environment'], runtime=problem.get('_runtime', {})))

    def test_correct_references_pass_all_visible_cases(self):
        for slug in ('serpentine-matrix-traversal', 'minimum-listing-count-capacity',
                     'unit-time-deadline-reward-schedule'):
            with self.subTest(slug=slug):
                result = self.evaluate(slug)
                self.assertEqual(result['status'], 'passed', result)

    def test_listing_reference_matches_independent_capacity_dp(self):
        select = runpy.run_path(str(REFERENCE_PATH))['select_group_listings']
        # DP stores the best index tuple for each (count, capacity), independently
        # of the reference's subset-size enumeration. Include zero and tied values.
        for capacities in itertools.product((0, 2, 3), repeat=4):
            listings = [dict(id=str(i), neighborhood='n', capacity=c) for i, c in enumerate(capacities)]
            states = {(0, 0): ()}
            for index, capacity in enumerate(capacities):
                for (count, total), indices in list(states.items()):
                    key = (count + 1, total + capacity)
                    candidate = indices + (index,)
                    states[key] = min(states.get(key, candidate), candidate)
            for target in (1, 4, 7):
                feasible = [(count, total, indices) for (count, total), indices in states.items() if total >= target]
                expected = [str(i) for i in min(feasible)[2]] if feasible else []
                self.assertEqual(select(listings, target, 'n'), expected)

    def test_schedule_reward_matches_exhaustive_feasible_orders(self):
        schedule = runpy.run_path(str(REFERENCE_PATH))['deadline_reward_schedule']
        for deadlines in itertools.product((1, 2, 4), repeat=3):
            tasks = [(str(i), d, r) for i, (d, r) in enumerate(zip(deadlines, (2, 5, 5)))]
            optimal = max(sum(task[2] for task in order)
                          for count in range(4) for order in itertools.permutations(tasks, count)
                          if all(day <= task[1] for day, task in enumerate(order, 1)))
            order, reward = schedule(tasks)
            by_id = {task_id: (deadline, task_reward) for task_id, deadline, task_reward in tasks}
            self.assertEqual(reward, optimal)
            self.assertEqual(reward, sum(by_id[task_id][1] for task_id in order))
            self.assertTrue(all(day <= by_id[task_id][0] for day, task_id in enumerate(order, 1)))

    def test_visible_cases_reject_typical_wrong_implementations(self):
        variants = [
            ('serpentine-matrix-traversal', 2, '''
def zigzag_matrix_rows(matrix):
    for row in matrix[1::2]:
        row.reverse()
    return [value for row in matrix for value in row]
'''),
            ('minimum-listing-count-capacity', 3, '''
def select_group_listings(listings, group_size, neighborhood):
    candidates = sorted((x for x in listings if x['neighborhood'] == neighborhood), key=lambda x: -x['capacity'])
    chosen, total = [], 0
    for item in candidates:
        chosen.append(item['id'])
        total += item['capacity']
        if total >= group_size:
            return [item['id'] for item in listings if item['id'] in chosen]
    return []
'''),
            ('minimum-listing-count-capacity', 4, '''
_original_select = select_group_listings
def select_group_listings(listings, group_size, neighborhood):
    return _original_select(sorted(listings, key=lambda x: x['id']), group_size, neighborhood)
'''),
            ('unit-time-deadline-reward-schedule', 0, '''
def deadline_reward_schedule(tasks):
    ordered = sorted(tasks, key=lambda task: task[1])
    selected = []
    for task in ordered:
        if len(selected) < task[1]:
            selected.append(task)
    return [task_id for task_id, _, _ in selected], sum(reward for _, _, reward in selected)
'''),
        ]
        for slug, index, mutation in variants:
            with self.subTest(slug=slug, case=index):
                result = self.evaluate(slug, REFERENCE + mutation, index)
                self.assertEqual(result['passed'], 0, result)
                self.assertEqual(result['status'], 'failed', result)


if __name__ == '__main__':
    unittest.main()
