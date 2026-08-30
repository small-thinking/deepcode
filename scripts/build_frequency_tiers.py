#!/usr/bin/env python3
"""Build source-neutral interview-frequency tiers from a private snapshot.

The snapshot contains the current raw Seen Count values only long enough to
produce a patch-ready plan. This script never writes repository files or emits
raw counts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_KEYS = {"record_id", "company", "seen_count", "slug"}
LEGACY_COMPANY_LABELS = {
    "gdm": "Google DeepMind",
    "mistraai": "Mistral AI",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build source-neutral interview-frequency tiers from a private Notion snapshot."
    )
    parser.add_argument("snapshot", type=Path, help="Private JSON snapshot of linked Notion records")
    parser.add_argument("--problems-root", type=Path, required=True, help="Directory containing problem folders")
    parser.add_argument("--synced-at", default=date.today().isoformat(), help="ISO date to record in the plan")
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def normalized_seen_count(value: Any, record_id: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"record {record_id}: seen_count must be a non-negative integer or null")
    if not float(value).is_integer() or value < 0:
        fail(f"record {record_id}: seen_count must be a non-negative integer or null")
    return int(value)


def read_snapshot(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read snapshot: {error}") from error

    rows = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        fail("snapshot must be a non-empty JSON array or an object with a non-empty records array")

    normalized_rows = []
    record_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != REQUIRED_KEYS:
            fail(f"snapshot row {index} must contain exactly: {', '.join(sorted(REQUIRED_KEYS))}")
        record_id = row["record_id"]
        company = row["company"]
        slug = row["slug"]
        if not isinstance(record_id, str) or not record_id.strip():
            fail(f"snapshot row {index}: record_id must be a non-empty string")
        if not isinstance(company, str) or not company.strip():
            fail(f"record {record_id}: company must be a non-empty string")
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            fail(f"record {record_id}: slug is invalid")

        record_id = record_id.strip().casefold()
        if record_id in record_ids:
            fail(f"record {record_id}: duplicated stable source record id")
        record_ids.add(record_id)
        normalized_rows.append(
            {
                "record_id": record_id,
                "company": company.strip(),
                "seen_count": normalized_seen_count(row["seen_count"], record_id),
                "slug": slug,
            }
        )
    return normalized_rows


def tier_for(total: int) -> int:
    if total <= 0:
        return 0
    if total == 1:
        return 1
    if total <= 5:
        return 2
    if total <= 10:
        return 3
    if total <= 15:
        return 4
    return 5


def load_problems(root: Path) -> dict[str, dict[str, Any]]:
    problems: dict[str, dict[str, Any]] = {}
    for problem_path in sorted(root.glob("*/problem.json")):
        try:
            problem = json.loads(problem_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"could not read {problem_path}") from error
        slug = problem.get("slug")
        companies = problem.get("companies")
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            fail(f"{problem_path}: problem.json has an invalid slug")
        if not isinstance(companies, list) or not all(isinstance(company, str) and company.strip() for company in companies):
            fail(f"{slug}: problem.json must contain a non-empty companies list")
        if slug in problems:
            fail(f"duplicate problem slug: {slug}")
        problems[slug] = problem
    if not problems:
        fail("problems root contains no problem.json files")
    return problems


def canonical_company(companies: list[str], source_company: str) -> str:
    normalized_source = LEGACY_COMPANY_LABELS.get(source_company.casefold(), source_company)
    matching = [company for company in companies if company.casefold() == normalized_source.casefold()]
    return matching[0] if len(matching) == 1 else normalized_source


def build_plan(rows: list[dict[str, Any]], problems_root: Path, synced_at: str) -> dict[str, Any]:
    try:
        date.fromisoformat(synced_at)
    except ValueError as error:
        raise ValueError("synced_at must be an ISO date") from error

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    slug_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    problems = load_problems(problems_root)
    for row in rows:
        slug = row["slug"]
        if slug not in problems:
            fail(f"{slug}: no matching problem.json")
        company = canonical_company(problems[slug]["companies"], row["company"])
        normalized_row = {**row, "company": company}
        grouped[(slug, company)].append(normalized_row)
        slug_entries[slug].append(normalized_row)

    plan: dict[str, dict[str, Any]] = {}
    for (slug, company), entries in sorted(grouped.items()):
        plan.setdefault(slug, {"companies": list(problems[slug]["companies"]), "interview_frequency": {}})[
            "interview_frequency"
        ][company] = {
            "stars": tier_for(sum(entry["seen_count"] for entry in entries)),
            "source_record_ids": sorted(entry["record_id"] for entry in entries),
            "synced_at": synced_at,
        }
        if not any(existing.casefold() == company.casefold() for existing in plan[slug]["companies"]):
            plan[slug]["companies"].append(company)
    for slug, entries in plan.items():
        entries["interview_frequency_total"] = {
            "stars": tier_for(sum(row["seen_count"] for row in slug_entries[slug])),
            "synced_at": synced_at,
        }
    return {"problems": plan}


def main() -> int:
    args = parse_args()
    try:
        rows = read_snapshot(args.snapshot)
        plan = build_plan(rows, args.problems_root, args.synced_at)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
