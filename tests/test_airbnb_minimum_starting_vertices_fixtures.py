import itertools
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "airbnb_minimum_starting_vertices.py"
).read_text(encoding="utf-8")


def brute_force_minimum(n, edges):
    outgoing = [[] for _ in range(n)]
    for source, target in edges:
        outgoing[source].append(target)
    for size in range(n + 1):
        for starts in itertools.combinations(range(n), size):
            reached = set(starts)
            pending = list(starts)
            while pending:
                for neighbor in outgoing[pending.pop()]:
                    if neighbor not in reached:
                        reached.add(neighbor)
                        pending.append(neighbor)
            if len(reached) == n:
                return size


class AirbnbMinimumStartingVerticesFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_visible_cases(self):
        problem = ProblemStore(ROOT / "problems").get_problem("minimum-starting-vertices")
        result = evaluate_submission(
            EvaluationRequest(
                code=REFERENCE_SOLUTION,
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_all_three_vertex_graphs_match_exhaustive_start_sets(self):
        namespace = {}
        exec(REFERENCE_SOLUTION, namespace)
        solve = namespace["minimum_starting_vertices"]
        possible_edges = list(itertools.product(range(3), repeat=2))
        for mask in range(1 << len(possible_edges)):
            edges = [edge for bit, edge in enumerate(possible_edges) if mask & (1 << bit)]
            with self.subTest(edges=edges):
                self.assertEqual(solve(3, edges), brute_force_minimum(3, edges))

    def test_visible_cases_reject_vertex_indegree_and_traversal_order_shortcuts(self):
        problem = ProblemStore(ROOT / "problems").get_problem("minimum-starting-vertices")
        shortcuts = [
            "def minimum_starting_vertices(n, edges):\n"
            "    return n - len({target for source, target in edges})\n",
            "def minimum_starting_vertices(n, edges):\n"
            "    graph = [[] for _ in range(n)]\n"
            "    for source, target in edges: graph[source].append(target)\n"
            "    visited = set()\n"
            "    count = 0\n"
            "    for start in range(n):\n"
            "        if start in visited: continue\n"
            "        count += 1\n"
            "        pending = [start]\n"
            "        while pending:\n"
            "            node = pending.pop()\n"
            "            if node in visited: continue\n"
            "            visited.add(node)\n"
            "            pending.extend(graph[node])\n"
            "    return count\n",
        ]
        for shortcut in shortcuts:
            rejected = False
            for case in problem["tests"]:
                try:
                    exec(shortcut + "\n" + case["test"], {})
                except AssertionError:
                    rejected = True
                    break
            self.assertTrue(rejected, shortcut)


if __name__ == "__main__":
    unittest.main()
