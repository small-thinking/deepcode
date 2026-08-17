from __future__ import annotations

import json
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
    "example",
    "evaluation",
    "environment",
    "references",
    "created_at",
)


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
            company_key = company.casefold()
            problems = [
                problem
                for problem in problems
                if any(str(value).casefold() == company_key for value in problem.get("companies", []))
            ]
        if search:
            needle = search.casefold()
            problems = [
                problem
                for problem in problems
                if needle in problem.get("title", "").casefold()
                or needle in problem.get("category", "").casefold()
                or any(needle in tag.casefold() for tag in problem.get("tags", []))
                or any(needle in company.casefold() for company in problem.get("companies", []))
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
                company
                for problem in self._load_all()
                for company in problem.get("companies", [])
                if isinstance(company, str) and company.strip()
            },
            key=str.casefold,
        )

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
        """Use the highest company-specific tier for the catalog Stars column."""
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
        required = ["id", "slug", "title", "category", "difficulty", "prompt", "starter_code", "example"]
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

        self._validate_relative_path(problem, problem_dir, "data", "path")
        self._validate_relative_path(problem, problem_dir, "artifacts", "results_path")
        self._validate_companies(problem, problem_dir)
        self._validate_interview_frequency(problem, problem_dir)
        self._validate_references(problem, problem_dir)

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

    def _id_sort_value(self, value: Any):
        text = str(value)
        return (0, int(text)) if text.isdigit() else (1, text.casefold())
