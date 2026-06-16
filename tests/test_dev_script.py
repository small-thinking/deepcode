import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dev.py"


def _load_dev_script():
    spec = importlib.util.spec_from_file_location("dev_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DevScriptTest(unittest.TestCase):
    def test_build_server_command_uses_direct_python_process(self):
        dev_script = _load_dev_script()

        command = dev_script.build_server_command(host="127.0.0.1", port=8848)

        self.assertEqual(command, "python -m deepcode --host 127.0.0.1 --port 8848")
        self.assertNotIn("uv run", command)

    def test_default_watch_paths_cover_source_ui_and_problem_files(self):
        dev_script = _load_dev_script()

        paths = dev_script.default_watch_paths(ROOT)

        self.assertEqual(
            paths,
            (
                ROOT / "deepcode",
                ROOT / "frontend",
                ROOT / "problems",
                ROOT / "pyproject.toml",
                ROOT / "uv.lock",
            ),
        )

    def test_parse_args_defaults_to_local_deepcode_port(self):
        dev_script = _load_dev_script()

        args = dev_script.parse_args([])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8848)
        self.assertEqual(args.debounce, 500)


if __name__ == "__main__":
    unittest.main()
