from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SUMMARY_FIELDS = (
    "slug",
    "name",
    "aliases",
    "summary",
    "stage",
    "updated_at",
)

BUSINESS_SNAPSHOT_FIELDS = (
    "founded",
    "team_size",
    "arr_or_revenue",
    "valuation",
    "latest_financing",
)


class CompanyStore:
    """Read company research profiles and link them to the problem catalog."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def list_companies(self, problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        companies = []
        for company in self._load_all():
            summary = {key: deepcopy(company[key]) for key in SUMMARY_FIELDS if key in company}
            summary["problem_count"] = len(self._related_problems(company, problems))
            companies.append(summary)
        return sorted(companies, key=lambda company: company["name"].casefold())

    def get_company(self, identifier: str, problems: list[dict[str, Any]]) -> dict[str, Any]:
        for company in self._load_all():
            if identifier.casefold() in {value.casefold() for value in self._identifiers(company)}:
                result = deepcopy(company)
                result["related_problems"] = self._related_problems(company, problems)
                result["problem_count"] = len(result["related_problems"])
                return result
        raise KeyError(identifier)

    def _load_all(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []

        companies = []
        for path in sorted(self.root.glob("*.json")):
            with path.open(encoding="utf-8") as file:
                company = json.load(file)
            self._validate(company, path)
            companies.append(company)
        return companies

    def _related_problems(self, company: dict[str, Any], problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        company_names = {value.casefold() for value in self._identifiers(company)}
        related = [
            {
                key: deepcopy(problem[key])
                for key in ("display_id", "id", "slug", "title", "category", "difficulty", "tags", "companies")
                if key in problem
            }
            for problem in problems
            if any(str(value).casefold() in company_names for value in problem.get("companies", []))
        ]
        return sorted(related, key=lambda problem: (problem.get("display_id", 0), str(problem.get("title", "")).casefold()))

    @staticmethod
    def _identifiers(company: dict[str, Any]) -> list[str]:
        return [company["slug"], company["name"], *company.get("aliases", [])]

    def _validate(self, company: dict[str, Any], path: Path) -> None:
        if not isinstance(company, dict):
            raise ValueError(f"{path} must contain a JSON object")

        for key in ("slug", "name", "summary", "stage"):
            if key not in company:
                raise ValueError(f"{path} is missing required field `{key}`")
        for key in ("slug", "name", "summary"):
            if not isinstance(company[key], str) or not company[key].strip():
                raise ValueError(f"{path} field `{key}` must be a non-empty string")

        aliases = company.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases):
            raise ValueError(f"{path} field `aliases` must be a list of non-empty strings")

        stage = company["stage"]
        if not isinstance(stage, dict):
            raise ValueError(f"{path} field `stage` must be an object")
        for key in ("company_state", "funding_stage"):
            if not isinstance(stage.get(key), str) or not stage[key].strip():
                raise ValueError(f"{path} field `stage.{key}` must be a non-empty string")
        if "source" in stage:
            self._validate_links(stage["source"], f"{path} field `stage.source`", allow_single=True)

        snapshot = company.get("business_snapshot")
        if snapshot is not None:
            if not isinstance(snapshot, dict):
                raise ValueError(f"{path} field `business_snapshot` must be an object")
            for key in BUSINESS_SNAPSHOT_FIELDS:
                if not isinstance(snapshot.get(key), str) or not snapshot[key].strip():
                    raise ValueError(f"{path} field `business_snapshot.{key}` must be a non-empty string")
            self._validate_links(snapshot.get("sources", []), f"{path} field `business_snapshot.sources`")

        self._validate_links(company.get("links", []), f"{path} field `links`")
        self._validate_links(company.get("references", []), f"{path} field `references`")

        interview = company.get("interview_process", {})
        if interview and not isinstance(interview, dict):
            raise ValueError(f"{path} field `interview_process` must be an object")
        if isinstance(interview, dict):
            stages = interview.get("stages", [])
            if not isinstance(stages, list):
                raise ValueError(f"{path} field `interview_process.stages` must be a list")
            for index, stage_item in enumerate(stages, start=1):
                if not isinstance(stage_item, dict):
                    raise ValueError(f"{path} interview stage {index} must be an object")
                for key in ("name", "signal", "evidence_tier"):
                    if not isinstance(stage_item.get(key), str) or not stage_item[key].strip():
                        raise ValueError(f"{path} interview stage {index} field `{key}` must be a non-empty string")
                self._validate_links(stage_item.get("sources", []), f"{path} interview stage {index} field `sources`")

    def _validate_links(self, links: Any, label: str, allow_single: bool = False) -> None:
        items = [links] if allow_single and isinstance(links, dict) else links
        if not isinstance(items, list):
            raise ValueError(f"{label} must be a list")
        for index, link in enumerate(items, start=1):
            if not isinstance(link, dict):
                raise ValueError(f"{label}[{index}] must be an object")
            if not isinstance(link.get("label"), str) or not link["label"].strip():
                raise ValueError(f"{label}[{index}].label must be a non-empty string")
            if not self._is_http_url(link.get("url")):
                raise ValueError(f"{label}[{index}].url must be http(s)")

    @staticmethod
    def _is_http_url(value: Any) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
