"""The stored SBOM (docs/sbom/sbom.spdx.json, from GitHub's dependency graph) matches the lock files.

If this fails after a dependency changed: push, wait for GitHub's dependency-graph update (the
`update-uv-graph` check on the commit), run `make sbom`, and commit the new file.
"""

import json

import pytest

from hre import docs

pytestmark = pytest.mark.skipif(not docs.SBOM_PATH.exists(), reason="no stored SBOM yet (make sbom)")


def test_sbom_is_github_spdx_for_this_repository():
    doc = json.loads(docs.SBOM_PATH.read_text(encoding="utf-8"))
    assert doc["spdxVersion"] == "SPDX-2.3"
    assert doc["name"] == "com.github.rmanacha/permit-horizon"
    assert "GitHub.com-Dependency-Graph" in " ".join(doc["creationInfo"]["creators"])


def test_python_packages_match_uv_lock():
    sbom = {(docs._norm(p["name"]), p["version"]) for p in docs.sbom_packages() if p["ecosystem"] == "pypi"}
    lock = {(n, v) for n, (v, _) in docs.uv_packages().items()}
    assert sbom == lock, {"only in the SBOM": sorted(sbom - lock), "only in uv.lock": sorted(lock - sbom)}


def test_npm_packages_match_package_lock():
    sbom = {(p["name"], p["version"]) for p in docs.sbom_packages() if p["ecosystem"] == "npm"}
    lock = set(docs.npm_packages())
    assert sbom == lock, {"only in the SBOM": sorted(sbom - lock), "only in package-lock.json": sorted(lock - sbom)}


def test_every_licence_is_permissive():
    assert not docs.licence_problems()


def test_copyleft_licences_are_caught():
    assert not docs.licence_tokens("MPL-2.0") <= docs.PERMISSIVE
    assert not docs.licence_tokens("MIT AND LGPL-3.0-or-later") <= docs.PERMISSIVE
    assert docs.licence_tokens("(Apache-2.0 OR BSD-2-Clause) AND MIT") <= docs.PERMISSIVE


def test_every_workflow_action_has_a_stated_licence():
    actions = {p["name"] for p in docs.sbom_packages() if p["ecosystem"] == "githubactions"}
    assert actions and actions <= set(docs.ACTION_LICENCES)
