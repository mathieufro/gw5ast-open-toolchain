"""`P3.T01` -- the three named checks over the Phase-3 preflight artefacts.

These read the log the preflight run wrote plus the apicula source; they never
rebuild the chipdb themselves, so the phase pays for that build exactly once.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths  # noqa: E402

LOG = os.path.join(paths.OTC_ROOT, "evidence", "_runs", "p3-preflight.log")


def _log():
    if not os.path.isfile(LOG):
        pytest.skip("p3-preflight.log absent; run tools/p3_preflight.py first")
    return open(LOG, encoding="utf-8").read()


def test_p3_preflight_chipdb_builds():
    """Check 1 passed, i.e. `chipdb_builder GW5AST-138C` exited 0."""
    line = [l for l in _log().splitlines() if l.endswith(
        "checks") or " 1 chipdb builds" in l]
    assert any(l.startswith("ok  ") and "1 chipdb builds" in l for l in line)
    assert re.search(r"^chipdb_sha256: [0-9a-f]{64}$", _log(), re.M)


def test_p3_preflight_has_5a_hclk():
    """Check 2 saw `HAS_5A_HCLK` exactly once in the canonical chipdb."""
    assert "HAS_5A_HCLK count=1" in _log()


def test_p3_preflight_guard_state_one():
    """`D39` state (1): the misspelling `GW5AST-138AC` is nowhere in `chipdb.py`."""
    apicula = paths.apicula_root()
    text = open(os.path.join(apicula, "apycula", "chipdb.py"),
                encoding="utf-8").read()
    assert text.count("GW5AST-138AC") == 0
