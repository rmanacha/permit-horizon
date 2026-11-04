"""Store the repository's SBOM (software bill of materials) from GitHub's dependency graph.

    make sbom        # = uv run python scripts/fetch_sbom.py

GitHub builds the SBOM from the lock files it finds in the repository (uv.lock,
web/package-lock.json and the workflow files). The "Export SBOM" button on the repository's
Insights > Dependency graph page downloads exactly this SPDX 2.3 JSON document; for a public
repository the same document is served without a sign-in at
https://api.github.com/repos/rmanacha/permit-horizon/dependency-graph/sbom (wrapped in
{"sbom": ...}). This script saves the inner document to docs/sbom/sbom.spdx.json.

Run it after the dependency graph has caught up with the latest push (the repository's
"update-uv-graph" check has finished). tests/test_sbom.py then checks the stored package list
against uv.lock and web/package-lock.json, and every licence against the project's rule
(MIT, ISC, BSD, Apache and other permissive licences only).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from hre.data import net

API = "https://api.github.com/repos/rmanacha/permit-horizon/dependency-graph/sbom"
OUT = REPO / "docs" / "sbom" / "sbom.spdx.json"


def main() -> int:
    doc = net.with_retries(lambda: net.get_json(API, headers={"User-Agent": "permit-horizon-sbom",
                                                              "Accept": "application/vnd.github+json"}))
    sbom = doc["sbom"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    kinds: dict[str, int] = {}
    for p in sbom["packages"]:
        ref = next((r["referenceLocator"] for r in p.get("externalRefs") or [] if r.get("referenceType") == "purl"), "")
        kind = ref.split("/", 1)[0].removeprefix("pkg:") or "other"
        kinds[kind] = kinds.get(kind, 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    print(f"wrote {OUT.relative_to(REPO)}: {sbom['spdxVersion']}, created {sbom['creationInfo']['created']}, "
          f"{len(sbom['packages'])} packages ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
