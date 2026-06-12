from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from deepcode.api import ApiContext, handle_api_request
from deepcode.problem_store import ProblemStore
from deepcode.user_state import UserStateStore


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
PROBLEMS_DIR = BASE_DIR / "problems"
USER_STATE_PATH = Path(os.environ.get("DEEPCODE_USER_STATE_PATH", BASE_DIR / ".deepcode" / "user-state.json"))


class DeepCodeHandler(BaseHTTPRequestHandler):
    context = ApiContext(store=ProblemStore(PROBLEMS_DIR), user_state=UserStateStore(USER_STATE_PATH))

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def log_message(self, format, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

    def _dispatch(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api(parsed)
            return
        self._handle_static(parsed.path)

    def _handle_api(self, parsed):
        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("content-length", "0"))
            body = self.rfile.read(length) if length else b""

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

        data = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "127.0.0.1", port: int = 8000):
    if DeepCodeHandler.context.user_state:
        DeepCodeHandler.context.user_state.ensure_exists()
    server = ThreadingHTTPServer((host, port), DeepCodeHandler)
    print(f"DeepCode is running at http://{host}:{port}")
    print(f"Problem folders: {PROBLEMS_DIR}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run DeepCode locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
