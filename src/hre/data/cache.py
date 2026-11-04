"""Download cache and provenance manifests.

Every fetcher calls :func:`fetch` (one URL, one file) or :func:`record` (a file
the fetcher assembled itself, for example paged API results). Both write one
entry into ``data/manifests/<source>.json``:

    {
      "files": {
        "bps/co2025a.txt": {"bytes": 375314, "fetched_at": "2026-11-03T15:00:00Z",
                            "sha256": "...", "url": "https://...", "vintage": "2025"}
      },
      "license": "...", "notes": "...", "source": "bps"
    }

Manifests are tracked in git; the files they describe are not. A reviewer can
re-run ``hre fetch`` and compare SHA-256 digests to prove they hold the same
bytes we used. Keys are sorted so diffs are stable.

Environment:
- ``DATA_DIR``: where raw files are cached (default ``data/raw``). Only the raw
  cache moves with this variable; manifests always go to ``data/manifests``
  (override with ``HRE_MANIFEST_DIR`` for tests).
- ``HRE_CONTACT_EMAIL``: optional; appended to the User-Agent so a host that
  rate-limits us can reach a human. Read from ``.env`` if present.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hre import __version__
from hre.data import net

_PART_SUFFIX = ".part"


# -- environment -----------------------------------------------------------------


def load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    """Load KEY=VALUE lines from a .env file into os.environ without overriding."""
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def raw_dir() -> Path:
    """Raw cache root; read at call time so tests and the CLI can override it."""
    return Path(os.environ.get("DATA_DIR", "data/raw"))


def manifest_dir() -> Path:
    return Path(os.environ.get("HRE_MANIFEST_DIR", "data/manifests"))


def user_agent() -> str:
    contact = os.environ.get("HRE_CONTACT_EMAIL", "").strip()
    base = f"permit-horizon/{__version__} (+https://github.com/rmanacha/permit-horizon"
    return f"{base}; {contact})" if contact else f"{base})"


# -- hashing and manifests ---------------------------------------------------------


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def manifest_path(source: str) -> Path:
    return manifest_dir() / f"{source}.json"


def read_manifest(source: str) -> dict[str, Any]:
    p = manifest_path(source)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"source": source, "files": {}}


def write_manifest(source: str, manifest: dict[str, Any]) -> Path:
    p = manifest_path(source)
    p.parent.mkdir(parents=True, exist_ok=True)
    manifest["source"] = source
    manifest.setdefault("files", {})
    text = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    p.write_text(text, encoding="utf-8")
    return p


def record(
    source: str,
    rel_path: str,
    path: Path,
    *,
    url: str,
    license: str,
    vintage: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Add or replace the manifest entry for ``path`` (keyed by ``rel_path``)."""
    manifest = read_manifest(source)
    entry = {
        "bytes": path.stat().st_size,
        "fetched_at": _utc_now(),
        "sha256": sha256_of(path),
        "url": url,
        "vintage": vintage,
    }
    manifest["files"][rel_path] = entry
    manifest["license"] = license
    if notes is not None:
        manifest["notes"] = notes
    write_manifest(source, manifest)
    return entry


# -- download ------------------------------------------------------------------------


def _rel(dest: Path) -> str:
    """Manifest key: the path relative to the raw cache (falls back to the last two parts)."""
    try:
        return dest.resolve().relative_to(raw_dir().resolve()).as_posix()
    except ValueError:
        return "/".join(dest.parts[-2:])


def fetch(
    url: str,
    dest: Path,
    *,
    source: str,
    license: str,
    vintage: str,
    notes: str | None = None,
    params: dict[str, Any] | None = None,
    force: bool = False,
    retries: int = 4,
    timeout: tuple[float, float] = (15.0, 180.0),
) -> Path:
    """Download ``url`` to ``dest`` (streaming, retried, hashed) and record it.

    Idempotent: when ``dest`` exists and its SHA-256 matches the manifest entry
    for the same URL, nothing is downloaded. Returns ``dest``.
    """
    dest = Path(dest)
    rel = _rel(dest)
    manifest = read_manifest(source)
    prior = manifest["files"].get(rel)
    if dest.is_file() and not force:
        if prior and prior.get("url") == url and prior.get("sha256") == sha256_of(dest):
            return dest
        if prior is None:
            # File present from an earlier run without a manifest: record, don't refetch.
            record(source, rel, dest, url=url, license=license, vintage=vintage, notes=notes)
            return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + _PART_SUFFIX)
    headers = {"User-Agent": user_agent()}

    def attempt() -> None:
        net.download(url, part, params=params, headers=headers, timeout=timeout)
        part.replace(dest)

    try:
        net.with_retries(attempt, retries=retries)
    finally:
        part.unlink(missing_ok=True)

    record(source, rel, dest, url=url, license=license, vintage=vintage, notes=notes)
    return dest


def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    retries: int = 4,
    timeout: tuple[float, float] = (15.0, 180.0),
) -> Any:
    """GET a JSON document with the same retry policy as :func:`fetch` (no caching)."""
    headers = {"User-Agent": user_agent()}
    return net.with_retries(lambda: net.get_json(url, params=params, headers=headers, timeout=timeout),
                            retries=retries)
