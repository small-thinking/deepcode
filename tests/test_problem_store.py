import json
import os
import tempfile
import unittest
from pathlib import Path

from deepcode.problem_store import ProblemStore


class ProblemStoreTest(unittest.TestCase):
    def test_loads_problem_folders_and_sorts_by_numeric_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "mean-prediction",
                {
                    "id": "20",
                    "slug": "mean-prediction",
                    "title": "Mean Prediction",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["baseline"],
                    "prompt": "Return the mean.",
                    "starter_code": "def predict_mean(values):\n    pass\n",
                    "example": {
                        "input": "values = [1, 2, 3]",
                        "output": "2.0",
                        "reasoning": "The arithmetic mean is 2.",
                    },
                    "environment": {
                        "language": "python",
                        "timeout_seconds": 2,
                        "packages": [],
                        "comparator": "numeric",
                    },
                },
                [{"name": "basic", "test": "print(predict_mean([1, 2, 3]))", "expected_output": "2.0"}],
            )
            self._write_problem(
                root,
                "dot-product",
                {
                    "id": "3",
                    "slug": "dot-product",
                    "title": "Dot Product",
                    "category": "Linear Algebra",
                    "difficulty": "medium",
                    "tags": ["vectors"],
                    "prompt": "Return a dot product.",
                    "starter_code": "def dot_product(a, b):\n    pass\n",
                    "example": {
                        "input": "a = [1, 2], b = [3, 4]",
                        "output": "11",
                        "reasoning": "1 * 3 + 2 * 4 = 11.",
                    },
                    "environment": {
                        "language": "python",
                        "timeout_seconds": 2,
                        "packages": [],
                        "comparator": "exact",
                    },
                },
                [{"name": "basic", "test": "print(dot_product([1, 2], [3, 4]))", "expected_output": "11"}],
            )

            store = ProblemStore(root)

            self.assertEqual([problem["id"] for problem in store.list_problems()], ["3", "20"])
            self.assertEqual([problem["display_id"] for problem in store.list_problems()], [1, 2])
            self.assertEqual(
                [problem["id"] for problem in store.list_problems(sort="id", order="desc")], ["20", "3"]
            )
            self.assertEqual(
                [problem["id"] for problem in store.list_problems(sort="title", order="desc")], ["20", "3"]
            )
            self.assertEqual(
                [problem["id"] for problem in store.list_problems(sort="difficulty")], ["20", "3"]
            )
            self.assertEqual(
                [problem["id"] for problem in store.list_problems(sort="difficulty", order="desc")], ["3", "20"]
            )
            self.assertEqual(store.categories(), ["Linear Algebra", "Machine Learning"])
            self.assertEqual(store.get_problem("mean-prediction")["tests"][0]["name"], "basic")
            self.assertEqual(store.get_problem("20")["slug"], "mean-prediction")
            self.assertEqual(store.get_problem("20")["display_id"], 2)

    def test_filters_problem_list_by_category_difficulty_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "linear-regression",
                {
                    "id": "14",
                    "slug": "linear-regression",
                    "title": "Linear Regression Baseline",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["regression"],
                    "prompt": "Fit a line.",
                    "starter_code": "def fit_baseline(x, y):\n    pass\n",
                    "example": {"input": "x = [1]", "output": "1", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                },
                [{"name": "basic", "test": "print(fit_baseline([1], [1]))", "expected_output": "1"}],
            )
            self._write_problem(
                root,
                "matrix-dot",
                {
                    "id": "1",
                    "slug": "matrix-dot",
                    "title": "Matrix Dot",
                    "category": "Linear Algebra",
                    "difficulty": "easy",
                    "tags": ["matrix"],
                    "prompt": "Multiply.",
                    "starter_code": "def matrix_dot(a, b):\n    pass\n",
                    "example": {"input": "a = [[1]], b = [2]", "output": "[2]", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                },
                [{"name": "basic", "test": "print(matrix_dot([[1]], [2]))", "expected_output": "[2]"}],
            )

            store = ProblemStore(root)

            filtered = store.list_problems(category="Machine Learning", difficulty="easy", search="baseline")

            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["slug"], "linear-regression")
            self.assertNotIn("tests", filtered[0])
            self.assertNotIn("starter_code", filtered[0])

    def test_includes_reference_links_in_problem_summaries_and_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "with-links",
                {
                    "id": "8",
                    "slug": "with-links",
                    "title": "With Links",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["links"],
                    "prompt": "Return one.",
                    "starter_code": "def one():\n    pass\n",
                    "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                    "references": [{"label": "Background", "url": "https://example.com/background"}],
                },
                [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
            )

            store = ProblemStore(root)

            self.assertEqual(
                store.list_problems()[0]["references"],
                [{"label": "Background", "url": "https://example.com/background"}],
            )
            self.assertEqual(
                store.get_problem("with-links")["references"],
                [{"label": "Background", "url": "https://example.com/background"}],
            )

    def test_loads_system_design_problem_with_reference_answer_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "milestone-counter",
                {
                    "id": "141",
                    "slug": "milestone-counter",
                    "title": "Milestone Counter",
                    "category": "System Design",
                    "difficulty": "medium",
                    "prompt": "Design a counter.",
                    "response": {"placeholder": "Start with requirements.", "reference_answer": "## A reference"},
                    "assets": [
                        {
                            "path": "assets/architecture.svg",
                            "alt": "Counter architecture",
                            "caption": "Reference diagram.",
                            "section": "reference_answer",
                        }
                    ],
                    "evaluation": {"type": "system_design"},
                },
                [],
            )
            asset_dir = root / "milestone-counter" / "assets"
            asset_dir.mkdir()
            (asset_dir / "architecture.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")

            problem = ProblemStore(root).get_problem("milestone-counter")

            self.assertEqual(problem["evaluation"]["type"], "system_design")
            self.assertEqual(problem["response"]["reference_answer"], "## A reference")
            self.assertEqual(problem["assets"][0]["path"], "assets/architecture.svg")

    def test_rejects_system_design_asset_outside_its_assets_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "unsafe-system-design",
                {
                    "id": "141",
                    "slug": "unsafe-system-design",
                    "title": "Unsafe System Design",
                    "category": "System Design",
                    "difficulty": "medium",
                    "prompt": "Design safely.",
                    "response": {"placeholder": "Start.", "reference_answer": "## Reference"},
                    "assets": [{"path": "../secret.png", "alt": "Nope", "section": "prompt"}],
                    "evaluation": {"type": "system_design"},
                },
                [],
            )

            with self.assertRaisesRegex(ValueError, "must be under assets/"):
                ProblemStore(root).get_problem("unsafe-system-design")

    def test_includes_companies_in_summaries_details_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "company-problem",
                {
                    "id": "10",
                    "slug": "company-problem",
                    "title": "Company Problem",
                    "category": "ML Systems",
                    "difficulty": "medium",
                    "tags": ["batching"],
                    "companies": ["Anthropic", "OpenAI"],
                    "interview_frequency": {
                        "Anthropic": {
                            "stars": 3,
                            "source_record_ids": ["canonical-row-1"],
                            "synced_at": "2026-08-16",
                        }
                    },
                    "interview_frequency_total": {"stars": 3, "synced_at": "2026-08-16"},
                    "prompt": "Return one.",
                    "starter_code": "def one():\n    pass\n",
                    "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                },
                [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
            )

            store = ProblemStore(root)

            self.assertEqual(store.list_problems()[0]["companies"], ["Anthropic", "OpenAI"])
            self.assertEqual(store.get_problem("company-problem")["companies"], ["Anthropic", "OpenAI"])
            self.assertEqual(store.list_problems(search="anthropic")[0]["slug"], "company-problem")
            self.assertEqual(store.list_problems(company="openai")[0]["slug"], "company-problem")
            self.assertEqual(store.companies(), ["Anthropic", "OpenAI"])
            self.assertEqual(store.list_problems()[0]["interview_frequency"]["Anthropic"]["stars"], 3)
            self.assertEqual(store.list_problems()[0]["interview_frequency_total"]["stars"], 3)
            self.assertEqual(store.get_problem("company-problem")["interview_frequency"]["Anthropic"]["synced_at"], "2026-08-16")

    def test_committed_frequency_tiers_are_per_company_and_source_neutral(self):
        root = Path(__file__).resolve().parents[1]
        store = ProblemStore(root / "problems")

        spreadsheet = store.get_problem("spreadsheet-dependency-cycle")
        self.assertEqual(spreadsheet["interview_frequency"]["Harvey"]["stars"], 1)
        self.assertEqual(spreadsheet["interview_frequency"]["Sierra"]["stars"], 2)
        self.assertEqual(store.get_problem("infection-spread-simulation")["interview_frequency"]["OpenAI"]["stars"], 5)
        self.assertEqual(store.get_problem("linux-cd-path-resolution")["interview_frequency"]["OpenAI"]["stars"], 0)
        self.assertNotIn("seen_count", json.dumps(spreadsheet["interview_frequency"]))

    def test_sorts_by_combined_company_frequency_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder, problem_id, frequency, total in (
                ("no-signal", "1", {}, None),
                (
                    "multi-company-signal",
                    "2",
                    {
                        "Harvey": {"stars": 1, "source_record_ids": ["row-1"], "synced_at": "2026-08-16"},
                        "Sierra": {"stars": 1, "source_record_ids": ["row-2"], "synced_at": "2026-08-16"},
                    },
                    {"stars": 2, "synced_at": "2026-08-16"},
                ),
                (
                    "strong-signal",
                    "3",
                    {"OpenAI": {"stars": 2, "source_record_ids": ["row-3"], "synced_at": "2026-08-16"}},
                    {"stars": 3, "synced_at": "2026-08-16"},
                ),
            ):
                problem = {
                    "id": problem_id,
                    "slug": folder,
                    "title": folder,
                    "category": {
                        "no-signal": "Algorithms",
                        "multi-company-signal": "Systems Coding",
                        "strong-signal": "Computer Vision",
                    }[folder],
                    "difficulty": "medium",
                    "companies": list(frequency),
                    "prompt": "Return one.",
                    "starter_code": "def one():\n    pass\n",
                    "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                    "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                }
                if frequency:
                    problem["interview_frequency"] = frequency
                if total:
                    problem["interview_frequency_total"] = total
                self._write_problem(
                    root,
                    folder,
                    problem,
                    [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
                )

            store = ProblemStore(root)

            self.assertEqual(
                [problem["slug"] for problem in store.list_problems(sort="frequency", order="asc")],
                ["no-signal", "multi-company-signal", "strong-signal"],
            )
            self.assertEqual(
                [problem["slug"] for problem in store.list_problems(sort="frequency", order="desc")],
                ["strong-signal", "multi-company-signal", "no-signal"],
            )

    def test_rejects_invalid_combined_frequency_metadata(self):
        invalid_values = [
            {},
            {"stars": 6, "synced_at": "2026-08-16"},
            {"stars": 1, "synced_at": "today"},
            {"stars": 1, "synced_at": "2026-08-16", "source_record_ids": ["row-1"]},
        ]

        for total in invalid_values:
            with self.subTest(total=total), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write_problem(
                    root,
                    "bad-total-frequency",
                    {
                        "id": "1",
                        "slug": "bad-total-frequency",
                        "title": "Bad Total Frequency",
                        "category": "Machine Learning",
                        "difficulty": "easy",
                        "tags": ["metadata"],
                        "companies": ["Anthropic"],
                        "interview_frequency_total": total,
                        "prompt": "Return one.",
                        "starter_code": "def one():\n    pass\n",
                        "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                        "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                    },
                    [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
                )

                with self.assertRaisesRegex(ValueError, "interview_frequency_total"):
                    ProblemStore(root).get_problem("bad-total-frequency")

    def test_rejects_invalid_reference_links(self):
        invalid_values = [
            "https://example.com",
            [{"label": "Missing URL"}],
            [{"url": "https://example.com"}],
            [{"label": "Unsafe", "url": "javascript:alert(1)"}],
        ]

        for references in invalid_values:
            with self.subTest(references=references), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write_problem(
                    root,
                    "bad-links",
                    {
                        "id": "9",
                        "slug": "bad-links",
                        "title": "Bad Links",
                        "category": "Machine Learning",
                        "difficulty": "easy",
                        "tags": ["links"],
                        "prompt": "Return one.",
                        "starter_code": "def one():\n    pass\n",
                        "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                        "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                        "references": references,
                    },
                    [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
                )

                with self.assertRaisesRegex(ValueError, "references"):
                    ProblemStore(root).get_problem("bad-links")

    def test_rejects_invalid_company_metadata(self):
        invalid_values = [
            "OpenAI",
            [""],
            [1],
        ]

        for companies in invalid_values:
            with self.subTest(companies=companies), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write_problem(
                    root,
                    "bad-companies",
                    {
                        "id": "11",
                        "slug": "bad-companies",
                        "title": "Bad Companies",
                        "category": "Machine Learning",
                        "difficulty": "easy",
                        "tags": ["metadata"],
                        "companies": companies,
                        "prompt": "Return one.",
                        "starter_code": "def one():\n    pass\n",
                        "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                        "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                    },
                    [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
                )

                with self.assertRaisesRegex(ValueError, "companies"):
                    ProblemStore(root).get_problem("bad-companies")

    def test_rejects_invalid_interview_frequency_metadata(self):
        invalid_values = [
            {"Unknown": {"stars": 1, "source_record_ids": ["row-1"], "synced_at": "2026-08-16"}},
            {"Anthropic": {"stars": 6, "source_record_ids": ["row-1"], "synced_at": "2026-08-16"}},
            {"Anthropic": {"stars": 1, "source_record_ids": [], "synced_at": "2026-08-16"}},
            {"Anthropic": {"stars": 1, "source_record_ids": ["row-1"], "synced_at": "today"}},
            {"Anthropic": {"stars": 1, "source_record_ids": ["row-1"], "synced_at": "2026-08-16", "seen_count": 1}},
        ]

        for frequency in invalid_values:
            with self.subTest(frequency=frequency), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write_problem(
                    root,
                    "bad-frequency",
                    {
                        "id": "12",
                        "slug": "bad-frequency",
                        "title": "Bad Frequency",
                        "category": "Machine Learning",
                        "difficulty": "easy",
                        "tags": ["metadata"],
                        "companies": ["Anthropic"],
                        "interview_frequency": frequency,
                        "prompt": "Return one.",
                        "starter_code": "def one():\n    pass\n",
                        "example": {"input": "none", "output": "1", "reasoning": "Toy example."},
                        "environment": {"language": "python", "timeout_seconds": 2, "packages": []},
                    },
                    [{"name": "basic", "test": "print(one())", "expected_output": "1"}],
                )

                with self.assertRaisesRegex(ValueError, "interview_frequency"):
                    ProblemStore(root).get_problem("bad-frequency")

    def test_supports_private_runtime_paths_for_future_modeling_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_target = root / "local-data" / "small-mlp"
            results_target = root / "local-runs" / "small-mlp"
            data_target.mkdir(parents=True)
            results_target.mkdir(parents=True)

            problem = {
                "id": "101",
                "slug": "small-mlp",
                "title": "Small MLP",
                "category": "Modeling",
                "difficulty": "medium",
                "prompt": "Train a small MLP.",
                "starter_code": "def train():\n    pass\n",
                "example": {"input": "dataset", "output": "metrics", "reasoning": "Modeling task."},
                "evaluation": {"type": "ml_modeling"},
                "environment": {"language": "python", "timeout_seconds": 60, "packages": []},
                "data": {"path": "data", "required": True},
                "artifacts": {"results_path": "eval-results"},
            }
            self._write_problem(root, "small-mlp", problem, [])

            problem_dir = root / "small-mlp"
            try:
                (problem_dir / "data").symlink_to(data_target, target_is_directory=True)
                (problem_dir / "eval-results").symlink_to(results_target, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks are not available: {error}")

            loaded = ProblemStore(root).get_problem("small-mlp")

            self.assertEqual(loaded["evaluation"]["type"], "ml_modeling")
            self.assertEqual(loaded["_runtime"]["data_path"], str(problem_dir / "data"))
            self.assertEqual(loaded["_runtime"]["results_path"], str(problem_dir / "eval-results"))
            self.assertTrue(Path(loaded["_runtime"]["data_path"]).is_symlink())
            self.assertTrue(Path(loaded["_runtime"]["results_path"]).is_symlink())

    def test_runtime_paths_are_absolute_when_store_root_is_relative(self):
        cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                root = Path("problems")
                problem_dir = root / "relative-lab"
                data_target = Path("local-data") / "relative-lab"
                root.mkdir()
                data_target.mkdir(parents=True)
                self._write_problem(
                    root,
                    "relative-lab",
                    {
                        "id": "109",
                        "slug": "relative-lab",
                        "title": "Relative Lab",
                        "category": "Modeling",
                        "difficulty": "medium",
                        "prompt": "Train.",
                        "starter_code": "def train():\n    pass\n",
                        "example": {"input": "dataset", "output": "metrics", "reasoning": "Modeling task."},
                        "evaluation": {"type": "ml_modeling"},
                        "environment": {"language": "python", "timeout_seconds": 60, "packages": []},
                        "data": {"path": "data", "required": True},
                    },
                    [],
                )
                (problem_dir / "data").symlink_to(Path("..") / ".." / data_target, target_is_directory=True)

                loaded = ProblemStore(root).get_problem("relative-lab")
            finally:
                os.chdir(cwd)

        self.assertTrue(Path(loaded["_runtime"]["problem_dir"]).is_absolute())
        self.assertTrue(Path(loaded["_runtime"]["data_path"]).is_absolute())
        self.assertIn("problems/relative-lab/data", loaded["_runtime"]["data_path"])

    def test_rejects_unsafe_problem_relative_runtime_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "unsafe",
                {
                    "id": "102",
                    "slug": "unsafe",
                    "title": "Unsafe",
                    "category": "Modeling",
                    "difficulty": "medium",
                    "prompt": "Train.",
                    "starter_code": "def train():\n    pass\n",
                    "example": {"input": "dataset", "output": "metrics", "reasoning": "Modeling task."},
                    "evaluation": {"type": "ml_modeling"},
                    "environment": {"language": "python", "timeout_seconds": 60, "packages": []},
                    "data": {"path": "../data"},
                },
                [],
            )

            with self.assertRaisesRegex(ValueError, "problem-relative"):
                ProblemStore(root).get_problem("unsafe")

    def test_rejects_ml_modeling_tests_without_check_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "modeling",
                {
                    "id": "103",
                    "slug": "modeling",
                    "title": "Modeling",
                    "category": "Modeling",
                    "difficulty": "medium",
                    "prompt": "Fit a model.",
                    "starter_code": "def train():\n    pass\n",
                    "example": {"input": "dataset", "output": "metrics", "reasoning": "Modeling task."},
                    "evaluation": {"type": "ml_modeling"},
                    "environment": {"language": "python", "timeout_seconds": 5, "packages": []},
                },
                [{"name": "missing script"}],
            )

            with self.assertRaisesRegex(ValueError, "missing `test`"):
                ProblemStore(root).get_problem("modeling")

    def test_rejects_ml_torch_modeling_tests_without_check_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "torch-modeling",
                {
                    "id": "104",
                    "slug": "torch-modeling",
                    "title": "Torch Modeling",
                    "category": "Transformers",
                    "difficulty": "hard",
                    "prompt": "Debug a module.",
                    "starter_code": "class Module:\n    pass\n",
                    "example": {"input": "x", "output": "y", "reasoning": "Toy example."},
                    "evaluation": {"type": "ml_torch_modeling"},
                    "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                },
                [{"name": "missing script"}],
            )

            with self.assertRaisesRegex(ValueError, "missing `test`"):
                ProblemStore(root).get_problem("torch-modeling")

    def test_rejects_ml_torch_lab_tests_without_check_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "torch-lab",
                {
                    "id": "105",
                    "slug": "torch-lab",
                    "title": "Torch Lab",
                    "category": "Vision",
                    "difficulty": "medium",
                    "prompt": "Train a module.",
                    "starter_code": "def train_model():\n    pass\n",
                    "example": {"input": "dataset", "output": "metric", "reasoning": "Lab task."},
                    "evaluation": {"type": "ml_torch_lab", "harness": "harness.py"},
                    "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                },
                [{"name": "missing script"}],
            )
            (root / "torch-lab" / "harness.py").write_text("print('hidden')\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing `test`"):
                ProblemStore(root).get_problem("torch-lab")

    def test_rejects_ml_torch_lab_without_problem_relative_harness(self):
        invalid_harnesses = ["../harness.py", "/tmp/harness.py", ""]

        for harness in invalid_harnesses:
            with self.subTest(harness=harness), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write_problem(
                    root,
                    "torch-lab",
                    {
                        "id": "106",
                        "slug": "torch-lab",
                        "title": "Torch Lab",
                        "category": "Vision",
                        "difficulty": "medium",
                        "prompt": "Train a module.",
                        "starter_code": "def train_model():\n    pass\n",
                        "example": {"input": "dataset", "output": "metric", "reasoning": "Lab task."},
                        "evaluation": {"type": "ml_torch_lab", "harness": harness},
                        "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                    },
                    [{"name": "contract", "test": "assert callable(train_model)"}],
                )

                with self.assertRaisesRegex(ValueError, "harness"):
                    ProblemStore(root).get_problem("torch-lab")

    def test_rejects_ml_torch_lab_when_harness_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_problem(
                root,
                "torch-lab",
                {
                    "id": "107",
                    "slug": "torch-lab",
                    "title": "Torch Lab",
                    "category": "Vision",
                    "difficulty": "medium",
                    "prompt": "Train a module.",
                    "starter_code": "def train_model():\n    pass\n",
                    "example": {"input": "dataset", "output": "metric", "reasoning": "Lab task."},
                    "evaluation": {"type": "ml_torch_lab", "harness": "harness.py"},
                    "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                },
                [{"name": "contract", "test": "assert callable(train_model)"}],
            )

            with self.assertRaisesRegex(ValueError, "Lab harness not found"):
                ProblemStore(root).get_problem("torch-lab")

    def _write_problem(self, root, folder, problem, tests):
        problem_dir = root / folder
        problem_dir.mkdir()
        (problem_dir / "problem.json").write_text(json.dumps(problem), encoding="utf-8")
        (problem_dir / "tests.json").write_text(json.dumps(tests), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
