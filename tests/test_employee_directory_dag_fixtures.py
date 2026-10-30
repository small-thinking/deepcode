import random
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests/reference_solutions/employee_directory_dag.py").read_text()


class EmployeeDirectoryDagFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("employee-directory-dag")

    def evaluate(self, code, case_name=None):
        cases = self.problem["tests"]
        if case_name is not None:
            cases = [case for case in cases if case_name in case["name"]]
        self.assertTrue(cases)
        return evaluate_submission(EvaluationRequest(
            code=code, problem=self.problem, tests=cases,
            environment=self.problem["environment"], runtime=self.problem.get("_runtime", {}),
        ))

    def test_reference_passes_visible_contract(self):
        result = self.evaluate(REFERENCE)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(self.problem["tests"]), result)

    def test_starter_does_not_pass(self):
        self.assertEqual(self.evaluate(self.problem["starter_code"])["passed"], 0)

    def test_visible_cases_reject_common_dag_mistakes(self):
        mutations = [
            ("Incomparable", "return common - non_lowest", "return set(list(common - non_lowest)[:1])"),
            ("Transitive", "return common - non_lowest", "return common"),
            ("Later employee", "employees[1:]", "employees[1:2]"),
            ("Shared paths", "stack = list(employee.parents)", "stack = list(employee.parents[:1])"),
            ("Identity", "return common - non_lowest", "return {node.name for node in common - non_lowest}"),
        ]
        for case_name, old, new in mutations:
            with self.subTest(case=case_name):
                result = self.evaluate(REFERENCE.replace(old, new), case_name)
                self.assertNotEqual(result["status"], "passed", result)

    def test_reference_matches_downward_reachability_oracle(self):
        namespace = {}
        exec(REFERENCE, namespace)
        Node = namespace["Node"]
        solve = namespace["closest_common_groups"]
        rng = random.Random(41)
        for _ in range(40):
            groups = [Node(str(i)) for i in range(8)]
            for index, group in enumerate(groups):
                group.parents = [parent for parent in groups[:index] if rng.random() < 0.35]
            employees = [Node("employee", [g for g in groups if rng.random() < 0.4]) for _ in range(3)]
            nodes = groups + employees
            children = {node: [] for node in nodes}
            for node in nodes:
                for parent in node.parents:
                    children[parent].append(node)
            descendants = {}
            for node in reversed(nodes):
                descendants[node] = {node}
                for child in children[node]:
                    descendants[node].update(descendants[child])
            common = {g for g in groups if set(employees) <= descendants[g]}
            expected = {g for g in common if not (descendants[g] - {g}) & common}
            with self.subTest(parents=[[nodes.index(p) for p in n.parents] for n in nodes]):
                self.assertEqual(solve(employees), expected)


if __name__ == "__main__":
    unittest.main()
