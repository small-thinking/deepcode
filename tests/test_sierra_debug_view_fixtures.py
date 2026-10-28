import random
import unittest
from copy import deepcopy
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests/reference_solutions/sierra_debug_view.py").read_text()


class SierraDebugViewFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("sierra-debug-view")

    def evaluate(self, code, cases=None):
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=self.problem,
            tests=self.problem["tests"] if cases is None else cases,
            environment=self.problem["environment"],
            runtime=self.problem.get("_runtime", {}),
        ))

    def test_reference_passes_all_visible_cases(self):
        result = self.evaluate(REFERENCE)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(self.problem["tests"]))

    def test_overlap_alone_is_not_an_interruption(self):
        # The supplied study file's overlap-and-clip shortcut can set an
        # agent's end before its start when a user was already speaking.
        code = REFERENCE + '''
def mark_interruptions(chunks):
    result = []
    for chunk in chunks:
        item = dict(chunk, interrupted=False)
        if item["role"] == "agent":
            for user in chunks:
                if (user["role"] == "user" and item["start"] < user["end"]
                        and user["start"] < item["end"]):
                    item["end"] = user["start"]
                    item["text"] += " ... [INTERRUPTED]"
                    item["interrupted"] = True
                    break
        result.append(item)
    return result
'''
        case = next(t for t in self.problem["tests"] if "Already speaking" in t["name"])
        self.assertNotEqual(self.evaluate(code, [case])["status"], "passed")

    def test_sorting_without_interval_merging_is_insufficient(self):
        code = REFERENCE + '''
def merge_chunks(agent_chunks, user_chunks, tool_chunks):
    priority = {"user": 0, "agent": 1, "tool": 2}
    items = [dict(role=role, start=s, end=e, text=t)
             for role, chunks in [("agent", agent_chunks), ("user", user_chunks), ("tool", tool_chunks)]
             for s, e, t in chunks]
    return sorted(items, key=lambda item: (item["start"], priority[item["role"]]))
'''
        case = next(t for t in self.problem["tests"] if "Unsorted and touching" in t["name"])
        self.assertNotEqual(self.evaluate(code, [case])["status"], "passed")

    def test_median_must_use_only_inserted_gaps(self):
        code = REFERENCE + '''
def thinking_time_p50(chunks):
    durations = sorted(chunk["end"] - chunk["start"] for chunk in chunks)
    n = len(durations)
    return durations[n // 2] if n else 0
'''
        case = next(t for t in self.problem["tests"] if "Even median" in t["name"])
        self.assertNotEqual(self.evaluate(code, [case])["status"], "passed")

    def test_interruption_matches_direct_search_on_random_timelines(self):
        namespace = {}
        exec(REFERENCE, namespace)
        rng = random.Random(527)
        for _ in range(150):
            inputs = []
            for _role in range(3):
                intervals = []
                for _chunk in range(rng.randrange(8)):
                    start = rng.randrange(30)
                    intervals.append((start, start + rng.randrange(1, 12), "text"))
                inputs.append(intervals)
            merged = namespace["merge_chunks"](*inputs)
            before = deepcopy(merged)
            marked = namespace["mark_interruptions"](merged)
            for original, actual in zip(merged, marked):
                candidates = [
                    user["start"] for user in merged
                    if original["role"] == "agent" and user["role"] == "user"
                    and original["start"] < user["start"] < original["end"]
                ]
                self.assertEqual(actual["interrupted"], bool(candidates))
                self.assertEqual(actual["end"], min(candidates) if candidates else original["end"])
                self.assertGreater(actual["end"], actual["start"])
            self.assertEqual(merged, before)


if __name__ == "__main__":
    unittest.main()
