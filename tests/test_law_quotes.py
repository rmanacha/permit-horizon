"""The current-law quote check, offline: a cached page, a found quote, a missing one, a PDF."""

import yaml

from hre.validation import law_quotes as lq


def test_normalize_handles_quotes_dashes_spaces_and_links():
    assert lq.normalize("The “permitted use” – one unit") == lq.normalize('the "permitted use" - one unit')
    assert lq.normalize(lq.html_to_text('Section <a href="x">10-21-303</a> , within')) == "section 10-21-303, within"


def _law_file(tmp_path, quote_ok: str, quote_bad: str):
    doc = {"state": "ZZ", "scenarios": {"adu": {
        "record": {"url": "https://example.gov/s1.htm", "quote": quote_ok},
        "features": [{"id": "adu_per_lot", "sources": [
            {"url": "https://example.gov/s1.htm", "locator": "I", "quote": quote_bad},
            {"url": "https://example.gov/act.pdf", "locator": "s. 2", "quote": "anything"}]}]}}}
    law = tmp_path / "law"
    law.mkdir()
    (law / "ZZ.yaml").write_text(yaml.safe_dump(doc))
    return law


def test_check_reports_found_missing_and_pdf(tmp_path):
    law = _law_file(tmp_path, "One accessory dwelling unit shall be allowed", "two accessory dwelling units")
    cache = tmp_path / "raw" / "law_pages"
    cache.mkdir(parents=True)
    page = "<html><script>var x=1;</script><p>I. One accessory dwelling&nbsp;unit <b>shall</b> be allowed.</p></html>"
    lq._cache_path("https://example.gov/s1.htm", cache).write_text(page)
    rows = lq.check(law, fetch=False, data_dir=tmp_path / "raw")
    assert [r["status"] for r in rows][:2] == ["found", "NOT FOUND"]
    assert "not cached" in rows[2]["status"]                     # the PDF was never fetched here
    md = lq.render_markdown(rows, "2026-11-03")
    assert "1 of 3 quotes found" in md and "## Not found" in md


def test_pdf_margin_line_numbers_are_dropped():
    assert lq.normalize(lq.LINE_NUMBER.sub("", "12  shall allow one accessory\n13  dwelling unit")) == \
        "shall allow one accessory dwelling unit"


def test_uncached_page_without_fetch_is_reported_not_guessed(tmp_path):
    law = _law_file(tmp_path, "x", "y")
    rows = lq.check(law, fetch=False, data_dir=tmp_path / "raw")
    assert rows[0]["found"] is None and "not cached" in rows[0]["status"]


def test_glued_line_numbers_go_but_thousands_stay():
    text = "is hereby amended by12\nan ADU of at least 1,000\nsquare feet"
    assert lq.GLUED_LINE_NUMBER.sub("", text) == "is hereby amended by\nan ADU of at least 1,000\nsquare feet"
