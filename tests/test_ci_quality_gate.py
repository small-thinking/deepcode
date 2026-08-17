import unittest
from pathlib import Path

from deepcode.evaluators import get_evaluator
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]


class CiQualityGateTest(unittest.TestCase):
    def test_workflow_includes_repository_hygiene_gate(self):
        workflow = ROOT / ".github" / "workflows" / "tests.yml"
        text = workflow.read_text(encoding="utf-8")

        self.assertIn("name: Quality Gate", text)
        self.assertIn("concurrency:", text)
        self.assertIn("repository-hygiene:", text)
        self.assertIn("git diff --check", text)
        self.assertIn("git ls-files .DS_Store", text)
        self.assertIn("git check-attr filter -- docs/assets/deepcode-local-architecture.png", text)

    def test_problem_image_extensions_are_tracked_with_lfs(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

        self.assertIn("problems/**/assets/*.png filter=lfs", attributes)
        self.assertIn("problems/**/assets/*.jpg filter=lfs", attributes)
        self.assertIn("problems/**/assets/*.jpeg filter=lfs", attributes)

    def test_committed_problem_catalog_loads(self):
        store = ProblemStore(ROOT / "problems")
        problems = store.list_problems()

        self.assertGreaterEqual(len(problems), 3)
        for problem in problems:
            self.assertNotIn("tests", problem)
            self.assertNotIn("_runtime", problem)

            loaded = store.get_problem(problem["slug"])
            evaluation_type = loaded["evaluation"]["type"]
            if evaluation_type == "system_design":
                self.assertEqual(loaded["tests"], [])
                self.assertIn("reference_answer", loaded["response"])
                continue
            self.assertEqual(get_evaluator(evaluation_type).name, evaluation_type)
            self.assertGreaterEqual(len(loaded["tests"]), 1)
            for test in loaded["tests"]:
                self.assertIn("test", test)
                if evaluation_type == "ml_coding":
                    self.assertIn("expected_output", test)

    def test_local_user_state_and_data_directories_are_ignored(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(".deepcode/", gitignore)
        self.assertIn("data/", gitignore)
        self.assertIn("data/**", gitignore)
        self.assertIn("runs/", gitignore)
        self.assertIn("runs/**", gitignore)
        self.assertIn("problems/**/data", gitignore)
        self.assertIn("problems/**/data/**", gitignore)
        self.assertIn("problems/**/eval-results", gitignore)
        self.assertIn("problems/**/eval-results/**", gitignore)


if __name__ == "__main__":
    unittest.main()
