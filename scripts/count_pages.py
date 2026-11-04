"""Count the printed pages of the two documents with page limits, and store the counts.

    make pages        # = uv run --with markdown==3.8 python scripts/count_pages.py

The challenge limits the Model and Assumptions Overview to 25 pages and the Policy Scenario
Comparison to 4, single-spaced. A Markdown file has no pages, so this script prints each one the
way a reader would: Python-Markdown (BSD-3-Clause, pulled in for this run only by ``uv run --with``,
never a project dependency) turns it into HTML; headless Google Chrome prints that HTML to PDF on US
Letter paper with one-inch margins, 11 pt body text at single spacing (line height 1.2) and 8.5 pt
tables; pypdf (already in the locked environment, extra ``law``) counts the pages.

Output: ``docs/evidence/page_counts.json`` (committed: pages, limit, the SHA-256 of the Markdown
that was counted, date, method) and the PDFs in ``docs/pdf/`` (git-ignored; attach them to the
submission). ``scripts/check_submission.py`` fails when a count is over its limit and reports a
count as stale when the document changed after it was counted.

Chrome: the macOS default path, or set CHROME=/path/to/chrome (Chromium works too).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
LIMITS = {"docs/MODEL_AND_ASSUMPTIONS.md": 25, "docs/POLICY_SCENARIO_COMPARISON.md": 4}
OUT_JSON = REPO / "docs" / "evidence" / "page_counts.json"
PDF_DIR = REPO / "docs" / "pdf"
CHROME_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium", "google-chrome", "chromium")

CSS = """
@page { size: Letter; margin: 1in; }
html { font-size: 11pt; }
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.2; color: #000; margin: 0; }
h1 { font-size: 15pt; margin: 14pt 0 6pt; } h2 { font-size: 12.5pt; margin: 12pt 0 4pt; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; }
p, ul, ol { margin: 0 0 6pt; } li { margin: 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; line-height: 1.15; margin: 4pt 0 8pt; }
th, td { border: 0.5pt solid #777; padding: 2pt 3pt; vertical-align: top; text-align: left; }
code { font-size: 9pt; } pre { font-size: 8.5pt; white-space: pre-wrap; }
img { max-width: 100%; }
a { color: #000; text-decoration: none; }
"""

METHOD = ("Python-Markdown 3.8 (tables, fenced code) to HTML; headless Google Chrome print to PDF, US Letter, "
          "1 inch margins, 11 pt Georgia at line height 1.2 (single-spaced), tables 8.5 pt; pages counted with "
          "pypdf (scripts/count_pages.py)")


def chrome() -> str:
    for c in ([os.environ["CHROME"]] if os.environ.get("CHROME") else []) + list(CHROME_PATHS):
        if Path(c).exists() or shutil.which(c):
            return c
    sys.exit("Chrome or Chromium not found; set CHROME=/path/to/chrome")


def to_pdf(md_path: Path, pdf_path: Path, browser: str) -> int:
    body = markdown.markdown(md_path.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    base = md_path.parent.resolve().as_uri() + "/"
    html = (f'<!doctype html><html><head><meta charset="utf-8"><base href="{base}">'
            f"<title>{md_path.stem}</title><style>{CSS}</style></head><body>{body}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={tmp}/profile", "--allow-file-access-from-files",
                        f"--print-to-pdf={pdf_path}", page.as_uri()],
                       check=True, capture_output=True, timeout=120)
    return len(PdfReader(str(pdf_path)).pages)


def main() -> int:
    browser = chrome()
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    docs = {}
    worst = 0
    for rel, limit in LIMITS.items():
        src = REPO / rel
        pages = to_pdf(src, PDF_DIR / (src.stem + ".pdf"), browser)
        docs[rel] = {"pages": pages, "limit": limit, "counted_on": today,
                     "sha256": hashlib.sha256(src.read_bytes()).hexdigest()}
        flag = "within" if pages <= limit else "OVER"
        worst = max(worst, pages > limit)
        print(f"{rel}: {pages} pages ({flag} the limit of {limit}) -> docs/pdf/{src.stem}.pdf")
    OUT_JSON.write_text(json.dumps({"method": METHOD, "documents": docs}, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main())
