import ast
import itertools
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]


class AlienDictionaryFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem("alien-dictionary-order")

    def accepts(self, case, output):
        try:
            exec(case["test"], {"alien_order": lambda words: output})
        except AssertionError:
            return False
        return True

    def test_small_cases_accept_exactly_the_alphabets_that_sort_the_words(self):
        # An independent oracle compares whole encoded words, without building
        # a precedence graph or relying on the reference solution's tie breaks.
        for case in self.problem["tests"]:
            words = ast.literal_eval(case["input"])
            characters = sorted(set("".join(words)))
            if len(characters) > 6:
                continue
            valid_orders = []
            for permutation in itertools.permutations(characters):
                order = "".join(permutation)
                rank = {char: index for index, char in enumerate(order)}
                encoded = [tuple(rank[char] for char in word) for word in words]
                valid = encoded == sorted(encoded)
                with self.subTest(case=case["name"], order=order):
                    self.assertEqual(self.accepts(case, order), valid)
                if valid:
                    valid_orders.append(order)
            with self.subTest(case=case["name"], order=""):
                self.assertEqual(self.accepts(case, ""), not valid_orders)

    def test_rejects_missing_repeated_extra_characters_and_non_string_orders(self):
        for case in self.problem["tests"]:
            words = ast.literal_eval(case["input"])
            characters = "".join(sorted(set("".join(words))))
            invalid_outputs = [
                characters[:-1],
                characters + characters[0],
                characters + "!",
                list(characters),
                None,
            ]
            for output in invalid_outputs:
                with self.subTest(case=case["name"], output=output):
                    self.assertFalse(self.accepts(case, output))

    def test_alternative_valid_orders_pass_the_real_evaluator(self):
        # DFS yields different valid orders from the heap-based reference,
        # especially for isolated characters and disconnected components.
        code = '''
def alien_order(words):
    graph = {char: set() for word in words for char in word}
    for first, second in zip(words, words[1:]):
        for left, right in zip(first, second):
            if left != right:
                graph[left].add(right)
                break
        else:
            if len(first) > len(second):
                return ""
    state = {}
    postorder = []

    def visit(char):
        if state.get(char) == 1:
            return False
        if state.get(char) == 2:
            return True
        state[char] = 1
        for neighbor in sorted(graph[char]):
            if not visit(neighbor):
                return False
        state[char] = 2
        postorder.append(char)
        return True

    for char in sorted(graph):
        if not visit(char):
            return ""
    return "".join(reversed(postorder))
'''
        result = evaluate_submission(
            EvaluationRequest(
                code=code,
                problem=self.problem,
                tests=self.problem["tests"],
                environment=self.problem["environment"],
                runtime=self.problem.get("_runtime", {}),
            )
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(self.problem["tests"]))


if __name__ == "__main__":
    unittest.main()
