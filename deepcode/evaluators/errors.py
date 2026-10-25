"""Present Python failures in terms of the code the learner can edit."""
from __future__ import annotations

import json
import re

from deepcode.evaluators.submission import normalize_python_indentation

_FRAME = re.compile(r'^ {0,2}File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in (?P<context>.*))?$')
_HEADER = "Traceback (most recent call last):"
_GROUP_HEADER = re.compile(r"^ *\+ Exception Group Traceback \(most recent call last\):$")
_GROUP_PREFIX = re.compile(r"^ *\| ?")
_GROUP_DIVIDER = re.compile(r"^ *\+(?:-\+)?-+.*$")
_MISMATCH = "AssertionError: DEEPCODE_ASSERTION_MISMATCH:"


def starts_python_traceback(line: str) -> bool:
    return (
        line.rstrip() == _HEADER
        or _GROUP_HEADER.match(line.rstrip()) is not None
        or _FRAME.match(line.rstrip()) is not None
    )


def format_python_error(stderr: str, code: str, script_path: str) -> str:
    """Keep editor frames and exception messages, omitting harness/library frames.

    The runner appends checks after code.rstrip(), without a preamble, so editor
    line numbers are unchanged. Generated checks intentionally get no line number:
    assertion instrumentation and hidden harnesses don't map to the visible editor.
    Non-traceback stderr (including warnings) passes through unchanged.
    """
    code_lines = normalize_python_indentation(code).rstrip().splitlines()
    output: list[str] = []
    frames: list[tuple[re.Match[str], list[str]]] = []

    def flush_frames() -> None:
        if not frames:
            return
        editor_frames = [
            (match, context) for match, context in frames
            if match["path"] == script_path and 1 <= int(match["line"]) <= len(code_lines)
        ]
        for match, context in editor_frames:
            location = f'Line {match["line"]}'
            if match["context"] and match["context"] != "<module>":
                location += f' in {match["context"]}'
            output.append(location)
            # Prefer Python's source/caret context, which also marks syntax errors.
            output.extend(context or [f'    {code_lines[int(match["line"]) - 1].strip()}'])
        if not editor_frames:
            output.append("Test check" if any(m["path"] == script_path for m, _ in frames) else "Python execution")
        frames.clear()

    lines = stderr.splitlines()
    if any(_GROUP_HEADER.match(line) for line in lines):
        # ExceptionGroup decorates every nested traceback with a tree margin.
        # Remove that margin before applying the same frame/source filtering.
        lines = [
            _HEADER if _GROUP_HEADER.match(line) else
            "" if _GROUP_DIVIDER.match(line) else _GROUP_PREFIX.sub("", line)
            for line in lines
        ]
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == _HEADER:
            flush_frames()
            index += 1
            continue
        match = _FRAME.match(line)
        if match:
            context: list[str] = []
            index += 1
            while index < len(lines) and lines[index].startswith("    "):
                context.append(lines[index])
                index += 1
            frames.append((match, context))
            continue
        if frames and line.strip().startswith("[Previous line repeated "):
            # This is traceback metadata, not an exception message.
            index += 1
            continue
        flush_frames()
        if line.startswith(_MISMATCH):
            try:
                payload = json.loads(line[len(_MISMATCH):])
                line = f'AssertionError: Expected {payload["expected"]}, got {payload["actual"]}'
                if payload.get("message"):
                    line += f' ({payload["message"]})'
            except (ValueError, KeyError, TypeError):
                line = "AssertionError: Values do not match"
        output.append(line)
        index += 1
    flush_frames()
    return "\n".join(output).strip()
