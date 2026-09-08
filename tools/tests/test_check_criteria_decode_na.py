"""Clause (c) against rows that have nothing to compare.

`DONE-STD` clause (c) is "the two decodes agree", which presupposes two
bitstreams.  Two honest kinds of row have only one: a design the open flow
cannot build at all (`EC9`), and a vendor-side measurement such as the IOB
safety diff.  Both report `n/a`, and both were previously unclosable for a
reason that had nothing to do with what they measured.
"""
import sys

from tools import check_criteria as cc


def _row(c1, c2, notes=""):
    return {"decode_check": {"c1": c1, "c2": c2}, "notes": notes}


def test_both_ok_satisfies_clause_c():
    assert cc._decode_ok(_row("ok", "ok"))


def test_a_mismatch_never_satisfies_clause_c():
    assert not cc._decode_ok(_row("mismatch", "ok", "EC9: whatever"))
    assert not cc._decode_ok(_row("ok", "mismatch", "kind=measurement"))


def test_bare_na_does_not_satisfy_clause_c():
    """An `n/a` with no reason is exactly the silent pass to avoid."""
    assert not cc._decode_ok(_row("n/a", "n/a"))
    assert not cc._decode_ok(_row("n/a", "n/a", "nothing relevant here"))


def test_na_with_ec9_satisfies_clause_c():
    assert cc._decode_ok(
        _row("n/a", "n/a", "E1 unreachable, EC9: the open flow cannot build"))


def test_na_on_a_vendor_measurement_satisfies_clause_c():
    assert cc._decode_ok(
        _row("n/a", "n/a", "kind=measurement (vendor decode, not equivalence)"))


def test_a_missing_decode_check_is_not_a_pass():
    assert not cc._decode_ok({"notes": "EC9"})
