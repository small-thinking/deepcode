import heapq
import runpy
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUGS = (
    "blockwise-online-softmax-attention",
    "k-smallest-sorted-squares",
    "time-aware-task-management",
    "robot-charging-route",
)


def evaluate(slug, code):
    problem = ProblemStore(ROOT / "problems").get_problem(slug)
    return evaluate_submission(EvaluationRequest(
        code=code,
        problem=problem,
        tests=problem["tests"],
        environment=problem["environment"],
        runtime=problem.get("_runtime", {}),
    ))


def robot_route_oracle(grid):
    """Enumerate battery states for each capacity on small test grids."""
    rows, cols = len(grid), len(grid[0])
    start = next((r, c) for r in range(rows) for c in range(cols)
                 if grid[r][c] == "S")
    results = []
    for capacity in range(1, rows * cols + 1):
        queue = [(0, 0, *start, capacity)]
        best = {(*start, capacity): (0, 0)}
        while queue:
            charges, moves, r, c, battery = heapq.heappop(queue)
            if (charges, moves) != best[(r, c, battery)]:
                continue
            if grid[r][c] == "D":
                results.append((charges, capacity, moves))
                break
            if battery == 0:
                continue
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue
                symbol = grid[nr][nc]
                if symbol == "#":
                    continue
                next_battery = capacity if symbol == "C" else battery - 1
                next_cost = (charges + (symbol == "C"), moves + 1)
                state = (nr, nc, next_battery)
                if next_cost < best.get(state, (float("inf"), float("inf"))):
                    best[state] = next_cost
                    heapq.heappush(queue, (*next_cost, nr, nc, next_battery))
    return min(results) if results else -1


class RecentVerifiedCodingFixtures(unittest.TestCase):
    def test_reference_solutions_pass(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                path = next((ROOT / "problems").glob(f"*-{slug}"))
                result = evaluate(slug, (path / "solution.py").read_text())
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], result["total"], result)

    def test_attention_zero_output_is_rejected(self):
        code = """import numpy as np
def blockwise_attention(Q, K, V, block_size):
    return np.zeros((len(Q), len(V[0])))
"""
        result = evaluate("blockwise-online-softmax-attention", code)
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(any("AssertionError" in case["actual_output"]
                            for case in result["results"]), result)

    def test_squares_wrong_negative_order_is_rejected(self):
        code = """def k_smallest_squares(nums, k):
    return [x*x for x in nums[:k]]
"""
        result = evaluate("k-smallest-sorted-squares", code)
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(any("AssertionError" in case["actual_output"]
                            for case in result["results"]), result)

    def test_expiry_inclusive_boundary_is_rejected(self):
        path = next((ROOT / "problems").glob("*-time-aware-task-management"))
        code = (path / "solution.py").read_text()
        self.assertIn('t < assignment["finish"]', code)
        bad = code.replace('t < assignment["finish"]', 't <= assignment["finish"]')
        result = evaluate("time-aware-task-management", bad)
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(any("AssertionError" in case["actual_output"]
                            for case in result["results"]), result)

    def test_robot_route_matches_battery_state_oracle(self):
        path = next((ROOT / "problems").glob("*-robot-charging-route"))
        solution = runpy.run_path(str(path / "solution.py"))["optimal_route"]
        grids = [
            ["S.D"],
            ["S#D"],
            ["S.C.D"],
            ["S.C.D", "....."],
            ["S..#", ".C..", "##.D"],
            ["S.C..", ".#.#.", "..C.D"],
            ["S...##", ".C#.#.", "#.C..#", "...CC.", ".....D"],
        ]
        for grid in grids:
            with self.subTest(grid=grid):
                self.assertEqual(solution(grid), robot_route_oracle(grid))


if __name__ == "__main__":
    unittest.main()
