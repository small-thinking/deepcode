from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class UserStateStore:
    """Read and write local-only user progress for problems."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def ensure_exists(self) -> None:
        if self.path.exists():
            return
        self._write({"problems": {}})

    def annotate(self, problem: dict[str, Any]) -> dict[str, Any]:
        annotated = deepcopy(problem)
        annotated["personal_status"] = self.status_for(str(problem.get("slug", "")))
        return annotated

    def status_for(self, slug: str) -> dict[str, Any]:
        data = self._read()
        status = data.get("problems", {}).get(slug, {})
        return {"completed": bool(status.get("completed")), "completed_at": status.get("completed_at")}

    def mark_completed(self, slug: str) -> dict[str, Any]:
        data = self._read()
        problems = data.setdefault("problems", {})
        status = problems.setdefault(slug, {})
        status["completed"] = True
        status["completed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        self._write(data)
        return self.status_for(slug)

    def reset_problem(self, slug: str) -> dict[str, Any]:
        data = self._read()
        data.setdefault("problems", {}).pop(slug, None)
        self._write(data)
        return self.status_for(slug)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"problems": {}}

        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"{self.path} must contain valid JSON") from error

        if not isinstance(data, dict):
            raise ValueError(f"{self.path} must contain a JSON object")
        problems = data.setdefault("problems", {})
        if not isinstance(problems, dict):
            raise ValueError(f"{self.path} field `problems` must be an object")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
            file.write("\n")
