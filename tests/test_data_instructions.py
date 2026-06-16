import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "problems"


def _dataset_backed_problems():
    for problem_path in sorted(PROBLEMS.glob("*/problem.json")):
        problem = json.loads(problem_path.read_text(encoding="utf-8"))
        if problem.get("data", {}).get("path"):
            yield problem_path, problem


class DataInstructionTest(unittest.TestCase):
    def test_dataset_backed_prompts_do_not_embed_local_data_setup(self):
        forbidden_prompt_fragments = [
            "DEEPCODE_DATA_PATH",
            "DEEPCODE_RESULTS_PATH",
            "link this problem",
            "Prepare the local data",
        ]

        for problem_path, problem in _dataset_backed_problems():
            with self.subTest(problem=problem_path.parent.name):
                prompt = problem["prompt"]
                for fragment in forbidden_prompt_fragments:
                    self.assertNotIn(fragment, prompt)

    def test_dataset_backed_problems_describe_local_data_separately(self):
        for problem_path, problem in _dataset_backed_problems():
            with self.subTest(problem=problem_path.parent.name):
                data = problem["data"]
                self.assertIn("path", data)
                self.assertIn("format", data)
                self.assertTrue(any(data.get(key) for key in ("note", "setup", "runtime")))
                for key in ("note", "setup", "runtime"):
                    if data.get(key):
                        self.assertLessEqual(len(data[key]), 160)

    def test_ngram_starter_code_carries_alpha_and_dataset_hint(self):
        problem = json.loads((PROBLEMS / "101-ngram-next-character-model" / "problem.json").read_text(encoding="utf-8"))
        starter_code = problem["starter_code"]

        self.assertIn("def __init__(self, n=3, alpha=0.1):", starter_code)
        self.assertIn("self.alpha = alpha", starter_code)
        self.assertIn("DEEPCODE_DATA_PATH/tiny_shakespeare.txt", starter_code)

    def test_ngram_prompt_is_interview_sized(self):
        problem = json.loads((PROBLEMS / "101-ngram-next-character-model" / "problem.json").read_text(encoding="utf-8"))

        self.assertLessEqual(len(problem["prompt"]), 900)
        self.assertNotIn("tiny_shakespeare", problem["prompt"])


if __name__ == "__main__":
    unittest.main()
