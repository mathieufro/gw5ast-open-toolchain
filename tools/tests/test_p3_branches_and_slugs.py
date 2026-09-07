"""`P3.T02` -- the Phase-3 branches and the 13 evidence slugs exist.

`D3` gives each fork one upstream-ready branch per deliverable; Phase 3's are
`prim/io-iologic-138c` (apicula) and `gowin/io-iologic-138c` (nextpnr). Each
must resolve *and* have an upstream, because a branch that was never pushed is
not landed.
"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths  # noqa: E402

#: The 13 evidence slugs this phase owns (`P3` "Owned" table).
P3_SLUGS = ("iob-bank", "pin-to-hclk", "oddr-iddr", "oser", "ides",
            "oser16-ides16", "iodelay", "tlvds", "tlvds-iobuf", "elvds",
            "bank-coercion", "adc", "osc")

#: `<repo dir>: <branch>` -- the fork branches `P3.T02` creates.
P3_BRANCHES = {"apicula": "prim/io-iologic-138c",
               "nextpnr": "gowin/io-iologic-138c"}


def _git(repo, *args):
    return subprocess.run(("git", "-C", repo) + args, capture_output=True,
                          text=True, check=False)


def test_p3_evidence_dirs_exist():
    """13 slugs, each with an (initially empty) ledger and a summary."""
    root = os.path.join(paths.OTC_ROOT, "evidence")
    for slug in P3_SLUGS:
        assert os.path.isfile(os.path.join(root, slug, "runs.jsonl")), slug
        assert os.path.isfile(os.path.join(root, slug, "summary.md")), slug
    assert len(P3_SLUGS) == 13


@pytest.mark.parametrize("name,branch", sorted(P3_BRANCHES.items()))
def test_p3_branches_exist(name, branch):
    """The branch resolves in the fork and tracks an upstream."""
    repo = paths.apicula_root() if name == "apicula" else \
        paths.sibling("nextpnr", "NEXTPNR_DIR")
    assert _git(repo, "rev-parse", "--verify", branch).returncode == 0
    upstream = _git(repo, "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}")
    assert upstream.returncode == 0, upstream.stderr
    assert upstream.stdout.strip() == f"origin/{branch}"
