from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from deepcode.evaluators import (
    EvaluationRequest,
    UnsupportedEvaluatorError,
    evaluate_submission,
    stream_evaluation_events,
)
from deepcode.problem_store import ProblemStore
from deepcode.user_state import UserStateStore


@dataclass(frozen=True)
class ApiContext:
    store: ProblemStore
    user_state: UserStateStore | None = None


def handle_api_request(
    context: ApiContext,
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: bytes | None,
) -> tuple[int, dict[str, Any]]:
    try:
        return _handle_api_request(context, method.upper(), path, query, body)
    except KeyError:
        return 404, {"error": "Problem not found"}
    except UnsupportedEvaluatorError as error:
        return 501, {"error": str(error)}
    except json.JSONDecodeError:
        return 400, {"error": "Invalid JSON body"}
    except ValueError as error:
        return 400, {"error": str(error)}


def stream_api_events(
    context: ApiContext,
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: bytes | None,
) -> Generator[dict[str, Any], None, None]:
    try:
        yield from _stream_api_events(context, method.upper(), path, query, body)
    except KeyError:
        yield {"type": "error", "status": 404, "error": "Problem not found"}
    except UnsupportedEvaluatorError as error:
        yield {"type": "error", "status": 501, "error": str(error)}
    except json.JSONDecodeError:
        yield {"type": "error", "status": 400, "error": "Invalid JSON body"}
    except ValueError as error:
        yield {"type": "error", "status": 400, "error": str(error)}


def _handle_api_request(
    context: ApiContext,
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: bytes | None,
) -> tuple[int, dict[str, Any]]:
    parts = [unquote(part) for part in path.strip("/").split("/") if part]
    if parts == ["api", "health"] and method == "GET":
        return 200, {"status": "ok"}

    if parts == ["api", "problems"] and method == "GET":
        problems = context.store.list_problems(
            category=_first(query, "category"),
            difficulty=_first(query, "difficulty"),
            search=_first(query, "search"),
            sort=_first(query, "sort") or "id",
        )
        problems = _with_personal_status(context, problems)
        return 200, {
            "problems": problems,
            "categories": context.store.categories(),
            "difficulties": context.store.difficulties(),
            "total": len(problems),
        }

    if len(parts) == 3 and parts[:2] == ["api", "problems"] and method == "GET":
        problem = _public_problem(context.store.get_problem(parts[2]))
        return 200, {"problem": _with_personal_status(context, [problem])[0]}

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "run" and method == "POST":
        problem, request, test_index = _evaluation_request_from_body(context, parts[2], body)
        result = evaluate_submission(request)
        if context.user_state and test_index is None and result.get("status") == "passed":
            result["problem_status"] = context.user_state.mark_completed(str(problem.get("slug", parts[2])))
        return 200, result

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "reset" and method == "POST":
        problem = context.store.get_problem(parts[2])
        if context.user_state:
            return 200, {"problem_status": context.user_state.reset_problem(str(problem.get("slug", parts[2])))}
        return 200, {"problem_status": {"completed": False, "completed_at": None}}

    if parts[:2] == ["api", "problems"]:
        return 405, {"error": "Method not allowed"}
    return 404, {"error": "Route not found"}


def _stream_api_events(
    context: ApiContext,
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: bytes | None,
) -> Generator[dict[str, Any], None, None]:
    parts = [unquote(part) for part in path.strip("/").split("/") if part]
    if len(parts) != 5 or parts[:2] != ["api", "problems"] or parts[3:] != ["run", "stream"]:
        yield {"type": "error", "status": 404, "error": "Route not found"}
        return
    if method != "POST":
        yield {"type": "error", "status": 405, "error": "Method not allowed"}
        return

    problem, request, test_index = _evaluation_request_from_body(context, parts[2], body)
    yield {"type": "run_started", "total": len(request.tests)}
    final_result: dict[str, Any] | None = None
    for event in stream_evaluation_events(request):
        if event.get("type") == "run_finished":
            final_result = dict(event.get("result") or {})
            if context.user_state and test_index is None and final_result.get("status") == "passed":
                final_result["problem_status"] = context.user_state.mark_completed(str(problem.get("slug", parts[2])))
            event = {**event, "result": final_result}
        yield event


def _evaluation_request_from_body(
    context: ApiContext,
    slug: str,
    body: bytes | None,
) -> tuple[dict[str, Any], EvaluationRequest, int | None]:
    problem = context.store.get_problem(slug)
    payload = json.loads((body or b"{}").decode("utf-8"))
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Request body must include non-empty `code`")

    tests = problem.get("tests", [])
    test_index = payload.get("test_index")
    if test_index is not None:
        if isinstance(test_index, bool) or not isinstance(test_index, int):
            raise ValueError("`test_index` must be an integer visible test index")
        if test_index < 0 or test_index >= len(tests):
            raise ValueError("`test_index` must refer to a visible test case")
        tests = [tests[test_index]]

    runtime = dict(problem.get("_runtime", {}))
    if test_index is not None:
        runtime["skip_hidden_harness"] = True

    return (
        problem,
        EvaluationRequest(
            code=code,
            problem=problem,
            tests=tests,
            environment=problem.get("environment", {}),
            runtime=runtime,
        ),
        test_index,
    )


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    return values[0] or None


def _public_problem(problem: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in problem.items() if not key.startswith("_")}


def _with_personal_status(context: ApiContext, problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not context.user_state:
        return problems
    return [context.user_state.annotate(problem) for problem in problems]
