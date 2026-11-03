"""Load a state's current-law register and return the strength the engine uses.

    from hre.current_law.loader import current_strength
    current_strength("NH", "adu")
    -> {"current_strength": 0.75, "newly_affected_share": 0.25, "source": "register", ...}

Any state file that is missing, or a scenario that is absent or fails the schema,
yields strength 0 (so the whole benchmark counts as newly affected) and the note
"No statewide law found; local permissions unverified." An incomplete entry also
says which checks it failed, so the gap is visible instead of silent.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from hre.current_law.schema import DEFAULT_NOTE, SCENARIOS, validate_scenario

HERE = Path(__file__).resolve().parent


def state_path(state: str, folder: Path = HERE) -> Path:
    return folder / f"{state.upper()}.yaml"


def load_state(state: str, folder: Path = HERE) -> dict[str, Any] | None:
    p = state_path(state, folder)
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def current_strength(state: str, scenario: str, folder: Path = HERE) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}")
    path = state_path(state, folder)
    doc = load_state(state, folder)
    default = {"current_strength": 0.0, "newly_affected_share": 1.0, "source": "default",
               "note": DEFAULT_NOTE, "human_review": None, "record": None, "features": [],
               "file": None, "problems": []}
    if doc is None:
        return default
    entry = (doc.get("scenarios") or {}).get(scenario)
    if entry is None:
        return {**default, "file": path.name}
    problems = validate_scenario(scenario, entry)
    if problems:
        return {**default, "file": path.name, "problems": problems,
                "note": DEFAULT_NOTE + f" (register entry incomplete: {len(problems)} problem(s))"}
    s = float(entry["current_strength"])
    return {
        "current_strength": s,
        "newly_affected_share": 1.0 - s,
        "source": "register",
        "note": " ".join(str(entry["strength_rationale"]).split()),
        "human_review": entry["human_review"],
        "record": entry["record"],
        "features": entry["features"],
        "file": path.name,
        "problems": [],
    }


def register_digest(state: str, folder: Path = HERE) -> str | None:
    """sha256 of the state file (recorded in results meta), or None when there is no file."""
    p = state_path(state, folder)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
