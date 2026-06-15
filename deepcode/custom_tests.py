from __future__ import annotations

import ast
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

    def list_for(self, slug: str) -> list[dict[str, Any]]:
        data = self._read()
        entry = data.get("problems", {}).get(slug, {})
        tests = entry.get("tests", []) if isinstance(entry, dict) else []
        if not isinstance(tests, list):
            raise ValueError(f"{self.path} custom tests for `{slug}` must be a list")
        return validate_custom_tests(tests)

    def replace_for(
        self,
        slug: str,
        tests: list[dict[str, Any]],
        problem: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        validated = validate_custom_tests(tests, problem=problem)
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


def validate_custom_tests(tests: Any, problem: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not isinstance(tests, list):
        raise ValueError("`custom_tests` must be a list")

    validated = []
    for index, test in enumerate(tests, start=1):
        if not isinstance(test, dict):
            raise ValueError(f"`custom_tests[{index}]` must be an object")

        if _uses_argument_mode(test):
            if problem is not None:
                validated.append(_argument_test(index, test, problem))
                continue
            if not _has_raw_call(test):
                raise ValueError(f"`custom_tests[{index}].test` must be a non-empty string")

        for key in ("test", "expected_output"):
            value = test.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"`custom_tests[{index}].{key}` must be a non-empty string")

        validated.append(_raw_test(index, test))

    return deepcopy(validated)


def custom_test_signature(problem: dict[str, Any]) -> dict[str, Any] | None:
    starter_code = problem.get("starter_code")
    if not isinstance(starter_code, str):
        return None

    try:
        module = ast.parse(starter_code)
    except SyntaxError:
        return None

    function = next((node for node in module.body if isinstance(node, ast.FunctionDef)), None)
    if function is None:
        return None

    parameters = [argument.arg for argument in [*function.args.posonlyargs, *function.args.args]]
    parameters = [name for name in parameters if name not in {"self", "cls"}]
    if not parameters:
        return None

    return {"function_name": function.name, "parameters": parameters}


def _string_field(test: dict[str, Any], key: str, default: str) -> str:
    value = test.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"`custom_tests[].{key}` must be a string")
    return value


def _uses_argument_mode(test: dict[str, Any]) -> bool:
    return test.get("mode") == "arguments" or ("arguments" in test and not _has_raw_call(test))


def _has_raw_call(test: dict[str, Any]) -> bool:
    value = test.get("test")
    return isinstance(value, str) and bool(value.strip())


def _raw_test(index: int, test: dict[str, Any]) -> dict[str, Any]:
    mode = _string_field(test, "mode", "raw")
    if mode not in {"raw", "arguments"}:
        raise ValueError(f"`custom_tests[{index}].mode` must be `raw` or `arguments`")

    validated: dict[str, Any] = {
        "name": _string_field(test, "name", f"Custom test {index}"),
        "input": _string_field(test, "input", ""),
        "test": str(test["test"]),
        "expected_output": str(test["expected_output"]),
        "mode": mode,
    }
    if isinstance(test.get("arguments"), dict):
        validated["arguments"] = {
            str(name): _string_argument(index, str(name), value) for name, value in test["arguments"].items()
        }
    return validated


def _argument_test(index: int, test: dict[str, Any], problem: dict[str, Any]) -> dict[str, Any]:
    signature = custom_test_signature(problem)
    if signature is None:
        raise ValueError(f"`custom_tests[{index}].arguments` requires a starter function signature")

    expected_output = _string_field(test, "expected_output", "")
    if not expected_output.strip():
        raise ValueError(f"`custom_tests[{index}].expected_output` must be a non-empty string")

    arguments = test.get("arguments")
    if not isinstance(arguments, dict):
        raise ValueError(f"`custom_tests[{index}].arguments` must be an object")

    parameters = list(signature["parameters"])
    unknown = sorted(str(name) for name in arguments if str(name) not in parameters)
    if unknown:
        raise ValueError(f"`custom_tests[{index}].arguments` includes unknown parameter `{unknown[0]}`")

    normalized_arguments = {
        name: _argument_expression(name, _string_argument(index, name, arguments.get(name))) for name in parameters
    }
    input_text = ", ".join(f"{name} = {value}" for name, value in normalized_arguments.items())
    call_args = ", ".join(normalized_arguments.values())
    return {
        "name": _string_field(test, "name", f"Custom test {index}"),
        "input": input_text,
        "test": f"print({signature['function_name']}({call_args}))",
        "expected_output": expected_output,
        "mode": "arguments",
        "arguments": normalized_arguments,
    }


def _string_argument(index: int, name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`custom_tests[{index}].arguments.{name}` must be a non-empty string")
    return value.strip()


def _argument_expression(name: str, value: str) -> str:
    try:
        module = ast.parse(value)
    except SyntaxError:
        return value

    if len(module.body) != 1:
        return value

    statement = module.body[0]
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return value
    target = statement.targets[0]
    if not isinstance(target, ast.Name) or target.id != name:
        return value
    return ast.unparse(statement.value).strip()
