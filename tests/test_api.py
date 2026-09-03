import json
import tempfile
import unittest
from pathlib import Path

from deepcode.activity_log import ActivityLogStore
from deepcode.api import ApiContext, handle_api_request, stream_api_events
from deepcode.company_store import CompanyStore
from deepcode.custom_tests import CustomTestStore
from deepcode.problem_store import ProblemStore
from deepcode.server import DeepCodeHandler
from deepcode.user_state import UserStateStore


class ApiTest(unittest.TestCase):
    def test_lists_problems_with_facets(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems",
                {"category": ["Machine Learning"]},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["problems"][0]["slug"], "toy")
            self.assertEqual(payload["categories"], ["Machine Learning"])
            self.assertEqual(payload["difficulties"], ["easy"])

    def test_lists_global_company_counts_even_when_results_are_filtered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(root, "airbnb-openai", "1", {"companies": ["Airbnb", "OpenAI"]})
            self._write_problem(root, "airbnb-only", "2", {"companies": ["Airbnb"]})

            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems",
                {"company": ["OpenAI"]},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual([problem["slug"] for problem in payload["problems"]], ["airbnb-openai"])
            self.assertEqual(payload["company_counts"], {"Airbnb": 2, "OpenAI": 1})

    def test_lists_problems_in_requested_sort_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(root, "alpha", "1", {"title": "Alpha"})
            self._write_problem(root, "zulu", "2", {"title": "Zulu"})

            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems",
                {"sort": ["title"], "order": ["desc"]},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual([problem["slug"] for problem in payload["problems"]], ["zulu", "alpha"])

    def test_server_dispatches_mutating_api_methods(self):
        self.assertTrue(hasattr(DeepCodeHandler, "do_PUT"))
        self.assertTrue(hasattr(DeepCodeHandler, "do_DELETE"))

    def test_lists_problems_with_local_personal_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")
            user_state.mark_completed("toy")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "GET",
                "/api/problems",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["problems"][0]["personal_status"]["completed"], True)

    def test_sorts_problems_by_local_completion_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user_state = UserStateStore(root / ".deepcode" / "user-state.json")
            self._write_problem(root / "problems", "incomplete", "1")
            self._write_problem(root / "problems", "complete", "2")
            user_state.mark_completed("complete")
            context = ApiContext(store=ProblemStore(root / "problems"), user_state=user_state)

            _, ascending = handle_api_request(
                context, "GET", "/api/problems", {"sort": ["completed"], "order": ["asc"]}, None
            )
            _, descending = handle_api_request(
                context, "GET", "/api/problems", {"sort": ["completed"], "order": ["desc"]}, None
            )

            self.assertEqual([problem["slug"] for problem in ascending["problems"]], ["incomplete", "complete"])
            self.assertEqual([problem["slug"] for problem in descending["problems"]], ["complete", "incomplete"])

    def test_fetches_problem_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(ApiContext(store=store), "GET", "/api/problems/toy", {}, None)

            self.assertEqual(status, 200)
            self.assertEqual(payload["problem"]["starter_code"], "def identity(x):\n    pass\n")
            self.assertEqual(payload["problem"]["tests"][0]["input"], "x = 4")
            self.assertEqual(payload["problem"]["tests"][0]["expected_output"], "4")
            self.assertNotIn("_runtime", payload["problem"])

    def test_exposes_interview_frequency_tiers_without_raw_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            frequency = {
                "OpenAI": {"stars": 3, "source_record_ids": ["canonical-row-1"], "synced_at": "2026-08-16"}
            }
            total = {"stars": 3, "synced_at": "2026-08-16"}
            self._write_problem(
                root,
                "toy",
                "1",
                {"companies": ["OpenAI"], "interview_frequency": frequency, "interview_frequency_total": total},
            )
            context = ApiContext(store=store)

            _, list_payload = handle_api_request(context, "GET", "/api/problems", {}, None)
            _, detail_payload = handle_api_request(context, "GET", "/api/problems/toy", {}, None)

            self.assertEqual(list_payload["problems"][0]["interview_frequency"], frequency)
            self.assertEqual(list_payload["problems"][0]["interview_frequency_total"], total)
            self.assertEqual(detail_payload["problem"]["interview_frequency"], frequency)
            self.assertEqual(detail_payload["problem"]["interview_frequency_total"], total)
            self.assertNotIn("seen_count", json.dumps(detail_payload["problem"]["interview_frequency"]))
            self.assertNotIn("seen_count", json.dumps(detail_payload["problem"]["interview_frequency_total"]))

    def test_lists_and_fetches_company_profiles_with_related_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            problems_root = root / "problems"
            companies_root = root / "companies"
            companies_root.mkdir()
            self._write_problem(problems_root, "harvey-question", "1", {"companies": ["Harvey"]})
            self._write_company(companies_root, "harvey", self._company_payload())
            context = ApiContext(store=ProblemStore(problems_root), company_store=CompanyStore(companies_root))

            status, payload = handle_api_request(context, "GET", "/api/companies", {}, None)
            self.assertEqual(status, 200)
            self.assertEqual(payload["total"], 1)
            self.assertEqual(payload["companies"][0]["problem_count"], 1)

            status, payload = handle_api_request(context, "GET", "/api/companies/harvey", {}, None)
            self.assertEqual(status, 200)
            self.assertEqual(payload["company"]["name"], "Harvey")
            self.assertEqual(payload["company"]["related_problems"][0]["slug"], "harvey-question")

            status, payload = handle_api_request(context, "GET", "/api/problems", {"company": ["Harvey"]}, None)
            self.assertEqual(status, 200)
            self.assertEqual([problem["slug"] for problem in payload["problems"]], ["harvey-question"])
            self.assertEqual(payload["companies"], ["Harvey"])
            self.assertEqual(payload["company_profiles"], [{"slug": "harvey", "name": "Harvey", "aliases": []}])

    def test_returns_404_for_unknown_company_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companies_root = root / "companies"
            companies_root.mkdir()
            context = ApiContext(store=ProblemStore(root / "problems"), company_store=CompanyStore(companies_root))

            status, payload = handle_api_request(context, "GET", "/api/companies/missing", {}, None)

            self.assertEqual(status, 404)
            self.assertEqual(payload["error"], "Company not found")

    def test_runs_submission_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["passed"], 1)

    def test_runs_selected_visible_test_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                tests=[
                    {"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"},
                    {"name": "harder", "input": "x = 5", "test": "print(identity(5))", "expected_output": "5"},
                ],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 4\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["total"], 1)
            self.assertEqual([result["name"] for result in payload["results"]], ["basic"])

    def test_rejects_out_of_range_selected_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n", "test_index": 3}).encode("utf-8"),
            )

            self.assertEqual(status, 400)
            self.assertIn("test_index", payload["error"])

    def test_passing_submission_marks_problem_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["problem_status"]["completed"], True)
            self.assertEqual(payload["problem_status"]["last_submission"]["status"], "passed")
            self.assertEqual(user_state.status_for("toy")["completed"], True)

    def test_failed_full_submission_marks_problem_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 0\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["problem_status"]["completed"], False)
            self.assertEqual(payload["problem_status"]["last_submission"]["status"], "in_progress")
            self.assertIsNotNone(payload["problem_status"]["last_submission"]["at"])

    def test_progress_records_every_scope_but_status_only_records_full_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root / "problems")
            user_state = UserStateStore(root / ".deepcode" / "user-state.json")
            activity_log = ActivityLogStore(root / ".deepcode" / "activity-log.json")
            self._write_problem(
                root / "problems",
                "toy",
                "1",
                problem_overrides={"companies": ["OpenAI"]},
                tests=[
                    {"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"},
                    {"name": "harder", "input": "x = 5", "test": "print(identity(5))", "expected_output": "5"},
                ],
            )
            context = ApiContext(store=store, user_state=user_state, activity_log=activity_log)

            _, failed = handle_api_request(
                context,
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 0\n"}).encode("utf-8"),
            )
            _, selected = handle_api_request(
                context,
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 4\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(failed["status"], "failed")
            self.assertEqual(selected["status"], "passed")
            self.assertNotIn("problem_status", selected)
            events = activity_log.list_events()
            self.assertEqual(len(events), 2)
            self.assertEqual({event["scope"] for event in events}, {"full", "selected"})
            self.assertEqual({event["outcome"] for event in events}, {"passed", "not_passed"})
            self.assertEqual(user_state.status_for("toy")["last_submission"]["status"], "in_progress")
            _, progress = handle_api_request(context, "GET", "/api/progress", {}, None)
            self.assertEqual(len(progress["events"]), 2)

    def test_progress_endpoint_backfills_existing_statuses_and_returns_catalog_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user_state = UserStateStore(root / ".deepcode" / "user-state.json")
            activity_log = ActivityLogStore(root / ".deepcode" / "activity-log.json")
            self._write_problem(
                root / "problems",
                "toy",
                "1",
                problem_overrides={"companies": ["OpenAI"]},
            )
            companies_root = root / "companies"
            companies_root.mkdir()
            company = self._company_payload()
            company.update({"slug": "openai", "name": "OpenAI"})
            self._write_company(companies_root, "openai", company)
            user_state.mark_completed("toy")
            context = ApiContext(
                store=ProblemStore(root / "problems"),
                company_store=CompanyStore(companies_root),
                user_state=user_state,
                activity_log=activity_log,
            )

            status, payload = handle_api_request(context, "GET", "/api/progress", {}, None)
            _, repeated_payload = handle_api_request(context, "GET", "/api/progress", {}, None)

            self.assertEqual(status, 200)
            self.assertEqual(len(payload["events"]), 1)
            self.assertEqual(payload["events"][0]["source"], "status_backfill")
            self.assertEqual(len(repeated_payload["events"]), 1)
            self.assertEqual(payload["problems"][0]["companies"], ["OpenAI"])
            self.assertEqual(payload["problems"][0]["personal_status"]["completed"], True)
            self.assertEqual(payload["company_profiles"], [{"slug": "openai", "name": "OpenAI", "aliases": []}])

    def test_passing_selected_test_does_not_mark_problem_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(
                Path(tmp) / "problems",
                "toy",
                "1",
                tests=[
                    {"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"},
                    {"name": "harder", "input": "x = 5", "test": "print(identity(5))", "expected_output": "5"},
                ],
            )

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 4\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertNotIn("problem_status", payload)
            self.assertEqual(user_state.status_for("toy")["completed"], False)

    def test_failed_streaming_full_submission_marks_problem_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            events = list(
                stream_api_events(
                    ApiContext(store=store, user_state=user_state),
                    "POST",
                    "/api/problems/toy/run/stream",
                    {},
                    json.dumps({"code": "def identity(x):\n    return 0\n"}).encode("utf-8"),
                )
            )

            result = events[-1]["result"]
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["problem_status"]["last_submission"]["status"], "in_progress")
            self.assertFalse(user_state.status_for("toy")["completed"])

    def test_saves_and_fetches_local_custom_tests_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            custom_tests = CustomTestStore(Path(tmp) / ".deepcode" / "custom-tests.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, custom_tests=custom_tests),
                "PUT",
                "/api/problems/toy/custom-tests",
                {},
                json.dumps(
                    {
                        "custom_tests": [
                            {
                                "name": "negative value",
                                "input": "x = -3",
                                "test": "print(identity(-3))",
                                "expected_output": "-3",
                            }
                        ]
                    }
                ).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["custom_tests"][0]["name"], "negative value")

            status, payload = handle_api_request(
                ApiContext(store=store, custom_tests=custom_tests),
                "GET",
                "/api/problems/toy/custom-tests",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["custom_tests"][0]["test"], "print(identity(-3))")
            self.assertIn("negative value", custom_tests.path.read_text(encoding="utf-8"))

    def test_saves_argument_custom_tests_as_generated_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            custom_tests = CustomTestStore(Path(tmp) / ".deepcode" / "custom-tests.json")
            self._write_problem(
                Path(tmp) / "problems",
                "toy",
                "1",
                problem_overrides={"starter_code": "def score(y_true, y_pred):\n    pass\n"},
            )

            status, payload = handle_api_request(
                ApiContext(store=store, custom_tests=custom_tests),
                "PUT",
                "/api/problems/toy/custom-tests",
                {},
                json.dumps(
                    {
                        "custom_tests": [
                            {
                                "name": "case-sensitive labels",
                                "arguments": {
                                    "y_true": "['cat', 'Cat']",
                                    "y_pred": "['cat', 'cat']",
                                },
                                "expected_output": "0.5",
                            }
                        ]
                    }
                ).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["custom_tests"][0]["mode"], "arguments")
            self.assertEqual(payload["custom_tests"][0]["input"], "y_true = ['cat', 'Cat'], y_pred = ['cat', 'cat']")
            self.assertEqual(payload["custom_tests"][0]["test"], "print(score(['cat', 'Cat'], ['cat', 'cat']))")
            self.assertEqual(payload["custom_tests"][0]["arguments"]["y_pred"], "['cat', 'cat']")

    def test_runs_argument_custom_tests_without_raw_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(
                Path(tmp) / "problems",
                "toy",
                "1",
                problem_overrides={"starter_code": "def score(y_true, y_pred):\n    pass\n"},
            )

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps(
                    {
                        "code": "def score(y_true, y_pred):\n    return round(sum(a == b for a, b in zip(y_true, y_pred)) / len(y_true), 4)\n",
                        "custom_only": True,
                        "custom_tests": [
                            {
                                "name": "case-sensitive labels",
                                "arguments": {
                                    "y_true": "['cat', 'Cat']",
                                    "y_pred": "['cat', 'cat']",
                                },
                                "expected_output": "0.5",
                            }
                        ],
                    }
                ).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["results"][0]["test"], "print(score(['cat', 'Cat'], ['cat', 'cat']))")
            self.assertNotIn("problem_status", payload)

    def test_rejects_invalid_custom_test_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            custom_tests = CustomTestStore(Path(tmp) / ".deepcode" / "custom-tests.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, custom_tests=custom_tests),
                "PUT",
                "/api/problems/toy/custom-tests",
                {},
                json.dumps({"custom_tests": [{"name": "missing expected", "test": "print(identity(4))"}]}).encode(
                    "utf-8"
                ),
            )

            self.assertEqual(status, 400)
            self.assertIn("expected_output", payload["error"])

    def test_runs_custom_ml_coding_tests_without_marking_problem_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps(
                    {
                        "code": "def identity(x):\n    return x\n",
                        "custom_only": True,
                        "custom_tests": [
                            {
                                "name": "negative value",
                                "input": "x = -3",
                                "test": "print(identity(-3))",
                                "expected_output": "-3",
                            }
                        ],
                    }
                ).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["results"][0]["name"], "negative value")
            self.assertNotIn("problem_status", payload)
            self.assertEqual(user_state.status_for("toy")["completed"], False)

    def test_rejects_custom_tests_for_non_ml_coding_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            self._write_problem(
                Path(tmp) / "problems",
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "identity behavior", "test": "assert identity(4) == 4"}],
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps(
                    {
                        "code": "def identity(x):\n    return x\n",
                        "custom_only": True,
                        "custom_tests": [
                            {"name": "custom", "test": "assert identity(4) == 4", "expected_output": "ok"}
                        ],
                    }
                ).encode("utf-8"),
            )

            self.assertEqual(status, 400)
            self.assertIn("ml_coding", payload["error"])

    def test_reset_submission_status_marks_problem_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")
            user_state.mark_completed("toy")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/reset",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(
                payload["problem_status"],
                {"completed": False, "completed_at": None, "last_submission": None},
            )
            self.assertEqual(user_state.status_for("toy")["completed"], False)

    def test_returns_501_for_unregistered_evaluator(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "not_registered"}},
                tests=[],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "print('training placeholder')\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 501)
            self.assertIn("Unsupported evaluator", payload["error"])

    def test_runs_ml_modeling_submission_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "identity behavior", "test": "assert identity(4) == 4\nprint('ok')"}],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["results"][0]["actual_output"], "ok")

    def test_selected_visible_check_for_lab_problem_skips_hidden_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "lab",
                "200",
                problem_overrides={
                    "evaluation": {"type": "ml_torch_lab", "harness": "harness.py"},
                    "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                },
                tests=[{"name": "visible contract", "test": "assert callable(train)\nprint('visible ok')"}],
            )
            (root / "lab" / "harness.py").write_text(
                "raise AssertionError('hidden lab harness should not run')",
                encoding="utf-8",
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/lab/run",
                {},
                json.dumps({"code": "def train():\n    return None\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["total"], 1)
            self.assertEqual(payload["results"][0]["name"], "visible contract")

    def test_reports_missing_modeling_data_link_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "modeling",
                "101",
                problem_overrides={
                    "evaluation": {"type": "ml_modeling"},
                    "data": {"path": "data", "required": True},
                },
                tests=[{"name": "noop", "test": "assert True"}],
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems/modeling/data-link",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["data_path"], "data")
            self.assertFalse(payload["exists"])
            self.assertFalse(payload["is_symlink"])
            self.assertIsNone(payload["target_path"])
            self.assertTrue(payload["link_path"].endswith("modeling/data"))

    def test_creates_modeling_data_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "datasets" / "toy"
            target.mkdir(parents=True)
            store = ProblemStore(root / "problems")
            self._write_problem(
                root / "problems",
                "modeling",
                "101",
                problem_overrides={
                    "evaluation": {"type": "ml_modeling"},
                    "data": {"path": "data", "required": True},
                },
                tests=[{"name": "noop", "test": "assert True"}],
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "PUT",
                "/api/problems/modeling/data-link",
                {},
                json.dumps({"target_path": str(target)}).encode("utf-8"),
            )

            link_path = root / "problems" / "modeling" / "data"
            self.assertEqual(status, 200)
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(link_path.readlink(), target)
            self.assertTrue(payload["exists"])
            self.assertTrue(payload["is_symlink"])
            self.assertEqual(payload["target_path"], str(target))

    def test_rejects_missing_modeling_data_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "modeling",
                "101",
                problem_overrides={
                    "evaluation": {"type": "ml_modeling"},
                    "data": {"path": "data", "required": True},
                },
                tests=[{"name": "noop", "test": "assert True"}],
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "PUT",
                "/api/problems/modeling/data-link",
                {},
                json.dumps({"target_path": str(root / "missing")}).encode("utf-8"),
            )

            self.assertEqual(status, 400)
            self.assertIn("existing directory", payload["error"])

    def test_refuses_to_overwrite_real_data_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "datasets" / "toy"
            target.mkdir(parents=True)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "modeling",
                "101",
                problem_overrides={
                    "evaluation": {"type": "ml_modeling"},
                    "data": {"path": "data", "required": True},
                },
                tests=[{"name": "noop", "test": "assert True"}],
            )
            (root / "modeling" / "data").mkdir()

            status, payload = handle_api_request(
                ApiContext(store=store),
                "PUT",
                "/api/problems/modeling/data-link",
                {},
                json.dumps({"target_path": str(target)}).encode("utf-8"),
            )

            self.assertEqual(status, 400)
            self.assertIn("Refusing to replace", payload["error"])

    def test_removes_modeling_data_symlink_without_deleting_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "datasets" / "toy"
            target.mkdir(parents=True)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "modeling",
                "101",
                problem_overrides={
                    "evaluation": {"type": "ml_modeling"},
                    "data": {"path": "data", "required": True},
                },
                tests=[{"name": "noop", "test": "assert True"}],
            )
            link_path = root / "modeling" / "data"
            link_path.symlink_to(target, target_is_directory=True)

            status, payload = handle_api_request(
                ApiContext(store=store),
                "DELETE",
                "/api/problems/modeling/data-link",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertFalse(link_path.exists())
            self.assertTrue(target.exists())
            self.assertFalse(payload["exists"])

    def test_rejects_data_link_for_problem_without_data_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems/toy/data-link",
                {},
                None,
            )

            self.assertEqual(status, 400)
            self.assertIn("data.path", payload["error"])

    def test_streams_submission_logs_for_modeling_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "training", "test": "train()\nprint('done')\n"}],
            )
            events = list(
                stream_api_events(
                    ApiContext(store=store),
                    "POST",
                    "/api/problems/toy/run/stream",
                    {},
                    json.dumps({"code": "def train():\n    print('epoch 1 loss=0.25')\n"}).encode("utf-8"),
                )
            )

            log_events = [event for event in events if event["type"] == "log"]
            self.assertEqual(events[0], {"type": "run_started", "total": 1})
            self.assertEqual(log_events[0]["text"], "epoch 1 loss=0.25\n")
            self.assertEqual(events[-1]["type"], "run_finished")
            self.assertEqual(events[-1]["result"]["status"], "passed")

    def test_returns_404_for_unknown_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, payload = handle_api_request(
                ApiContext(store=ProblemStore(Path(tmp))),
                "GET",
                "/api/problems/missing",
                {},
                None,
            )

            self.assertEqual(status, 404)
            self.assertEqual(payload["error"], "Problem not found")

    def _write_problem(self, root, folder, problem_id, problem_overrides=None, tests=None):
        problem_dir = root / folder
        problem_dir.mkdir(parents=True)
        problem = {
            "id": problem_id,
            "slug": folder,
            "title": "Toy Identity",
            "category": "Machine Learning",
            "difficulty": "easy",
            "tags": ["toy"],
            "prompt": "Return the input.",
            "starter_code": "def identity(x):\n    pass\n",
            "example": {"input": "x = 4", "output": "4", "reasoning": "Identity returns the same value."},
            "environment": {
                "language": "python",
                "timeout_seconds": 2,
                "packages": [],
                "comparator": "exact",
            },
        }
        if problem_overrides:
            problem.update(problem_overrides)
        (problem_dir / "problem.json").write_text(
            json.dumps(problem),
            encoding="utf-8",
        )
        (problem_dir / "tests.json").write_text(
            json.dumps(
                tests
                if tests is not None
                else [{"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"}]
            ),
            encoding="utf-8",
        )

    def _write_company(self, root, slug, company):
        (root / f"{slug}.json").write_text(json.dumps(company), encoding="utf-8")

    def _company_payload(self):
        return {
            "slug": "harvey",
            "name": "Harvey",
            "summary": "Legal AI.",
            "stage": {
                "company_state": "Private",
                "funding_stage": "Growth round",
                "source": {"label": "Funding", "url": "https://example.com/funding"},
            },
            "links": [{"label": "Website", "url": "https://example.com"}],
            "interview_process": {
                "stages": [
                    {
                        "name": "Technical screen",
                        "signal": "Public signal.",
                        "evidence_tier": "Candidate report",
                        "sources": [{"label": "Source", "url": "https://example.com/source"}],
                    }
                ]
            },
            "references": [{"label": "Company", "url": "https://example.com"}],
        }


if __name__ == "__main__":
    unittest.main()
