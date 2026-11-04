"""Check every current-law quote against the page it cites (``hre validate --law-quotes``).

Each current-law file quotes the statute in its record and in every feature's sources. This
check fetches each cited page once (cached under ``data/raw/law_pages/``, git-ignored), reduces
it to plain text, and confirms each quote appears in it word for word after normalizing white
space, typographic quotes and dashes. The result is ``docs/evidence/current_law_quotes.md``.

Pages are untrusted text: they are only searched, never executed or followed beyond one known
indirection (le.utah.gov section pages load the text from a versioned file named in the page).
A PDF is not parsed (no PDF library is a dependency); its quotes are listed as "PDF, checked by
hand" and the reviewer checklist covers them (docs/methods/current_law.md).
"""

from __future__ import annotations

import hashlib
import html
import re
import time
from pathlib import Path
from typing import Any

import requests
import yaml

from hre.data.cache import raw_dir, user_agent

UTAH_VERSION = re.compile(r'versionDefault="([^"]+)"')
TAGS = re.compile(r"<[^>]+>")
SPACE_BEFORE_PUNCT = re.compile(r" ([,.;:)])")     # a link's closing tag leaves "303 , within"
SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")
QUOTE_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-",
                           "—": "-", " ": " ", "­": ""})


def normalize(text: str) -> str:
    """Case-folded, single-spaced text with plain quotes and dashes, for substring checks."""
    text = html.unescape(text).translate(QUOTE_MAP)
    text = " ".join(text.split())
    return SPACE_BEFORE_PUNCT.sub(r"\1", text).casefold()


def html_to_text(raw: str) -> str:
    raw = SCRIPT.sub(" ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>", "\n", raw)
    return html.unescape(TAGS.sub(" ", raw))


def collect(law_dir: Path) -> list[dict[str, Any]]:
    """Every (state, scenario, where, url, quote) in the current-law files."""
    rows = []
    for p in sorted(law_dir.glob("[A-Z][A-Z].yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for name, s in (doc.get("scenarios") or {}).items():
            rec = s.get("record") or {}
            if rec.get("url") and rec.get("quote"):
                rows.append({"state": doc["state"], "scenario": name, "where": "record",
                             "url": rec["url"], "quote": rec["quote"]})
            for f in s.get("features") or []:
                for src in f.get("sources") or []:
                    rows.append({"state": doc["state"], "scenario": name,
                                 "where": f"{f['id']} ({src.get('locator', '')})",
                                 "url": src["url"], "quote": src["quote"]})
    return rows


def _cache_path(url: str, cache: Path) -> Path:
    return cache / (hashlib.sha256(url.encode()).hexdigest()[:20] + ".page")


def _get(url: str, session: requests.Session) -> bytes:
    for attempt in range(3):
        try:
            r = session.get(url, headers={"User-Agent": user_agent()}, timeout=(15, 60))
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def page_text(url: str, cache: Path, fetch: bool, session: requests.Session | None = None) -> tuple[str | None, str]:
    """(plain text or None, status) for one URL; status explains a None."""
    if url.lower().split("?")[0].endswith(".pdf"):
        return None, "PDF, checked by hand"
    path = _cache_path(url, cache)
    if not path.exists():
        if not fetch:
            return None, "not cached (run with --fetch)"
        sess = session or requests.Session()
        try:
            raw = _get(url, sess)
            m = UTAH_VERSION.search(raw.decode("utf-8", "replace"))
            if "le.utah.gov/xcode/" in url and m and m.group(1):
                raw = _get(url.rsplit("/", 1)[0] + f"/{m.group(1)}.html", sess)
        except requests.RequestException as e:
            return None, f"fetch failed ({type(e).__name__})"
        cache.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    raw_text = path.read_bytes().decode("utf-8", "replace")
    if raw_text.lstrip()[:5] == "%PDF-":
        return None, "PDF, checked by hand"
    return html_to_text(raw_text), "fetched"


def check(law_dir: Path, fetch: bool = False, data_dir: Path | None = None) -> list[dict[str, Any]]:
    cache = (data_dir or raw_dir()) / "law_pages"
    texts: dict[str, tuple[str | None, str]] = {}
    session = requests.Session()
    out = []
    for row in collect(law_dir):
        if row["url"] not in texts:
            t, status = page_text(row["url"], cache, fetch, session)
            texts[row["url"]] = (normalize(t) if t is not None else None, status)
        text, status = texts[row["url"]]
        found = None if text is None else normalize(row["quote"]) in text
        out.append({**row, "found": found, "status": status if text is None else ("found" if found else "NOT FOUND")})
    return out


def render_markdown(rows: list[dict[str, Any]], today: str) -> str:
    n = len(rows)
    found = sum(1 for r in rows if r["found"])
    missing = [r for r in rows if r["found"] is False]
    unchecked = [r for r in rows if r["found"] is None]
    out = [
        "# Current-law quotes checked against their pages",
        "",
        (f"Generated {today} by `uv run hre validate --law-quotes --fetch`: every quote in "
        "`src/hre/current_law/*.yaml` (the record and every feature source) is searched for, word for "
        "word, in the text of the page it cites (white space, typographic quotes and dashes normalized; "
        "case ignored). Code: `src/hre/validation/law_quotes.py`."),
        "",
        (f"**{found} of {n} quotes found on their pages; {len(missing)} not found; {len(unchecked)} not "
        "checked automatically** (PDFs and pages that refuse scripted access are checked by hand in review)."),
        "",
        "| State | Reform | Where | Result | Page |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(f"| {r['state']} | {r['scenario']} | {r['where']} | {r['status']} | {r['url']} |")
    if missing:
        out += ["", "## Not found", ""]
        out += [f"- {r['state']} {r['scenario']} {r['where']}: \"{r['quote']}\" ({r['url']})" for r in missing]
    return "\n".join(out) + "\n"
