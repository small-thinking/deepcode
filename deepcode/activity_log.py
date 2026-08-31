"""Append-only local practice activity storage for the Progress dashboard."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


VALID_SCOPES = {"full", "selected", "custom"}
VALID_OUTCOMES = {"passed", "not_passed"}


class ActivityLogStore:
    """Persist timestamped evaluation events without storing submitted code."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def ensure_exists(self) -> None:
        if not self.path.exists():
            self._write({"events": []})

    def record_submission(
        self,
        problem: dict[str, Any],
        *,
        scope: str,
        result: dict[str, Any],
        at: str | None = None,
    ) -> dict[str, Any]:
        """Record one completed evaluator run, including repeat attempts."""
        if scope not in VALID_SCOPES:
            raise ValueError(f"Unsupported activity scope: {scope}")

        outcome = "passed" if result.get("passed") else "not_passed"
        event = self._new_event(
            problem,
            at=at or _now_iso(),
            source="live_run",
            scope=scope,
            outcome=outcome,
            passed=_nonnegative_int(result.get("passed")),
            total=_nonnegative_int(result.get("total")),
        )
        payload = self._read()
        payload["events"].append(event)
        self._write(payload)
        return deepcopy(event)

    def backfill_problem_statuses(self, problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add one transparent legacy event for each status timestamp we know.

        Older state files only know a completion timestamp and the latest full-suite
        status.  Backfilling those facts makes the timeline useful without inventing
        historical attempts, selected-test runs, or test counts.
        """
        payload = self._read()
        events = payload["events"]
        existing = {
            (event.get("problem_slug"), event.get("at"), event.get("outcome"))
            for event in events
            if isinstance(event, dict)
        }
        added: list[dict[str, Any]] = []

        for problem in problems:
            personal_status = problem.get("personal_status")
            if not isinstance(personal_status, dict):
                continue

            completed_at = personal_status.get("completed_at")
            if isinstance(completed_at, str):
                event = self._backfill_event(problem, completed_at, "passed")
                if self._add_if_missing(events, existing, event):
                    added.append(event)

            last_submission = personal_status.get("last_submission")
            if not isinstance(last_submission, dict):
                continue
            submission_at = last_submission.get("at")
            submission_status = last_submission.get("status")
            if not isinstance(submission_at, str):
                continue
            outcome = "passed" if submission_status == "passed" else "not_passed"
            event = self._backfill_event(problem, submission_at, outcome)
            if self._add_if_missing(events, existing, event):
                added.append(event)

        if added:
            self._write(payload)
        return deepcopy(added)

    def list_events(self) -> list[dict[str, Any]]:
        events = self._read()["events"]
        return sorted(deepcopy(events), key=lambda event: str(event.get("at", "")), reverse=True)

    def _backfill_event(
        self,
        problem: dict[str, Any],
        at: str,
        outcome: str,
    ) -> dict[str, Any]:
        return self._new_event(
            problem,
            at=at,
            source="status_backfill",
            scope="full",
            outcome=outcome,
            passed=None,
            total=None,
        )

    def _new_event(
        self,
        problem: dict[str, Any],
        *,
        at: str,
        source: str,
        scope: str,
        outcome: str,
        passed: int | None,
        total: int | None,
    ) -> dict[str, Any]:
        if outcome not in VALID_OUTCOMES:
            raise ValueError(f"Unsupported activity outcome: {outcome}")
        companies = problem.get("companies")
        return {
            "id": str(uuid4()),
            "at": at,
            "source": source,
            "kind": "submission",
            "scope": scope,
            "outcome": outcome,
            "passed": passed,
            "total": total,
            "problem_slug": problem.get("slug"),
            "title": problem.get("title"),
            "category": problem.get("category"),
            "difficulty": problem.get("difficulty"),
            "companies": list(companies) if isinstance(companies, list) else [],
        }

    @staticmethod
    def _add_if_missing(
        events: list[dict[str, Any]],
        existing: set[tuple[Any, Any, Any]],
        event: dict[str, Any],
    ) -> bool:
        identity = (event["problem_slug"], event["at"], event["outcome"])
        if identity in existing:
            return False
        events.append(event)
        existing.add(identity)
        return True

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        self.ensure_exists()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"events": []}
        events = payload.get("events") if isinstance(payload, dict) else None
        if not isinstance(events, list):
            return {"events": []}
        return {"events": [event for event in events if isinstance(event, dict)]}

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value >= 0 else None
