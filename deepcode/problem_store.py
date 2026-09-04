from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SUMMARY_FIELDS = (
    "id",
    "display_id",
    "slug",
    "title",
    "category",
    "difficulty",
    "tags",
    "companies",
    "interview_frequency",
    "interview_frequency_total",
    "example",
    "evaluation",
    "environment",
    "references",
    "created_at",
)

PROBLEM_ASSET_SUFFIXES = frozenset({".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"})
SYSTEM_DESIGN_ASSET_SECTIONS = frozenset({"prompt", "reference_answer"})
PROBLEM_DEMO_SUFFIXES = frozenset({".html"})
PROBLEM_DEMO_SCHEMA_VERSION = 1
PROBLEM_DEMO_KINDS = frozenset({"standalone_html"})
PROBLEM_DEMO_THEMES = frozenset({"sync", "light", "dark"})
PROBLEM_DEMO_FALLBACK_THEMES = frozenset({"light", "dark"})
PROBLEM_DEMO_HEIGHT_MODES = frozenset({"content", "fixed"})
PROBLEM_DEMO_MIN_HEIGHT = 320
PROBLEM_DEMO_MAX_HEIGHT = 1000
PROBLEM_DEMO_FIELDS = frozenset(
    {"schema_version", "id", "kind", "path", "title", "section", "presentation"}
)
PROBLEM_DEMO_PRESENTATION_FIELDS = frozenset(
    {"theme", "fallback_theme", "height", "fallback_height"}
)

# Keep source labels on each problem intact while exposing one selector for the
# SpaceX/xAI scope that is curated in the Company Hub.
COMPANY_FACET_LABELS = {
    "spacex": "SpaceXAI / xAI-related roles",
    "xai": "SpaceXAI / xAI-related roles",
    "spacexai / xai-related roles": "SpaceXAI / xAI-related roles",
    "spacexai-xai-related-roles": "SpaceXAI / xAI-related roles",
}


class ProblemStore:
    """Read problem folders from disk.

    Each direct child folder needs a `problem.json` file and may include a
    separate `tests.json` file so large test payloads stay out of metadata.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def list_problems(
        self,
        category: str | None = None,
        difficulty: str | None = None,
        company: str | None = None,
        search: str | None = None,
        sort: str = "id",
        order: str = "asc",
    ) -> list[dict[str, Any]]:
        problems = [self._summary(problem) for problem in self._load_all()]

        if category and category.lower() not in {"all", "all categories"}:
            problems = [problem for problem in problems if problem.get("category") == category]
        if difficulty and difficulty.lower() not in {"all", "any"}:
            problems = [problem for problem in problems if problem.get("difficulty") == difficulty]
        if company and company.casefold() not in {"all", "all companies"}:
            company_key = self._canonical_company_label(company).casefold()
            problems = [
                problem
                for problem in problems
                if any(
                    self._canonical_company_label(str(value)).casefold() == company_key
                    for value in problem.get("companies", [])
                )
            ]
        if search:
            needle = search.casefold()
            problems = [
                problem
                for problem in problems
                if needle in problem.get("title", "").casefold()
                or needle in problem.get("category", "").casefold()
                or any(needle in tag.casefold() for tag in problem.get("tags", []))
                or any(
                    needle in str(value).casefold()
                    or needle in self._canonical_company_label(str(value)).casefold()
                    for value in problem.get("companies", [])
                )
            ]

        return sorted(problems, key=self._sort_key(sort), reverse=order.casefold() == "desc")

    def categories(self) -> list[str]:
        return sorted({problem["category"] for problem in self._load_all() if problem.get("category")})

    def difficulties(self) -> list[str]:
        order = {"easy": 0, "medium": 1, "hard": 2}
        values = {problem["difficulty"] for problem in self._load_all() if problem.get("difficulty")}
        return sorted(values, key=lambda value: (order.get(value, 99), value))

    def companies(self) -> list[str]:
        """Return the stable, display-ready company labels used by the catalog."""
        return sorted(
            {
                self._canonical_company_label(company)
                for problem in self._load_all()
                for company in problem.get("companies", [])
                if isinstance(company, str) and company.strip()
            },
            key=str.casefold,
        )

    def company_counts(self) -> dict[str, int]:
        """Return each display company label and its total number of catalog problems."""
        labels = self.companies()
        labels_by_key = {label.casefold(): label for label in labels}
        counts = {label: 0 for label in labels}

        for problem in self._load_all():
            seen = set()
            for company in problem.get("companies", []):
                if not isinstance(company, str) or not company.strip():
                    continue
                label = self._canonical_company_label(company)
                key = label.casefold()
                if key in seen:
                    continue
                seen.add(key)
                display_label = labels_by_key.get(key)
                if display_label:
                    counts[display_label] += 1

        return counts

    @staticmethod
    def _canonical_company_label(company: str) -> str:
        return COMPANY_FACET_LABELS.get(company.casefold(), company)

    def get_problem(self, identifier: str) -> dict[str, Any]:
        for problem in self._load_all():
            if identifier in {problem.get("slug"), str(problem.get("id"))}:
                return deepcopy(problem)
        raise KeyError(identifier)

    def _load_all(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []

        problems = []
        for problem_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            metadata_path = problem_dir / "problem.json"
            if not metadata_path.exists():
                continue

            problem = self._read_json(metadata_path)
            tests_path = problem_dir / "tests.json"
            tests = self._read_json(tests_path) if tests_path.exists() else []
            problem.setdefault("slug", problem_dir.name)
            problem.setdefault("tags", [])
            problem.setdefault("companies", [])
            problem.setdefault("evaluation", {"type": "ml_coding"})
            problem.setdefault("environment", {"language": "python", "timeout_seconds": 2, "packages": []})
            problem["tests"] = tests
            problem["_runtime"] = self._runtime_paths(problem, problem_dir)
            self._validate(problem, problem_dir)
            problems.append(problem)

        sorted_problems = sorted(problems, key=lambda problem: self._id_sort_value(problem.get("id")))
        for display_id, problem in enumerate(sorted_problems, start=1):
            problem["display_id"] = display_id
        return sorted_problems

    def _summary(self, problem: dict[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(problem[key]) for key in SUMMARY_FIELDS if key in problem}

    def _sort_key(self, sort: str):
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}

        def key(problem: dict[str, Any]):
            if sort == "title":
                return problem.get("title", "").casefold()
            if sort == "category":
                return problem.get("category", "").casefold()
            if sort == "difficulty":
                return difficulty_order.get(problem.get("difficulty", ""), 99)
            if sort == "frequency":
                return self._frequency_sort_value(problem)
            return self._id_sort_value(problem.get("id"))

        return key

    @staticmethod
    def _frequency_sort_value(problem: dict[str, Any]) -> int:
        """Use the combined cross-company tier for the catalog Stars column."""
        total = problem.get("interview_frequency_total")
        if isinstance(total, dict) and isinstance(total.get("stars"), int):
            return total["stars"]

        # Compatibility for problems not yet refreshed from the canonical bank.
        frequencies = problem.get("interview_frequency")
        if not isinstance(frequencies, dict):
            return 0
        return max(
            (
                entry.get("stars", 0)
                for entry in frequencies.values()
                if isinstance(entry, dict) and isinstance(entry.get("stars", 0), int)
            ),
            default=0,
        )

    def _validate(self, problem: dict[str, Any], problem_dir: Path) -> None:
        evaluation = problem.get("evaluation")
        evaluation_type = evaluation.get("type", "ml_coding") if isinstance(evaluation, dict) else "ml_coding"
        required = ["id", "slug", "title", "category", "difficulty", "prompt"]
        if evaluation_type == "system_design":
            required.append("response")
        else:
            required.extend(["starter_code", "example"])
        missing = [key for key in required if key not in problem]
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"{problem_dir} is missing required field(s): {missing_text}")

        if not isinstance(problem["evaluation"], dict):
            raise ValueError(f"{problem_dir}/problem.json field `evaluation` must be an object")
        evaluation_type = problem["evaluation"].get("type", "ml_coding")
        if not isinstance(evaluation_type, str) or not evaluation_type.strip():
            raise ValueError(f"{problem_dir}/problem.json field `evaluation.type` must be a non-empty string")

        if not isinstance(problem["tests"], list):
            raise ValueError(f"{problem_dir}/tests.json must contain a list")

        if evaluation_type == "ml_coding":
            for index, test in enumerate(problem["tests"], start=1):
                for key in ("test", "expected_output"):
                    if key not in test:
                        raise ValueError(f"{problem_dir}/tests.json test {index} is missing `{key}`")
        if evaluation_type in {"ml_modeling", "ml_torch_modeling", "ml_torch_lab"}:
            for index, test in enumerate(problem["tests"], start=1):
                if "test" not in test:
                    raise ValueError(f"{problem_dir}/tests.json test {index} is missing `test`")
        if evaluation_type == "ml_torch_lab":
            self._validate_lab_harness(problem, problem_dir)
        if evaluation_type == "system_design":
            self._validate_system_design_response(problem, problem_dir)

        self._validate_relative_path(problem, problem_dir, "data", "path")
        self._validate_relative_path(problem, problem_dir, "artifacts", "results_path")
        self._validate_companies(problem, problem_dir)
        self._validate_interview_frequency(problem, problem_dir)
        self._validate_interview_frequency_total(problem, problem_dir)
        self._validate_references(problem, problem_dir)
        self._validate_assets(problem, problem_dir)
        self._validate_interactive_demos(problem, problem_dir, evaluation_type)

    def _validate_system_design_response(self, problem: dict[str, Any], problem_dir: Path) -> None:
        response = problem.get("response")
        if not isinstance(response, dict):
            raise ValueError(f"{problem_dir}/problem.json field `response` must be an object")
        for key in ("placeholder", "reference_answer"):
            value = response.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{problem_dir}/problem.json field `response.{key}` must be a non-empty string")

    def _validate_assets(self, problem: dict[str, Any], problem_dir: Path) -> None:
        assets = problem.get("assets")
        if assets is None:
            return
        if not isinstance(assets, list):
            raise ValueError(f"{problem_dir}/problem.json field `assets` must be a list")

        for index, asset in enumerate(assets, start=1):
            if not isinstance(asset, dict):
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}]` must be an object")
            path_value = asset.get("path")
            alt = asset.get("alt")
            section = asset.get("section")
            if not isinstance(path_value, str) or not path_value.strip():
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}].path` must be a non-empty string")
            if not isinstance(alt, str) or not alt.strip():
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}].alt` must be a non-empty string")
            if section not in SYSTEM_DESIGN_ASSET_SECTIONS:
                raise ValueError(
                    f"{problem_dir}/problem.json field `assets[{index}].section` must be prompt or reference_answer"
                )
            if "caption" in asset and not isinstance(asset["caption"], str):
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}].caption` must be a string")

            asset_path = Path(path_value)
            if asset_path.is_absolute() or ".." in asset_path.parts or not asset_path.parts or asset_path.parts[0] != "assets":
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}].path` must be under assets/")
            if asset_path.suffix.casefold() not in PROBLEM_ASSET_SUFFIXES:
                suffixes = ", ".join(sorted(PROBLEM_ASSET_SUFFIXES))
                raise ValueError(f"{problem_dir}/problem.json field `assets[{index}].path` must use one of: {suffixes}")
            if not (problem_dir / asset_path).is_file():
                raise ValueError(f"{problem_dir}/problem.json asset not found: {path_value}")

    def _validate_interactive_demos(
        self,
        problem: dict[str, Any],
        problem_dir: Path,
        evaluation_type: str,
    ) -> None:
        demos = problem.get("interactive_demos")
        if demos is None:
            return
        if evaluation_type != "system_design":
            raise ValueError(
                f"{problem_dir}/problem.json field `interactive_demos` is only supported for system_design problems"
            )
        if not isinstance(demos, list):
            raise ValueError(f"{problem_dir}/problem.json field `interactive_demos` must be a list")

        demo_ids = set()
        for index, demo in enumerate(demos, start=1):
            field = f"interactive_demos[{index}]"
            if not isinstance(demo, dict):
                raise ValueError(f"{problem_dir}/problem.json field `{field}` must be an object")

            missing_fields = PROBLEM_DEMO_FIELDS - demo.keys()
            if missing_fields:
                missing = ", ".join(sorted(missing_fields))
                raise ValueError(f"{problem_dir}/problem.json field `{field}` is missing: {missing}")
            unknown_fields = demo.keys() - PROBLEM_DEMO_FIELDS
            if unknown_fields:
                unknown = ", ".join(sorted(unknown_fields))
                raise ValueError(f"{problem_dir}/problem.json field `{field}` has unsupported fields: {unknown}")

            schema_version = demo.get("schema_version")
            demo_id = demo.get("id")
            kind = demo.get("kind")
            path_value = demo.get("path")
            title = demo.get("title")
            section = demo.get("section")
            presentation = demo.get("presentation")

            if schema_version != PROBLEM_DEMO_SCHEMA_VERSION or isinstance(schema_version, bool):
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.schema_version` must be "
                    f"{PROBLEM_DEMO_SCHEMA_VERSION}"
                )
            if not isinstance(demo_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", demo_id):
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.id` must be a lowercase kebab-case identifier"
                )
            if demo_id in demo_ids:
                raise ValueError(f"{problem_dir}/problem.json field `{field}.id` must be unique")
            demo_ids.add(demo_id)
            if not isinstance(kind, str) or kind not in PROBLEM_DEMO_KINDS:
                kinds = ", ".join(sorted(PROBLEM_DEMO_KINDS))
                raise ValueError(f"{problem_dir}/problem.json field `{field}.kind` must be one of: {kinds}")

            if not isinstance(path_value, str) or not path_value.strip():
                raise ValueError(f"{problem_dir}/problem.json field `{field}.path` must be a non-empty string")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"{problem_dir}/problem.json field `{field}.title` must be a non-empty string")
            if section != "reference_answer":
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.section` must be reference_answer"
                )
            if not isinstance(presentation, dict):
                raise ValueError(f"{problem_dir}/problem.json field `{field}.presentation` must be an object")

            missing_presentation_fields = PROBLEM_DEMO_PRESENTATION_FIELDS - presentation.keys()
            if missing_presentation_fields:
                missing = ", ".join(sorted(missing_presentation_fields))
                raise ValueError(f"{problem_dir}/problem.json field `{field}.presentation` is missing: {missing}")
            unknown_presentation_fields = presentation.keys() - PROBLEM_DEMO_PRESENTATION_FIELDS
            if unknown_presentation_fields:
                unknown = ", ".join(sorted(unknown_presentation_fields))
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.presentation` has unsupported fields: {unknown}"
                )

            theme = presentation.get("theme")
            fallback_theme = presentation.get("fallback_theme")
            height_mode = presentation.get("height")
            fallback_height = presentation.get("fallback_height")
            if not isinstance(theme, str) or theme not in PROBLEM_DEMO_THEMES:
                themes = ", ".join(sorted(PROBLEM_DEMO_THEMES))
                raise ValueError(f"{problem_dir}/problem.json field `{field}.presentation.theme` must be one of: {themes}")
            if not isinstance(fallback_theme, str) or fallback_theme not in PROBLEM_DEMO_FALLBACK_THEMES:
                themes = ", ".join(sorted(PROBLEM_DEMO_FALLBACK_THEMES))
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.presentation.fallback_theme` must be one of: {themes}"
                )
            if not isinstance(height_mode, str) or height_mode not in PROBLEM_DEMO_HEIGHT_MODES:
                modes = ", ".join(sorted(PROBLEM_DEMO_HEIGHT_MODES))
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.presentation.height` must be one of: {modes}"
                )
            if isinstance(fallback_height, bool) or not isinstance(fallback_height, int):
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.presentation.fallback_height` must be an integer"
                )
            if not PROBLEM_DEMO_MIN_HEIGHT <= fallback_height <= PROBLEM_DEMO_MAX_HEIGHT:
                raise ValueError(
                    f"{problem_dir}/problem.json field `{field}.presentation.fallback_height` must be between "
                    f"{PROBLEM_DEMO_MIN_HEIGHT} and {PROBLEM_DEMO_MAX_HEIGHT}"
                )

            demo_path = Path(path_value)
            if demo_path.is_absolute() or ".." in demo_path.parts or not demo_path.parts or demo_path.parts[0] != "assets":
                raise ValueError(f"{problem_dir}/problem.json field `{field}.path` must be under assets/")
            if demo_path.suffix.casefold() not in PROBLEM_DEMO_SUFFIXES:
                suffixes = ", ".join(sorted(PROBLEM_DEMO_SUFFIXES))
                raise ValueError(f"{problem_dir}/problem.json field `{field}.path` must use one of: {suffixes}")
            if not (problem_dir / demo_path).is_file():
                raise ValueError(f"{problem_dir}/problem.json interactive demo not found: {path_value}")

    def _read_json(self, path: Path) -> Any:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def _runtime_paths(self, problem: dict[str, Any], problem_dir: Path) -> dict[str, str]:
        runtime_problem_dir = problem_dir if problem_dir.is_absolute() else Path.cwd() / problem_dir
        runtime = {"problem_dir": str(runtime_problem_dir)}
        data = problem.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("path"), str) and data["path"].strip():
            runtime["data_path"] = str(runtime_problem_dir / data["path"])

        artifacts = problem.get("artifacts", {})
        if (
            isinstance(artifacts, dict)
            and isinstance(artifacts.get("results_path"), str)
            and artifacts["results_path"].strip()
        ):
            runtime["results_path"] = str(runtime_problem_dir / artifacts["results_path"])
        return runtime

    def _validate_relative_path(self, problem: dict[str, Any], problem_dir: Path, section: str, key: str) -> None:
        value = problem.get(section)
        if value is None:
            return
        if not isinstance(value, dict):
            raise ValueError(f"{problem_dir}/problem.json field `{section}` must be an object")
        if key not in value:
            return

        raw_path = value[key]
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"{problem_dir}/problem.json field `{section}.{key}` must be a non-empty string")

        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{problem_dir}/problem.json field `{section}.{key}` must be problem-relative")

    def _validate_lab_harness(self, problem: dict[str, Any], problem_dir: Path) -> None:
        evaluation = problem["evaluation"]
        harness = evaluation.get("harness")
        if not isinstance(harness, str) or not harness.strip():
            raise ValueError(f"{problem_dir}/problem.json field `evaluation.harness` must be a non-empty string")

        path = Path(harness)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{problem_dir}/problem.json field `evaluation.harness` must be problem-relative")

        if not (problem_dir / path).is_file():
            raise ValueError(f"{problem_dir}/problem.json Lab harness not found: {harness}")

    def _validate_references(self, problem: dict[str, Any], problem_dir: Path) -> None:
        references = problem.get("references")
        if references is None:
            return
        if not isinstance(references, list):
            raise ValueError(f"{problem_dir}/problem.json field `references` must be a list")

        for index, reference in enumerate(references, start=1):
            if not isinstance(reference, dict):
                raise ValueError(f"{problem_dir}/problem.json field `references[{index}]` must be an object")

            label = reference.get("label")
            url = reference.get("url")
            if not isinstance(label, str) or not label.strip():
                raise ValueError(f"{problem_dir}/problem.json field `references[{index}].label` must be non-empty")
            if not isinstance(url, str) or not url.strip():
                raise ValueError(f"{problem_dir}/problem.json field `references[{index}].url` must be non-empty")

            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"{problem_dir}/problem.json field `references[{index}].url` must be http(s)")

    def _validate_companies(self, problem: dict[str, Any], problem_dir: Path) -> None:
        companies = problem.get("companies")
        if companies is None:
            return
        if not isinstance(companies, list):
            raise ValueError(f"{problem_dir}/problem.json field `companies` must be a list")

        for index, company in enumerate(companies, start=1):
            if not isinstance(company, str) or not company.strip():
                raise ValueError(f"{problem_dir}/problem.json field `companies[{index}]` must be non-empty")

    def _validate_interview_frequency(self, problem: dict[str, Any], problem_dir: Path) -> None:
        frequency = problem.get("interview_frequency")
        if frequency is None:
            return
        if not isinstance(frequency, dict) or not frequency:
            raise ValueError(f"{problem_dir}/problem.json field `interview_frequency` must be a non-empty object")

        company_labels = {
            company.casefold()
            for company in problem.get("companies", [])
            if isinstance(company, str) and company.strip()
        }
        for company, entry in frequency.items():
            if not isinstance(company, str) or not company.strip() or company.casefold() not in company_labels:
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency` has an unknown company")
            if not isinstance(entry, dict) or set(entry) != {"stars", "source_record_ids", "synced_at"}:
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency.{company}` has an invalid shape")

            stars = entry["stars"]
            if isinstance(stars, bool) or not isinstance(stars, int) or not 0 <= stars <= 5:
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency.{company}.stars` must be an integer from 0 to 5")

            record_ids = entry["source_record_ids"]
            if (
                not isinstance(record_ids, list)
                or not record_ids
                or any(not isinstance(record_id, str) or not record_id.strip() for record_id in record_ids)
                or len({record_id.casefold() for record_id in record_ids}) != len(record_ids)
            ):
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency.{company}.source_record_ids` must be unique non-empty strings")

            synced_at = entry["synced_at"]
            if not isinstance(synced_at, str):
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency.{company}.synced_at` must be an ISO date")
            try:
                date.fromisoformat(synced_at)
            except ValueError as error:
                raise ValueError(f"{problem_dir}/problem.json field `interview_frequency.{company}.synced_at` must be an ISO date") from error

    def _validate_interview_frequency_total(self, problem: dict[str, Any], problem_dir: Path) -> None:
        total = problem.get("interview_frequency_total")
        if total is None:
            return
        if not isinstance(total, dict) or set(total) != {"stars", "synced_at"}:
            raise ValueError(f"{problem_dir}/problem.json field `interview_frequency_total` has an invalid shape")

        stars = total["stars"]
        if isinstance(stars, bool) or not isinstance(stars, int) or not 0 <= stars <= 5:
            raise ValueError(f"{problem_dir}/problem.json field `interview_frequency_total.stars` must be an integer from 0 to 5")

        synced_at = total["synced_at"]
        if not isinstance(synced_at, str):
            raise ValueError(f"{problem_dir}/problem.json field `interview_frequency_total.synced_at` must be an ISO date")
        try:
            date.fromisoformat(synced_at)
        except ValueError as error:
            raise ValueError(f"{problem_dir}/problem.json field `interview_frequency_total.synced_at` must be an ISO date") from error

    def _id_sort_value(self, value: Any):
        text = str(value)
        return (0, int(text)) if text.isdigit() else (1, text.casefold())
