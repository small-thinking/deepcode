from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from deepcode.activity_log import ActivityLogStore
from deepcode.api import ApiContext, handle_api_request, stream_api_events
from deepcode.company_store import CompanyStore
from deepcode.custom_tests import CustomTestStore
from deepcode.problem_store import PROBLEM_ASSET_SUFFIXES, PROBLEM_DEMO_SUFFIXES, ProblemStore
from deepcode.user_state import UserStateStore


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
PROBLEMS_DIR = BASE_DIR / "problems"
COMPANIES_DIR = BASE_DIR / "companies"
USER_STATE_PATH = Path(os.environ.get("DEEPCODE_USER_STATE_PATH", BASE_DIR / ".deepcode" / "user-state.json"))
CUSTOM_TESTS_PATH = Path(os.environ.get("DEEPCODE_CUSTOM_TESTS_PATH", BASE_DIR / ".deepcode" / "custom-tests.json"))
ACTIVITY_LOG_PATH = Path(os.environ.get("DEEPCODE_ACTIVITY_LOG_PATH", BASE_DIR / ".deepcode" / "activity-log.json"))
DEFAULT_PORT = 8848
PROBLEM_DEMO_CSP = (
    "default-src 'none'; "
    "script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline'; "
    "img-src data:; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'self'"
)


def resolve_problem_asset(request_path: str, problems_dir: Path = PROBLEMS_DIR) -> Path | None:
    """Resolve a committed visual under one problem's assets directory."""
    parts = [unquote(part) for part in request_path.strip("/").split("/")]
    if len(parts) < 4 or parts[0] != "problem-assets":
        return None
    slug, *asset_parts = parts[1:]
    if not slug or any(part in {"", ".", ".."} for part in [slug, *asset_parts]):
        return None

    asset_path = Path(*asset_parts)
    if asset_path.parts[0] != "assets" or asset_path.suffix.casefold() not in PROBLEM_ASSET_SUFFIXES:
        return None

    try:
        problem = ProblemStore(problems_dir).get_problem(slug)
    except (KeyError, ValueError):
        return None
    problem_dir = Path(problem["_runtime"]["problem_dir"])
    assets_dir = (problem_dir / "assets").resolve()
    file_path = (problem_dir / asset_path).resolve()
    if not file_path.is_relative_to(assets_dir) or not file_path.is_file():
        return None
    return file_path


def resolve_problem_demo(request_path: str, problems_dir: Path = PROBLEMS_DIR) -> Path | None:
    """Resolve one declared interactive demo under its owning problem directory."""
    parts = [unquote(part) for part in request_path.strip("/").split("/")]
    if len(parts) < 4 or parts[0] != "problem-demos":
        return None
    slug, *demo_parts = parts[1:]
    if not slug or any(part in {"", ".", ".."} for part in [slug, *demo_parts]):
        return None

    demo_path = Path(*demo_parts)
    if demo_path.parts[0] != "assets" or demo_path.suffix.casefold() not in PROBLEM_DEMO_SUFFIXES:
        return None

    try:
        problem = ProblemStore(problems_dir).get_problem(slug)
    except (KeyError, ValueError):
        return None
    declared_paths = {
        demo.get("path")
        for demo in problem.get("interactive_demos", [])
        if isinstance(demo, dict) and isinstance(demo.get("path"), str)
    }
    normalized_path = demo_path.as_posix()
    if normalized_path not in declared_paths:
        return None

    problem_dir = Path(problem["_runtime"]["problem_dir"])
    assets_dir = (problem_dir / "assets").resolve()
    file_path = (problem_dir / demo_path).resolve()
    if not file_path.is_relative_to(assets_dir) or not file_path.is_file():
        return None
    return file_path


class DeepCodeHandler(BaseHTTPRequestHandler):
    context = ApiContext(
        store=ProblemStore(PROBLEMS_DIR),
        company_store=CompanyStore(COMPANIES_DIR),
        user_state=UserStateStore(USER_STATE_PATH),
        custom_tests=CustomTestStore(CUSTOM_TESTS_PATH),
        activity_log=ActivityLogStore(ACTIVITY_LOG_PATH),
    )

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def do_PUT(self):
        self._dispatch()

    def do_DELETE(self):
        self._dispatch()

    def log_message(self, format, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

    def _dispatch(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api(parsed)
            return
        if parsed.path.startswith("/problem-assets/"):
            self._handle_problem_asset(parsed.path)
            return
        if parsed.path.startswith("/problem-demos/"):
            self._handle_problem_demo(parsed.path)
            return
        self._handle_static(parsed.path)

    def _handle_api(self, parsed):
        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("content-length", "0"))
            body = self.rfile.read(length) if length else b""

        if parsed.path.endswith("/run/stream"):
            self._handle_api_stream(parsed, body)
            return

        status, payload = handle_api_request(
            self.context,
            self.command,
            parsed.path,
            parse_qs(parsed.query),
            body,
        )
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _handle_api_stream(self, parsed, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        for event in stream_api_events(
            self.context,
            self.command,
            parsed.path,
            parse_qs(parsed.query),
            body,
        ):
            encoded = json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n"
            try:
                self.wfile.write(encoded)
                self.wfile.flush()
            except BrokenPipeError:
                break

    def _handle_static(self, request_path: str):
        path = request_path.strip("/")
        if not path:
            file_path = FRONTEND_DIR / "index.html"
        else:
            file_path = (FRONTEND_DIR / path).resolve()
            if not str(file_path).startswith(str(FRONTEND_DIR.resolve())) or not file_path.exists():
                file_path = FRONTEND_DIR / "index.html"

        if not file_path.exists():
            self.send_error(404, "Static asset not found")
            return

        self._send_file(file_path)

    def _handle_problem_asset(self, request_path: str):
        file_path = resolve_problem_asset(request_path)
        if file_path is None:
            self.send_error(404, "Problem asset not found")
            return
        self._send_file(file_path)

    def _handle_problem_demo(self, request_path: str):
        file_path = resolve_problem_demo(request_path)
        if file_path is None:
            self.send_error(404, "Problem demo not found")
            return
        self._send_file(
            file_path,
            {
                "Content-Security-Policy": PROBLEM_DEMO_CSP,
                "Cross-Origin-Resource-Policy": "same-origin",
                "X-Content-Type-Options": "nosniff",
            },
        )

    def _send_file(self, file_path: Path, extra_headers: dict[str, str] | None = None):
        data = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for header, value in (extra_headers or {}).items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    if DeepCodeHandler.context.user_state:
        DeepCodeHandler.context.user_state.ensure_exists()
    if DeepCodeHandler.context.custom_tests:
        DeepCodeHandler.context.custom_tests.ensure_exists()
    if DeepCodeHandler.context.activity_log:
        DeepCodeHandler.context.activity_log.ensure_exists()
    server = ThreadingHTTPServer((host, port), DeepCodeHandler)
    print(f"DeepCode is running at http://{host}:{port}")
    print(f"Problem folders: {PROBLEMS_DIR}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run DeepCode locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
