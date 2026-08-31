import tempfile
import unittest
from pathlib import Path

from deepcode.user_state import UserStateStore


class UserStateStoreTest(unittest.TestCase):
    def test_missing_state_file_defaults_to_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")

            self.assertEqual(
                store.status_for("toy"),
                {"completed": False, "completed_at": None, "last_submission": None},
            )

    def test_mark_completed_writes_local_status_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            store = UserStateStore(path)

            status = store.mark_completed("toy")

            self.assertTrue(status["completed"])
            self.assertIsNotNone(status["completed_at"])
            self.assertEqual(status["last_submission"]["status"], "passed")
            self.assertEqual(status["last_submission"]["at"], status["completed_at"])
            self.assertTrue(path.exists())
            self.assertIn('"toy"', path.read_text(encoding="utf-8"))

    def test_failed_full_submission_is_recorded_as_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")

            status = store.record_submission("toy", passed=False)

            self.assertFalse(status["completed"])
            self.assertIsNone(status["completed_at"])
            self.assertEqual(status["last_submission"]["status"], "in_progress")
            self.assertIsNotNone(status["last_submission"]["at"])

    def test_failed_submission_keeps_a_previous_completion_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            completed = store.mark_completed("toy")

            status = store.record_submission("toy", passed=False)

            self.assertTrue(status["completed"])
            self.assertEqual(status["completed_at"], completed["completed_at"])
            self.assertEqual(status["last_submission"]["status"], "in_progress")

    def test_ensure_exists_creates_empty_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            store = UserStateStore(path)

            store.ensure_exists()

            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "problems": {}\n}\n')

    def test_reset_problem_removes_completed_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            store = UserStateStore(path)
            store.mark_completed("toy")

            status = store.reset_problem("toy")

            self.assertEqual(status, {"completed": False, "completed_at": None, "last_submission": None})
            self.assertNotIn('"toy"', path.read_text(encoding="utf-8"))

    def test_reset_problem_creates_missing_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            store = UserStateStore(path)

            status = store.reset_problem("toy")

            self.assertEqual(status, {"completed": False, "completed_at": None, "last_submission": None})
            self.assertTrue(path.exists())

    def test_annotate_does_not_mutate_problem_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            problem = {"slug": "toy", "title": "Toy Problem"}

            annotated = store.annotate(problem)

            self.assertEqual(problem, {"slug": "toy", "title": "Toy Problem"})
            self.assertEqual(
                annotated["personal_status"],
                {"completed": False, "completed_at": None, "last_submission": None},
            )

    def test_rejects_invalid_state_json_with_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            path.parent.mkdir()
            path.write_text("{not-json", encoding="utf-8")
            store = UserStateStore(path)

            with self.assertRaisesRegex(ValueError, "valid JSON"):
                store.status_for("toy")


if __name__ == "__main__":
    unittest.main()
