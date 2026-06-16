#!/usr/bin/env python
from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8848
DEFAULT_DEBOUNCE_MS = 500


def build_server_command(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return shlex.join(["python", "-m", "deepcode", "--host", host, "--port", str(port)])


def default_watch_paths(root: Path = ROOT) -> tuple[Path, ...]:
    return (
        root / "deepcode",
        root / "frontend",
        root / "problems",
        root / "pyproject.toml",
        root / "uv.lock",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepCode locally and restart it when source files change.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--debounce", default=DEFAULT_DEBOUNCE_MS, type=int, help="Debounce file changes in milliseconds.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional paths to watch. Defaults to DeepCode source, frontend, problems, and uv project files.",
    )
    return parser.parse_args(argv)


def _relative_path(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return path


def _log_restart(changes) -> None:
    changed_paths = sorted({_relative_path(path) for _, path in changes})
    preview = ", ".join(changed_paths[:6])
    if len(changed_paths) > 6:
        preview = f"{preview}, ..."
    print(f"\nRestarting DeepCode after changes: {preview}", flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        from watchfiles import run_process
    except ImportError as error:
        raise SystemExit("watchfiles is required. Run: uv run --with watchfiles scripts/dev.py") from error

    paths = tuple(path.resolve() for path in args.paths) if args.paths else default_watch_paths(ROOT)
    command = build_server_command(host=args.host, port=args.port)

    print(f"Watching DeepCode paths from {ROOT}", flush=True)
    print(f"Restart command: {command}", flush=True)
    return run_process(
        *paths,
        target=command,
        target_type="command",
        callback=_log_restart,
        debounce=args.debounce,
    )


if __name__ == "__main__":
    raise SystemExit(main())
