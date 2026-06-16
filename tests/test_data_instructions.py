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
                self.assertIn("setup", data)
                self.assertIn("runtime", data)
                self.assertIn("DEEPCODE_DATA_PATH", data["runtime"])


if __name__ == "__main__":
    unittest.main()
