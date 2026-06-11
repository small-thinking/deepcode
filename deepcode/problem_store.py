from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


SUMMARY_FIELDS = (
    "id",
    "slug",
    "title",
    "category",
    "difficulty",
    "tags",
    "example",
    "environment",
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
        search: str | None = None,
        sort: str = "id",
    ) -> list[dict[str, Any]]:
        problems = [self._summary(problem) for problem in self._load_all()]

        if category and category.lower() not in {"all", "all categories"}:
            problems = [problem for problem in problems if problem.get("category") == category]
        if difficulty and difficulty.lower() not in {"all", "any"}:
            problems = [problem for problem in problems if problem.get("difficulty") == difficulty]
        if search:
            needle = search.casefold()
            problems = [
                problem
                for problem in problems
                if needle in problem.get("title", "").casefold()
                or needle in problem.get("category", "").casefold()
                or any(needle in tag.casefold() for tag in problem.get("tags", []))
            ]

        return sorted(problems, key=self._sort_key(sort))

    def categories(self) -> list[str]:
        return sorted({problem["category"] for problem in self._load_all() if problem.get("category")})

    def difficulties(self) -> list[str]:
        order = {"easy": 0, "medium": 1, "hard": 2}
        values = {problem["difficulty"] for problem in self._load_all() if problem.get("difficulty")}
        return sorted(values, key=lambda value: (order.get(value, 99), value))

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
            problem.setdefault("environment", {"language": "python", "timeout_seconds": 2, "packages": []})
            problem["tests"] = tests
            self._validate(problem, problem_dir)
            problems.append(problem)

        return sorted(problems, key=lambda problem: self._id_sort_value(problem.get("id")))

    def _summary(self, problem: dict[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(problem[key]) for key in SUMMARY_FIELDS if key in problem}

    def _sort_key(self, sort: str):
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}

        def key(problem: dict[str, Any]):
            if sort == "title":
                return problem.get("title", "").casefold()
            if sort == "category":
                return (problem.get("category", "").casefold(), self._id_sort_value(problem.get("id")))
            if sort == "difficulty":
                return (difficulty_order.get(problem.get("difficulty", ""), 99), self._id_sort_value(problem.get("id")))
            return self._id_sort_value(problem.get("id"))

        return key

    def _validate(self, problem: dict[str, Any], problem_dir: Path) -> None:
        required = ["id", "slug", "title", "category", "difficulty", "prompt", "starter_code", "example"]
        missing = [key for key in required if key not in problem]
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"{problem_dir} is missing required field(s): {missing_text}")

        if not isinstance(problem["tests"], list):
            raise ValueError(f"{problem_dir}/tests.json must contain a list")

        for index, test in enumerate(problem["tests"], start=1):
            for key in ("test", "expected_output"):
                if key not in test:
                    raise ValueError(f"{problem_dir}/tests.json test {index} is missing `{key}`")

    def _read_json(self, path: Path) -> Any:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def _id_sort_value(self, value: Any):
        text = str(value)
        return (0, int(text)) if text.isdigit() else (1, text.casefold())
