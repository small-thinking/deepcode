from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from deepcode.activity_log import ActivityLogStore
from deepcode.custom_tests import CustomTestStore, validate_custom_tests
from deepcode.company_store import CompanyStore
from deepcode.data_links import data_link_status, remove_data_link, set_data_link
from deepcode.evaluators import (
    EvaluationRequest,
    UnsupportedEvaluatorError,
    evaluate_submission,
    stream_evaluation_events,
)
from deepcode.playground import run_playground
from deepcode.problem_store import ProblemStore
from deepcode.user_state import UserStateStore


@dataclass(frozen=True)
class ApiContext:
    store: ProblemStore
    company_store: CompanyStore | None = None
    user_state: UserStateStore | None = None
    custom_tests: CustomTestStore | None = None
    activity_log: ActivityLogStore | None = None


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

    if parts == ["api", "playground", "run"]:
        if method != "POST":
            return 405, {"error": "Method not allowed"}
        payload = json.loads((body or b"{}").decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return 200, run_playground(payload.get("code"))

    if parts == ["api", "progress"]:
        if method != "GET":
            return 405, {"error": "Method not allowed"}
        return 200, _progress_payload(context)

    if parts == ["api", "companies"] and method == "GET":
        company_store = _company_store(context)
        companies = company_store.list_companies(context.store.list_problems())
        return 200, {"companies": companies, "total": len(companies)}

    if len(parts) == 3 and parts[:2] == ["api", "companies"] and method == "GET":
        company_store = _company_store(context)
        try:
            company = company_store.get_company(parts[2], context.store.list_problems())
        except KeyError:
            return 404, {"error": "Company not found"}
        return 200, {"company": company}

    if parts == ["api", "problems"] and method == "GET":
        sort = _first(query, "sort") or "id"
        order = _first(query, "order") or "asc"
        problems = context.store.list_problems(
            category=_first(query, "category"),
            difficulty=_first(query, "difficulty"),
            company=_first(query, "company"),
            search=_first(query, "search"),
            sort="id" if sort == "completed" else sort,
            order="asc" if sort == "completed" else order,
        )
        problems = _with_personal_status(context, problems)
        if sort == "completed":
            problems = sorted(
                problems,
                key=lambda problem: problem.get("personal_status", {}).get("completed") is True,
                reverse=order.casefold() == "desc",
            )
        return 200, {
            "problems": problems,
            "categories": context.store.categories(),
            "difficulties": context.store.difficulties(),
            "companies": context.store.companies(),
            "company_profiles": _company_profile_summaries(context),
            "total": len(problems),
        }

    if len(parts) == 3 and parts[:2] == ["api", "problems"] and method == "GET":
        problem = _public_problem(context.store.get_problem(parts[2]))
        return 200, {"problem": _with_personal_status(context, [problem])[0]}

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "custom-tests":
        problem = context.store.get_problem(parts[2])
        _ensure_ml_coding(problem, "Custom tests")
        slug = str(problem.get("slug", parts[2]))
        if method == "GET":
            return 200, {"custom_tests": context.custom_tests.list_for(slug) if context.custom_tests else []}
        if method == "PUT":
            if context.custom_tests is None:
                raise ValueError("Custom test storage is not configured")
            payload = json.loads((body or b"{}").decode("utf-8"))
            return 200, {"custom_tests": context.custom_tests.replace_for(slug, payload.get("custom_tests"), problem)}
        return 405, {"error": "Method not allowed"}

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "data-link":
        problem = context.store.get_problem(parts[2])
        if method == "GET":
            return 200, data_link_status(problem)
        if method == "PUT":
            payload = json.loads((body or b"{}").decode("utf-8"))
            target_path = payload.get("target_path")
            if not isinstance(target_path, str) or not target_path.strip():
                raise ValueError("Request body must include non-empty `target_path`")
            return 200, set_data_link(problem, target_path)
        if method == "DELETE":
            return 200, remove_data_link(problem)
        return 405, {"error": "Method not allowed"}

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "run" and method == "POST":
        problem, request, completion_eligible, activity_scope = _evaluation_request_from_body(context, parts[2], body)
        result = evaluate_submission(request)
        _record_submission_status(context, problem, parts[2], completion_eligible, result)
        _record_activity_event(context, problem, activity_scope, result)
        return 200, result

    if len(parts) == 4 and parts[:2] == ["api", "problems"] and parts[3] == "reset" and method == "POST":
        problem = context.store.get_problem(parts[2])
        if context.user_state:
            return 200, {"problem_status": context.user_state.reset_problem(str(problem.get("slug", parts[2])))}
        return 200, {"problem_status": _empty_problem_status()}

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

    problem, request, completion_eligible, activity_scope = _evaluation_request_from_body(context, parts[2], body)
    yield {"type": "run_started", "total": len(request.tests)}
    final_result: dict[str, Any] | None = None
    for event in stream_evaluation_events(request):
        if event.get("type") == "run_finished":
            final_result = dict(event.get("result") or {})
            _record_submission_status(context, problem, parts[2], completion_eligible, final_result)
            _record_activity_event(context, problem, activity_scope, final_result)
            event = {**event, "result": final_result}
        yield event


def _evaluation_request_from_body(
    context: ApiContext,
    slug: str,
    body: bytes | None,
) -> tuple[dict[str, Any], EvaluationRequest, bool, str]:
    problem = context.store.get_problem(slug)
    payload = json.loads((body or b"{}").decode("utf-8"))
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Request body must include non-empty `code`")

    tests = problem.get("tests", [])
    custom_tests = _custom_tests_from_payload(problem, payload)
    custom_only = payload.get("custom_only", False)
    if not isinstance(custom_only, bool):
        raise ValueError("`custom_only` must be a boolean")

    test_index = payload.get("test_index")
    if test_index is not None:
        if isinstance(test_index, bool) or not isinstance(test_index, int):
            raise ValueError("`test_index` must be an integer visible test index")
        if test_index < 0 or test_index >= len(tests):
            raise ValueError("`test_index` must refer to a visible test case")
        tests = [tests[test_index]]

    if custom_only:
        if test_index is not None:
            raise ValueError("`custom_only` cannot be combined with `test_index`")
        tests = custom_tests
    elif custom_tests:
        tests = [*tests, *custom_tests]

    runtime = dict(problem.get("_runtime", {}))
    if test_index is not None:
        runtime["skip_hidden_harness"] = True

    activity_scope = "selected" if test_index is not None else "custom" if custom_only or custom_tests else "full"
    completion_eligible = activity_scope == "full"
    return (
        problem,
        EvaluationRequest(
            code=code,
            problem=problem,
            tests=tests,
            environment=problem.get("environment", {}),
            runtime=runtime,
        ),
        completion_eligible,
        activity_scope,
    )


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    return values[0] or None


def _company_store(context: ApiContext) -> CompanyStore:
    if context.company_store is None:
        raise ValueError("Company profiles are not configured")
    return context.company_store


def _company_profile_summaries(context: ApiContext) -> list[dict[str, Any]]:
    """Expose only the fields the problem list needs to link company labels."""
    if context.company_store is None:
        return []
    return [
        {
            "slug": company["slug"],
            "name": company["name"],
            "aliases": company.get("aliases", []),
        }
        for company in context.company_store.list_companies(context.store.list_problems())
    ]


def _public_problem(problem: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in problem.items() if not key.startswith("_")}


def _with_personal_status(context: ApiContext, problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not context.user_state:
        return problems
    return [context.user_state.annotate(problem) for problem in problems]


def _progress_payload(context: ApiContext) -> dict[str, Any]:
    """Return activity and the small catalog projection needed for dashboard metrics."""
    problems = _with_personal_status(context, context.store.list_problems())
    events: list[dict[str, Any]] = []
    if context.activity_log is not None:
        context.activity_log.backfill_problem_statuses(problems)
        events = context.activity_log.list_events()
    return {
        "events": events,
        "problems": [_progress_problem_summary(problem) for problem in problems],
    }


def _progress_problem_summary(problem: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": problem.get("slug"),
        "title": problem.get("title"),
        "category": problem.get("category"),
        "difficulty": problem.get("difficulty"),
        "companies": list(problem.get("companies", [])),
        "personal_status": problem.get("personal_status", _empty_problem_status()),
    }


def _record_activity_event(
    context: ApiContext,
    problem: dict[str, Any],
    activity_scope: str,
    result: dict[str, Any],
) -> None:
    """Log every completed run; status changes remain limited to full suites."""
    if context.activity_log is not None:
        status = result.get("problem_status") if activity_scope == "full" else None
        last_submission = status.get("last_submission") if isinstance(status, dict) else None
        timestamp = last_submission.get("at") if isinstance(last_submission, dict) else None
        context.activity_log.record_submission(problem, scope=activity_scope, result=result, at=timestamp)


def _record_submission_status(
    context: ApiContext,
    problem: dict[str, Any],
    fallback_slug: str,
    completion_eligible: bool,
    result: dict[str, Any],
) -> None:
    """Persist one full-suite submission event without counting partial runs as progress."""
    if context.user_state is None or not completion_eligible:
        return
    result["problem_status"] = context.user_state.record_submission(
        str(problem.get("slug", fallback_slug)),
        passed=result.get("status") == "passed",
    )


def _empty_problem_status() -> dict[str, Any]:
    return {"completed": False, "completed_at": None, "last_submission": None}


def _custom_tests_from_payload(problem: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, str]]:
    if "custom_tests" not in payload:
        return []
    _ensure_ml_coding(problem, "Custom tests")
    return validate_custom_tests(payload["custom_tests"], problem=problem)


def _ensure_ml_coding(problem: dict[str, Any], label: str) -> None:
    evaluation = problem.get("evaluation", {})
    evaluation_type = evaluation.get("type", "ml_coding") if isinstance(evaluation, dict) else "ml_coding"
    if evaluation_type != "ml_coding":
        raise ValueError(f"{label} are only supported for ml_coding problems")
