from __future__ import annotations


def normalize_python_indentation(code: str, tab_width: int = 4) -> str:
    """Expand leading indentation tabs without changing tabs inside code text."""
    return "".join(_normalize_line_indentation(line, tab_width) for line in code.splitlines(keepends=True))


def _normalize_line_indentation(line: str, tab_width: int) -> str:
    indent_end = 0
    while indent_end < len(line) and line[indent_end] in {" ", "\t"}:
        indent_end += 1

    indent = line[:indent_end].replace("\t", " " * tab_width)
    return f"{indent}{line[indent_end:]}"
