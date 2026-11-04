"""Check every current-law quote against the page it cites (``hre validate --law-quotes``).

Each current-law file quotes the statute in its record and in every feature's sources. This
check fetches each cited page once (cached under ``data/raw/law_pages/``, git-ignored), reduces
it to plain text, and confirms each quote appears in it word for word after normalizing white
space, typographic quotes and dashes. The result is ``docs/evidence/current_law_quotes.md``.

Pages are untrusted text: they are only searched, never executed or followed beyond one known
indirection (le.utah.gov section pages load the text from a versioned file named in the page).
A PDF is read with pypdf when the optional ``law`` extra is installed (decision 94; ``uv sync
--all-extras``): its pages are joined and printed line numbers at the start of a line are dropped
(session laws print them in the margin). Without the extra, a PDF's quotes are listed as "PDF, not
read" and the reviewer checklist covers them (docs/methods/current_law.md).
"""

from __future__ import annotations

import hashlib
import html
import io
import re
from pathlib import Path
from typing import Any

import yaml

from hre.data import net
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


def _get(url: str) -> bytes:
    """One page, retried twice on a 429/5xx status or a network failure (2 then 4 seconds apart)."""
    return net.with_retries(lambda: net.get_bytes(url, headers={"User-Agent": user_agent()}, timeout=60.0),
                            retries=2, pause=lambda attempt: 2.0 * (attempt + 1))


LINE_NUMBER = re.compile(r"(?m)^\s*\d{1,3}\s+")
GLUED_LINE_NUMBER = re.compile(r"(?m)(?<=[A-Za-z])\d{1,3}[ \t]*$")   # "is amended by12"; never "1,000"


def pdf_text(data: bytes) -> str | None:
    """Text of a PDF with margin line numbers removed, or None when pypdf is not installed."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    reader = PdfReader(io.BytesIO(data))
    pages = [(pg.extract_text() or "") for pg in reader.pages]
    text = LINE_NUMBER.sub("", "\n".join(pages))
    return GLUED_LINE_NUMBER.sub("", text).replace("-\n", "")


def page_text(url: str, cache: Path, fetch: bool) -> tuple[str | None, str]:
    """(plain text or None, status) for one URL; status explains a None."""
    path = _cache_path(url, cache)
    if not path.exists():
        if not fetch:
            return None, "not cached (run with --fetch)"
        try:
            raw = _get(url)
            m = UTAH_VERSION.search(raw.decode("utf-8", "replace"))
            if "le.utah.gov/xcode/" in url and m and m.group(1):
                raw = _get(url.rsplit("/", 1)[0] + f"/{m.group(1)}.html")
        except net.ERRORS as e:
            return None, f"fetch failed ({type(e).__name__})"
        cache.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    raw = path.read_bytes()
    if raw.lstrip()[:5] == b"%PDF-":
        t = pdf_text(raw)
        return (t, "fetched (PDF)") if t is not None else (None, "PDF, not read (install the law extra)")
    return html_to_text(raw.decode("utf-8", "replace")), "fetched"


HAND_CHECKS = Path(__file__).resolve().parents[3] / "docs" / "evidence" / "current_law_hand_checks.yaml"


def hand_checks(path: Path = HAND_CHECKS) -> dict[tuple[str, str], dict[str, Any]]:
    """(url, normalized quote) -> the person's check, for pages a script cannot read."""
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {(c["url"], normalize(c["quote"])): c for c in doc.get("checks") or []}


def check(law_dir: Path, fetch: bool = False, data_dir: Path | None = None,
          hand_path: Path = HAND_CHECKS) -> list[dict[str, Any]]:
    cache = (data_dir or raw_dir()) / "law_pages"
    hand = hand_checks(hand_path)
    texts: dict[str, tuple[str | None, str]] = {}
    out = []
    for row in collect(law_dir):
        if row["url"] not in texts:
            t, status = page_text(row["url"], cache, fetch)
            texts[row["url"]] = (normalize(t) if t is not None else None, status)
        text, status = texts[row["url"]]
        found = None if text is None else normalize(row["quote"]) in text
        label = status if text is None else ("found" if found else "NOT FOUND")
        h = hand.get((row["url"], normalize(row["quote"])))
        if found is not True and h:
            found, label = None, f"checked by hand {h['checked']} ({h['how']})"
        out.append({**row, "found": found, "status": label})
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
         "checked automatically**, of which "
         f"{sum(1 for r in unchecked if r['status'].startswith('checked by hand'))} were checked by hand on "
         "pages a script cannot read (`docs/evidence/current_law_hand_checks.yaml`)."),
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
