import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / 'tests/reference_solutions/notion_nested_todo.py').read_text(encoding='utf-8')


class NotionNestedTodoFixtureTest(unittest.TestCase):
    def evaluate(self, code):
        problem = ProblemStore(ROOT / 'problems').get_problem('notion-nested-todo-list')
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem['tests'],
            environment=problem['environment'],
            runtime=problem.get('_runtime', {}),
        ))

    def test_reference_solution_passes_contract(self):
        result = self.evaluate(REFERENCE)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], 6, result)

    def test_unimplemented_starter_does_not_pass(self):
        problem = ProblemStore(ROOT / 'problems').get_problem('notion-nested-todo-list')
        result = self.evaluate(problem['starter_code'])
        self.assertNotEqual(result['status'], 'passed', result)
        self.assertEqual(result['passed'], 0, result)


if __name__ == '__main__':
    unittest.main()
