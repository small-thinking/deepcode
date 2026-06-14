from __future__ import annotations

from pathlib import Path
from typing import Any


def data_link_status(problem: dict[str, Any]) -> dict[str, Any]:
    link_path, data_path = _data_link_path(problem)
    exists = link_path.exists() or link_path.is_symlink()
    is_symlink = link_path.is_symlink()
    target_path = str(link_path.readlink()) if is_symlink else None
    data = problem.get("data", {})

    return {
        "data_path": data_path,
        "link_path": str(link_path),
        "exists": exists,
        "is_symlink": is_symlink,
        "target_path": target_path,
        "required": bool(data.get("required")) if isinstance(data, dict) else False,
    }


def set_data_link(problem: dict[str, Any], target_path: str) -> dict[str, Any]:
    link_path, _ = _data_link_path(problem)
    target = Path(target_path).expanduser()
    if not target.is_absolute():
        raise ValueError("`target_path` must be an absolute path")
    if not target.is_dir():
        raise ValueError("`target_path` must be an existing directory")

    if link_path.exists() and not link_path.is_symlink():
        raise ValueError(f"Refusing to replace non-symlink data path: {link_path}")
    if link_path.is_symlink():
        link_path.unlink()

    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target, target_is_directory=True)
    return data_link_status(problem)


def remove_data_link(problem: dict[str, Any]) -> dict[str, Any]:
    link_path, _ = _data_link_path(problem)
    if link_path.exists() and not link_path.is_symlink():
        raise ValueError(f"Refusing to remove non-symlink data path: {link_path}")
    if link_path.is_symlink():
        link_path.unlink()
    return data_link_status(problem)


def _data_link_path(problem: dict[str, Any]) -> tuple[Path, str]:
    data = problem.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("path"), str) or not data["path"].strip():
        raise ValueError("Problem does not declare `data.path`")

    runtime = problem.get("_runtime", {})
    link_path = runtime.get("data_path")
    if not isinstance(link_path, str) or not link_path.strip():
        raise ValueError("Problem does not have a runtime data path")

    return Path(link_path), data["path"]
