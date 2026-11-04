"""The submission checklist, checked item by item.

    make check              # = uv run python scripts/check_submission.py
    make check STRICT=1     # the run on submission day: anything pending fails too

Each item prints PASS, FAIL, PENDING or NOTE. FAIL means something in the repository is wrong
and the script exits non-zero. PENDING means it waits on the repository owner (a signature, a
setting, a click on GitHub); by default it is reported without failing, and with --strict it
fails. NOTE items are reminders that never fail.

Options: --strict; --skip-tests (do not run pytest and the website tests); --offline (do not
ask GitHub for the release or the public site, which then read PENDING).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import yaml

from hre import docs
from hre.data import net
from hre.model.run import OUTCOMES, validate_results

SITE = "https://rmanacha.github.io/permit-horizon/"
RELEASE_API = "https://api.github.com/repos/rmanacha/permit-horizon/releases/tags/v1.0.0-submission"
SHOWCASE = ("UT", "NH", "AZ")
# The seven documents a reviewer reads, with the headings each must keep (the starter template's).
DOCS = {
    "README.md": ["Command contract", "Documentation", "Team", "License"],
    "docs/MODEL_AND_ASSUMPTIONS.md": ["Purpose and Scope", "Core Assumptions and Their Rationale",
                                      "Data Sources and Cleaning Steps", "Methodological Approach",
                                      "Limitations and Known Edge Cases", "Sensitivity Notes",
                                      "Intended Users and Appropriate Use Cases"],
    "docs/POLICY_SCENARIO_COMPARISON.md": ["Scenarios Addressed", "Ranking of Results", "What Drives the Differences",
                                           "Which Assumptions Matter Most", "What the Tool Cannot Say"],
    "docs/DATA_PROVENANCE.md": ["Dataset Inventory", "Cleaning and Preparation", "Known Limitations",
                                "Restricted, Sensitive, or Personal Data"],
    "docs/DISCLOSURES.md": ["AI-Assisted Code Generation", "Pretrained Models, Weights, and Embeddings",
                            "External APIs and Hosted Services", "Dependency Licenses", "Generated or Copied Code"],
    "docs/JUDGE_GUIDE.md": ["Submission checklist"],
    "docs/GLOSSARY.md": [],
}
# The starter template's bracketed prompts begin with these words; none may survive.
TEMPLATE_PROMPT = re.compile(r"\[(List|What|Explain|Summarize|State|Rank|Identify|For each|Note any|Confirm|Who should|"
                             r"Which|Coverage gaps|Fill in|Replace|e\.g\.|name\]|value\]|why\]|citation\])")
SECRET_NAMES = re.compile(r"(^|/)(\.env(\.(?!example$)[^/]*)?|id_rsa|id_ed25519|credentials\.json|"
                          r"service-account[^/]*\.json|secrets\.[^/]+)$|\.(pem|key|p12|pfx)$")
SECRET_TEXT = re.compile(r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|"
                         r"xox[abprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-ant-[A-Za-z0-9_-]{20,}|"
                         r"AIza[0-9A-Za-z_-]{35}")
FORBIDDEN = re.compile(r"\.mp3$|(^|/)(transcripts?|podcast)[^/]*$", re.IGNORECASE)
DATA_ALLOWED = ("data/README.md", "data/DATA_SOURCES.md", "data/sample/", "data/manifests/")
SECURITY_FIELDS = ("Code scanning open alerts", "Dependabot open alerts", "Secret scanning open alerts",
                   "Push protection", "Checked by and date")


@dataclass
class Item:
    status: str          # PASS, FAIL, PENDING, NOTE
    name: str
    detail: str


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


# ------------------------------------------------------------------ repository checks


def check_licence() -> Item:
    lic = REPO / "LICENSE"
    text = lic.read_text(encoding="utf-8") if lic.exists() else ""
    py = re.search(r'^license = "([^"]+)"', (REPO / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE)
    web = json.loads((REPO / "web" / "package.json").read_text(encoding="utf-8")).get("license")
    ok = "Apache License" in text and "Version 2.0" in text and py and py.group(1) == "Apache-2.0" and web == "Apache-2.0"
    return Item("PASS" if ok else "FAIL", "Licence",
                "LICENSE is Apache-2.0, as pyproject.toml and web/package.json declare" if ok
                else "LICENSE, pyproject.toml and web/package.json must all say Apache-2.0")


def check_secrets(files: list[str]) -> Item:
    named = [f for f in files if SECRET_NAMES.search(f)]
    found = []
    for f in files:
        p = REPO / f
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET_TEXT.search(text):
            found.append(f)
    if named or found:
        return Item("FAIL", "No secrets", f"secret-looking files {named} or contents in {found}")
    return Item("PASS", "No secrets", f"no .env, key or credentials file and no key pattern in {len(files)} tracked files")


def check_forbidden(files: list[str]) -> Item:
    bad = [f for f in files if FORBIDDEN.search(f)]
    data = [f for f in files if f.startswith("data/") and not f.startswith(DATA_ALLOWED) and f not in DATA_ALLOWED]
    if bad or data:
        return Item("FAIL", "No audio, transcripts or raw data", f"tracked: {bad + data}")
    return Item("PASS", "No audio, transcripts or raw data",
                "under data/ only the README, the source list, fixtures and manifests are tracked")


def check_docs() -> Item:
    problems = []
    for rel, headings in DOCS.items():
        p = REPO / rel
        if not p.exists():
            problems.append(f"{rel} missing")
            continue
        text = p.read_text(encoding="utf-8")
        if m := TEMPLATE_PROMPT.search(text):
            problems.append(f"{rel} still has a template prompt: {m.group(0)}")
        for h in headings:
            if not re.search(rf"^#+ {re.escape(h)}\s*$", text, re.MULTILINE):
                problems.append(f"{rel} lacks the heading '{h}'")
    if problems:
        return Item("FAIL", "The seven documents", "; ".join(problems))
    return Item("PASS", "The seven documents", "present, template headings kept, no template prompt left: "
                + ", ".join(Path(d).name for d in DOCS))


def check_generated() -> Item:
    found = docs.problems()
    if found:
        return Item("FAIL", "Generated tables", "; ".join(found))
    return Item("PASS", "Generated tables", "every generated table matches the register, the law files, the ledger, "
                "the bundle and the SBOM")


def check_pages() -> list[Item]:
    path = REPO / "docs" / "evidence" / "page_counts.json"
    if not path.exists():
        return [Item("FAIL", "Page limits", "docs/evidence/page_counts.json missing (make pages)")]
    out = []
    for rel, c in json.loads(path.read_text(encoding="utf-8"))["documents"].items():
        sha = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        name = f"Page limit: {Path(rel).name}"
        if c["pages"] > c["limit"]:
            out.append(Item("FAIL", name, f"{c['pages']} pages, over the limit of {c['limit']}"))
        elif sha != c["sha256"]:
            out.append(Item("PENDING", name, f"{c['pages']} of {c['limit']} pages when counted on {c['counted_on']}, "
                                             "but the document changed since: run make pages"))
        else:
            out.append(Item("PASS", name, f"{c['pages']} of {c['limit']} pages (counted {c['counted_on']})"))
    return out


def unlabeled_ranges(obj: object, label: str | None = None) -> int:
    """Number ranges (low, mid, high) with no outcome label on themselves or an enclosing block."""
    n = 0
    if isinstance(obj, dict):
        here = obj["outcome"] if isinstance(obj.get("outcome"), str) else label
        if here is None and all(isinstance(obj.get(k), (int, float)) for k in ("low", "mid", "high")):
            n += 1
        n += sum(unlabeled_ranges(v, here) for v in obj.values())
    elif isinstance(obj, list):
        n += sum(unlabeled_ranges(v, label) for v in obj)
    return n


def check_bundle() -> Item:
    bundle = REPO / "web" / "public" / "results"
    index = json.loads((bundle / "index.json").read_text(encoding="utf-8"))
    states = sorted(r["state"] for r in index["states"])
    problems = [] if len(states) == 51 else [f"{len(states)} jurisdictions in index.json, not 51"]
    labels = set()
    for st in states:
        r = json.loads((bundle / f"{st}.json").read_text(encoding="utf-8"))
        problems += [f"{st}: {p}" for p in validate_results(r)]
        if (n := unlabeled_ranges(r)):
            problems.append(f"{st}: {n} number ranges without an outcome label")
        for s in r["scenarios"].values():
            for block in (s["benchmark"], s["increment"], s["total"], *s["cases"].values()):
                labels.add(block.get("outcome"))
    if not labels <= set(OUTCOMES):
        problems.append(f"labels outside the fixed set: {labels - set(OUTCOMES)}")
    if problems:
        return Item("FAIL", "Results for all 51 jurisdictions", "; ".join(problems[:5]))
    return Item("PASS", "Results for all 51 jurisdictions", "every file passes the results validator and every "
                "number range carries an outcome label (" + ", ".join(sorted(labels)) + ")")


def _count(pattern: str, text: str) -> int:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else 0


def check_tests(skip: bool) -> list[Item]:
    site = (REPO / "web" / "src" / "content" / "site.ts").read_text(encoding="utf-8")
    m = re.search(r"TEST_COUNTS = \{ python: (\d+), web: (\d+) \}", site)
    shown = (int(m.group(1)), int(m.group(2))) if m else None
    if skip:
        return [Item("NOTE", "Tests", "not run (--skip-tests)")]
    py = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=REPO,
                        capture_output=True, text=True, check=False)
    tail = py.stdout.strip().splitlines()[-1] if py.stdout.strip() else py.stderr[-300:]
    passed, failed, skipped = (_count(rf"(\d+) {w}", tail) for w in ("passed", "failed", "skipped"))
    items = [Item("PASS" if py.returncode == 0 else "FAIL", "Python tests", tail)]
    web_total = None
    if shutil.which("npm") and (REPO / "web" / "node_modules").exists():
        w = subprocess.run(["npm", "test", "--silent"], cwd=REPO / "web", capture_output=True, text=True, check=False)
        web_total = _count(r"ℹ tests (\d+)", w.stdout)
        web_fail = _count(r"ℹ fail (\d+)", w.stdout)
        items.append(Item("PASS" if w.returncode == 0 and not web_fail else "FAIL", "Website tests",
                          f"{web_total} tests, {web_fail} failed"))
    else:
        items.append(Item("NOTE", "Website tests", "not run here (needs Node and make web once); CI runs them"))
    total = passed + failed + skipped
    if shown is None:
        items.append(Item("FAIL", "Test counts on the About page", "TEST_COUNTS not found in web/src/content/site.ts"))
    elif shown[0] != total or (web_total is not None and shown[1] != web_total):
        items.append(Item("FAIL", "Test counts on the About page",
                          f"the page says {shown[0]} Python and {shown[1]} website tests; this run has {total} and "
                          f"{web_total}: update TEST_COUNTS in web/src/content/site.ts"))
    else:
        items.append(Item("PASS", "Test counts on the About page", f"{shown[0]} Python and {shown[1]} website tests, "
                          "as the page says"))
    return items


def check_sbom() -> Item:
    if not docs.SBOM_PATH.exists():
        return Item("PENDING", "SBOM", "docs/sbom/sbom.spdx.json missing: make sbom (or Insights > Dependency graph > "
                    "Export SBOM)")
    doc = json.loads(docs.SBOM_PATH.read_text(encoding="utf-8"))
    bad = docs.licence_problems()
    py = {(docs._norm(p["name"]), p["version"]) for p in docs.sbom_packages() if p["ecosystem"] == "pypi"}
    npm = {(p["name"], p["version"]) for p in docs.sbom_packages() if p["ecosystem"] == "npm"}
    same = py == {(n, v) for n, (v, _) in docs.uv_packages().items()} and npm == set(docs.npm_packages())
    if bad or not same:
        return Item("FAIL", "SBOM", f"licences {bad}; matches the lock files: {same} (run make sbom after CI)")
    return Item("PASS", "SBOM", f"{len(doc['packages'])} packages, created {doc['creationInfo']['created']}, the same "
                "as uv.lock and web/package-lock.json, every licence permissive")


# ------------------------------------------------------------------ items that wait on the owner


def check_reviews() -> Item:
    pending = []
    for st in SHOWCASE:
        doc = yaml.safe_load((REPO / "src" / "hre" / "current_law" / f"{st}.yaml").read_text(encoding="utf-8"))
        for sc, s in doc["scenarios"].items():
            h = s.get("human_review") or {}
            if not (h.get("status") == "reviewed" and h.get("by") and h.get("date")):
                pending.append(f"{st} {sc}")
    total = 5 * len(SHOWCASE)
    if pending:
        return Item("PENDING", "Human review of the showcase laws",
                    f"{total - len(pending)} of {total} signed; waiting: {', '.join(pending)} "
                    "(docs/evidence/current_law_review_ut_nh_az.md)")
    return Item("PASS", "Human review of the showcase laws", f"all {total} Utah, New Hampshire and Arizona records signed")


def security_block(text: str) -> dict[str, str]:
    out = {}
    for field in SECURITY_FIELDS:
        m = re.search(rf"^- {re.escape(field)}:[ \t]*(.*)$", text, re.MULTILINE)
        out[field] = m.group(1).strip() if m else ""
    return out


def judge_security(values: dict[str, str]) -> tuple[str, str]:
    """(status, detail) for the owner's security block."""
    blank = [k for k, v in values.items() if not v]
    if blank:
        return "PENDING", f"not yet filled in: {', '.join(blank)} (docs/evidence/security_gates.md)"
    bad = []
    for field in SECURITY_FIELDS[:3]:
        v = values[field]
        n = re.match(r"(\d+)", v)
        if not n:
            bad.append(f"{field} is not a count")
        elif int(n.group(1)) > 0 and "justified" not in v.lower():
            bad.append(f"{field}: {v}")
    if not values["Push protection"].lower().startswith(("on", "enabled", "yes")):
        bad.append(f"Push protection: {values['Push protection']}")
    if bad:
        return "FAIL", "; ".join(bad)
    detail = (f"open alerts: code scanning {values[SECURITY_FIELDS[0]]}, Dependabot {values[SECURITY_FIELDS[1]]}, "
              f"secret scanning {values[SECURITY_FIELDS[2]]}; push protection {values['Push protection']} "
              f"({values['Checked by and date']})")
    return "PASS", detail


def check_security() -> Item:
    text = (REPO / "docs" / "evidence" / "security_gates.md").read_text(encoding="utf-8")
    status, detail = judge_security(security_block(text))
    return Item(status, "Security alert pages", detail)


def check_release(offline: bool) -> Item:
    if offline:
        return Item("PENDING", "Release v1.0.0-submission", "not checked (--offline)")
    try:
        rel = net.get_json(RELEASE_API, headers={"User-Agent": "permit-horizon-check"}, timeout=20)
    except net.HTTPError as e:
        if e.status == 404:
            return Item("PENDING", "Release v1.0.0-submission", "not created yet (the owner creates it on GitHub; "
                        "body in docs/RELEASE_NOTES.md)")
        return Item("PENDING", "Release v1.0.0-submission", f"GitHub answered {e.status}")
    except net.TRANSIENT as e:
        return Item("PENDING", "Release v1.0.0-submission", f"could not reach GitHub ({type(e).__name__})")
    assets = {a["name"] for a in rel.get("assets", [])}
    if not any(a.endswith(".spdx.json") or a.startswith("sbom") for a in assets):
        return Item("FAIL", "Release v1.0.0-submission", f"exists but has no SBOM attached (assets: {sorted(assets)})")
    return Item("PASS", "Release v1.0.0-submission", f"published {rel.get('published_at')}, assets: {sorted(assets)}")


def check_site(offline: bool) -> Item:
    if offline:
        return Item("PENDING", "Public website", "not checked (--offline)")
    local = json.loads((REPO / "web" / "public" / "results" / "meta.json").read_text(encoding="utf-8"))
    try:
        live = net.get_json(SITE + "results/meta.json", headers={"User-Agent": "permit-horizon-check"}, timeout=20)
    except net.HTTPError as e:
        return Item("PENDING", "Public website", f"{SITE} answered {e.status}: Settings > Pages > Source: GitHub Actions")
    except net.TRANSIENT as e:
        return Item("PENDING", "Public website", f"could not reach {SITE} ({type(e).__name__})")
    if live.get("git_shas") != local.get("git_shas"):
        return Item("PENDING", "Public website", f"live bundle {live.get('git_shas')} differs from this checkout's "
                    f"{local.get('git_shas')}: wait for the Pages workflow on the latest push")
    return Item("PASS", "Public website", f"{SITE} serves the same bundle ({local['git_shas'][0][:7]})")


def notes() -> list[Item]:
    usability = (REPO / "docs" / "evidence" / "usability_check.md").read_text(encoding="utf-8")
    ran = "Not yet run" not in usability.split("## Results", 1)[-1]
    pa = yaml.safe_load((REPO / "src" / "hre" / "current_law" / "PA.yaml").read_text(encoding="utf-8"))
    pa_date = pa["scenarios"]["adu"]["record"].get("accessed")
    return [
        Item("NOTE", "Usability check", "recorded" if ran else "not yet run (docs/evidence/usability_check.md)"),
        Item("NOTE", "Pennsylvania ADU bill", f"PA.yaml last checked {pa_date}; recheck the statute before submitting"),
        Item("NOTE", "Deck and demo video", "made in the next phase; not checked here"),
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--strict", action="store_true", help="pending items fail too (the submission run)")
    ap.add_argument("--skip-tests", action="store_true", help="do not run the test suites")
    ap.add_argument("--offline", action="store_true", help="do not ask GitHub for the release or the public site")
    a = ap.parse_args(argv)
    files = tracked_files()
    items = [check_licence(), check_secrets(files), check_forbidden(files), check_docs(), check_generated(),
             *check_pages(), check_bundle(), check_sbom(), *check_tests(a.skip_tests),
             check_reviews(), check_security(), check_release(a.offline), check_site(a.offline), *notes()]
    width = max(len(i.name) for i in items)
    for i in items:
        print(f"{i.status:<8} {i.name:<{width}}  {i.detail}")
    fails = sum(i.status == "FAIL" for i in items)
    pending = sum(i.status == "PENDING" for i in items)
    mode = "strict" if a.strict else "default"
    print(f"\n{sum(i.status == 'PASS' for i in items)} pass, {fails} fail, {pending} pending ({mode} mode: "
          + ("pending items fail" if a.strict else "pending items are reported, not failed") + ")")
    return 1 if fails or (a.strict and pending) else 0


if __name__ == "__main__":
    sys.exit(main())
