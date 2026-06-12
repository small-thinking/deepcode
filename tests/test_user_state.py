import tempfile
import unittest
from pathlib import Path

from deepcode.user_state import UserStateStore


class UserStateStoreTest(unittest.TestCase):
    def test_missing_state_file_defaults_to_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")

            self.assertEqual(store.status_for("toy"), {"completed": False, "completed_at": None})

    def test_mark_completed_writes_local_status_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deepcode" / "user-state.json"
            store = UserStateStore(path)

            status = store.mark_completed("toy")

            self.assertTrue(status["completed"])
            self.assertIsNotNone(status["completed_at"])
            self.assertTrue(path.exists())
            self.assertIn('"toy"', path.read_text(encoding="utf-8"))

    def test_annotate_does_not_mutate_problem_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            problem = {"slug": "toy", "title": "Toy Problem"}

            annotated = store.annotate(problem)

            self.assertEqual(problem, {"slug": "toy", "title": "Toy Problem"})
            self.assertEqual(annotated["personal_status"], {"completed": False, "completed_at": None})

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
