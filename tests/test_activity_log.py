import tempfile
import unittest
from pathlib import Path

from deepcode.activity_log import ActivityLogStore


class ActivityLogStoreTest(unittest.TestCase):
    def test_records_repeat_runs_without_submission_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ActivityLogStore(Path(tmp) / "activity-log.json")
            problem = {
                "slug": "toy",
                "title": "Toy Identity",
                "category": "Machine Learning",
                "difficulty": "easy",
                "companies": ["OpenAI"],
            }

            store.record_submission(problem, scope="full", result={"passed": 0, "total": 1, "status": "failed"})
            store.record_submission(problem, scope="selected", result={"passed": 1, "total": 1, "status": "passed"})

            events = store.list_events()
            self.assertEqual(len(events), 2)
            self.assertEqual({event["scope"] for event in events}, {"full", "selected"})
            self.assertEqual({event["outcome"] for event in events}, {"passed", "not_passed"})
            self.assertTrue(all("code" not in event for event in events))

    def test_backfill_adds_known_statuses_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ActivityLogStore(Path(tmp) / "activity-log.json")
            problem = {
                "slug": "toy",
                "title": "Toy Identity",
                "category": "Machine Learning",
                "difficulty": "easy",
                "companies": [],
                "personal_status": {
                    "completed": True,
                    "completed_at": "2026-08-30T12:00:00Z",
                    "last_submission": {"status": "in_progress", "at": "2026-08-31T12:00:00Z"},
                },
            }

            self.assertEqual(len(store.backfill_problem_statuses([problem])), 2)
            self.assertEqual(store.backfill_problem_statuses([problem]), [])
            events = store.list_events()
            self.assertEqual(len(events), 2)
            self.assertEqual({event["source"] for event in events}, {"status_backfill"})
            self.assertEqual({event["outcome"] for event in events}, {"passed", "not_passed"})
            self.assertTrue(all(event["passed"] is None and event["total"] is None for event in events))
