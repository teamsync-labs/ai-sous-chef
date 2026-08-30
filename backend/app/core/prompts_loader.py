from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def resolve_prompts_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "prompts",  # Docker: /app/prompts
        here.parents[3] / "prompts",  # Local: <repo>/prompts
    ]
    for path in candidates:
        if (path / "pin.json").is_file():
            return path
    checked = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"prompts/pin.json not found. Looked in: {checked}"
    )


@lru_cache(maxsize=1)
def load_pin() -> dict[str, str]:
    pin_path = resolve_prompts_dir() / "pin.json"
    data = json.loads(pin_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid pin.json format: {pin_path}")
    for key in ("recognize", "recipes"):
        if key not in data or not str(data[key]).strip():
            raise ValueError(f"pin.json missing '{key}': {pin_path}")
    return {k: str(v).strip() for k, v in data.items()}


def _render(template: str, **values: str) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise KeyError(f"Unknown prompt placeholder: {{{{ {name} }}}}")
        return values[name]

    return _PLACEHOLDER_RE.sub(repl, template)


def load_prompt_pair(scenario: str, **values: str) -> tuple[str, str, str]:
    """
    Returns (version, system, user) for scenario from pin.json.
    """
    pin = load_pin()
    if scenario not in pin:
        raise KeyError(f"No pin for scenario '{scenario}'")
    version = pin[scenario]
    base = resolve_prompts_dir() / scenario / version
    system_path = base / "system.md"
    user_path = base / "user.md"
    if not system_path.is_file() or not user_path.is_file():
        raise FileNotFoundError(
            f"Prompt files missing for {scenario}/{version}: "
            f"{system_path}, {user_path}"
        )
    system = _render(system_path.read_text(encoding="utf-8"), **values)
    user = _render(user_path.read_text(encoding="utf-8"), **values)
    return version, system, user


def clear_prompt_cache() -> None:
    load_pin.cache_clear()
