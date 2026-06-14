from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class CustomTestStore:
    """Read and write local-only user-authored ML coding tests."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def ensure_exists(self) -> None:
        if self.path.exists():
            return
        self._write({"problems": {}})

    def list_for(self, slug: str) -> list[dict[str, str]]:
        data = self._read()
        entry = data.get("problems", {}).get(slug, {})
        tests = entry.get("tests", []) if isinstance(entry, dict) else []
        if not isinstance(tests, list):
            raise ValueError(f"{self.path} custom tests for `{slug}` must be a list")
        return validate_custom_tests(tests)

    def replace_for(self, slug: str, tests: list[dict[str, Any]]) -> list[dict[str, str]]:
        validated = validate_custom_tests(tests)
        data = self._read()
        problems = data.setdefault("problems", {})
        problems[slug] = {"tests": validated}
        self._write(data)
        return self.list_for(slug)

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


def validate_custom_tests(tests: Any) -> list[dict[str, str]]:
    if not isinstance(tests, list):
        raise ValueError("`custom_tests` must be a list")

    validated = []
    for index, test in enumerate(tests, start=1):
        if not isinstance(test, dict):
            raise ValueError(f"`custom_tests[{index}]` must be an object")

        for key in ("test", "expected_output"):
            value = test.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"`custom_tests[{index}].{key}` must be a non-empty string")

        validated.append(
            {
                "name": _string_field(test, "name", f"Custom test {index}"),
                "input": _string_field(test, "input", ""),
                "test": str(test["test"]),
                "expected_output": str(test["expected_output"]),
            }
        )

    return deepcopy(validated)


def _string_field(test: dict[str, Any], key: str, default: str) -> str:
    value = test.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"`custom_tests[].{key}` must be a string")
    return value
