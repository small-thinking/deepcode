from __future__ import annotations

import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PLAYGROUND_TIMEOUT_SECONDS = 30
MAX_CODE_CHARS = 100_000
MAX_CAPTURE_BYTES = 200_000
MAX_FILE_BYTES = 2_000_000


def run_playground(code: str, timeout_seconds: int | float = PLAYGROUND_TIMEOUT_SECONDS) -> dict[str, Any]:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Request body must include non-empty `code`")
    if len(code) > MAX_CODE_CHARS:
        raise ValueError(f"Playground code must be at most {MAX_CODE_CHARS:,} characters")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("Playground timeout must be a positive number")

    started_at = time.monotonic()
    timed_out = False
    returncode: int | None = None

    with tempfile.TemporaryDirectory(prefix="deepcode-playground-") as tmp:
        root = Path(tmp)
        script_path = root / "playground.py"
        stdout_path = root / "stdout.log"
        stderr_path = root / "stderr.log"
        script_path.write_text(code, encoding="utf-8")

        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                [sys.executable, "-u", str(script_path)],
                cwd=root,
                env=_runner_env(),
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=os.name == "posix",
                preexec_fn=_resource_limiter(timeout_seconds) if os.name == "posix" else None,
            )
            try:
                returncode = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_tree(process)

        stdout, stdout_truncated = _read_output(stdout_path)
        stderr, stderr_truncated = _read_output(stderr_path)

    duration_ms = round((time.monotonic() - started_at) * 1000)
    status = "timed_out" if timed_out else "completed" if returncode == 0 else "error"
    if timed_out:
        timeout_message = f"Execution timed out after {timeout_seconds:g} seconds."
        stderr = f"{stderr}\n{timeout_message}".strip()

    return {
        "status": status,
        "exit_code": None if timed_out else returncode,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "timeout_seconds": timeout_seconds,
        "output_truncated": stdout_truncated or stderr_truncated,
    }


def _read_output(path: Path) -> tuple[str, bool]:
    size = path.stat().st_size
    data = path.read_bytes()[:MAX_CAPTURE_BYTES]
    text = data.decode("utf-8", errors="replace")
    truncated = size > MAX_CAPTURE_BYTES
    if truncated:
        text = f"{text.rstrip()}\n\n[output truncated by DeepCode]"
    return text, truncated


def _kill_process_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()
    process.wait()


def _runner_env() -> dict[str, str]:
    allowed = {}
    for key in ("PATH", "PYTHONPATH", "PYTHONHOME", "SYSTEMROOT"):
        if key in os.environ:
            allowed[key] = os.environ[key]
    allowed["PYTHONIOENCODING"] = "utf-8"
    allowed["PYTHONUNBUFFERED"] = "1"
    return allowed


def _resource_limiter(timeout_seconds: int | float):
    def limit_resources():
        try:
            import resource

            cpu_seconds = max(1, math.ceil(timeout_seconds) + 1)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except Exception:
            pass

    return limit_resources
