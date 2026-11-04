"""Frozen checks: write the prediction down, hash it, commit the hash, only then fetch the outcome.

    validation/<check>/protocol.json    geography, years, outcome definition, denominator, the hit
                                        rule and the model's predictions, written by ``write_protocol``
    validation/<check>/protocol.sha256  its SHA-256, committed before any outcome is fetched
    validation/<check>/result.json      written afterwards by ``write_result``: the outcome, the
                                        protocol hash it was scored against, hit or miss

``verify`` recomputes the hash, so a protocol edited after the fact fails the test suite. The
predictions come from the same engine code as the forecasts (``hre.model``), run on the check's
place with the register unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
VALIDATION_DIR = REPO / "validation"


def canonical(obj: Any) -> bytes:
    """Stable bytes for hashing: sorted keys, fixed separators, a final newline."""
    return (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def check_dir(check: str, root: Path = VALIDATION_DIR) -> Path:
    return root / check


def write_protocol(check: str, protocol: dict[str, Any], root: Path = VALIDATION_DIR) -> str:
    """Write protocol.json and protocol.sha256; refuse to overwrite a frozen protocol."""
    d = check_dir(check, root)
    p = d / "protocol.json"
    if p.exists():
        raise FileExistsError(f"{p} is frozen; a new protocol needs a new check name")
    d.mkdir(parents=True, exist_ok=True)
    data = canonical(protocol)
    p.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    (d / "protocol.sha256").write_text(f"{sha}  protocol.json\n", encoding="utf-8")
    return sha


def verify(check: str, root: Path = VALIDATION_DIR) -> str:
    """The recorded hash, after checking that protocol.json still has it."""
    d = check_dir(check, root)
    recorded = (d / "protocol.sha256").read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256((d / "protocol.json").read_bytes()).hexdigest()
    if actual != recorded:
        raise ValueError(f"{check}: protocol.json hash {actual} differs from the recorded {recorded}")
    return recorded


def write_result(check: str, result: dict[str, Any], root: Path = VALIDATION_DIR) -> dict[str, Any]:
    """Score the outcome against the frozen prediction and write result.json."""
    sha = verify(check, root)
    proto = json.loads((check_dir(check, root) / "protocol.json").read_text(encoding="utf-8"))
    out = {"check": check, "protocol_sha256": sha, **result}
    lo, hi = proto["prediction"]["low"], proto["prediction"]["high"]
    if isinstance(result.get("actual"), (int, float)):
        out["inside"] = lo <= result["actual"] <= hi
        out["actual_over_mid"] = result["actual"] / proto["prediction"]["mid"] if proto["prediction"]["mid"] else None
    (check_dir(check, root) / "result.json").write_bytes(canonical(out))
    return out
