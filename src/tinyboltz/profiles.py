from __future__ import annotations

from pathlib import Path
from typing import Any


def load_profile(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    text = profile_path.read_text(encoding="utf-8")
    return _parse_simple_yaml(text)


def profile_get(profile: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    value: Any = profile
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def profile_bool(profile: dict[str, Any], dotted_key: str, default: bool = False) -> bool:
    value = profile_get(profile, dotted_key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"Unsupported profile line: {raw_line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if raw_value == "":
            child: dict[str, Any] = {}
            current[key] = child
            stack.append((indent, child))
        else:
            current[key] = _parse_scalar(raw_value)
    return root


def _parse_scalar(value: str) -> Any:
    cleaned = value.strip().strip('"').strip("'")
    lower = cleaned.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "none"}:
        return None
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return cleaned

