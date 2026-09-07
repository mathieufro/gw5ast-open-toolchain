"""Tests for `check_criteria.py --ae350` (`P2.T32`, `V18`, `S19` non-hw half).

`--ae350` is a separate mode from the rest of the tool: it takes
`--chipdb`/`--evidence` instead of the positional `spec_primitives`/
`evidence_dir`, and asserts four structural facts (`evidence/ae350/`:
`e1-138c.md`, `config-fuses-138c.md`, `reconciliation.md`) rather than
reading `spec-primitives.md` at all. The per-check functions are exercised
directly against small fakes so a missing chipdb build never blocks these
tests; one end-to-end test runs against the real installed chipdb and
evidence tree and is skipped if either is absent.
"""
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import pytest

import check_criteria as cc  # noqa: E402

ANCHOR = cc.AE350_ANCHOR_TILE  # (0, 159)
CORE_CLK_TAP = cc.AE350_CORE_CLK_FABRIC_TAP  # (0, 87, "CLK1")
NODE_PREFIX = f"X{ANCHOR[1]}Y{ANCHOR[0]}/AE350_SOC"


class FakeDevice:
    """The two `Device` attributes `--ae350`'s checks actually read."""

    def __init__(self, extra_func=None, nodes=None):
        self.extra_func = extra_func or {}
        self.nodes = nodes or {}


def _populated_ae350_extra_func():
    return {ANCHOR: {"ae350": {"ins": {"P0": "W0"}, "outs": {"P1": "W1"}}}}


def _core_clk_node():
    return {
        f"{NODE_PREFIX}CORE_CLKCLK1": (
            "TILE_CLK", {(ANCHOR[0], ANCHOR[1], "AE350_SOCCORE_CLKCLK1"), CORE_CLK_TAP}
        )
    }


def _write_evidence_ae350(tmp_path, e1_text="", config_fuses_text=None,
                           reconciliation_text="see the 637-entry table"):
    ae350_dir = tmp_path / "evidence" / "ae350"
    ae350_dir.mkdir(parents=True)
    (ae350_dir / "e1-138c.md").write_text(e1_text, encoding="utf-8")
    if config_fuses_text is not None:
        (ae350_dir / "config-fuses-138c.md").write_text(config_fuses_text, encoding="utf-8")
    if reconciliation_text is not None:
        (ae350_dir / "reconciliation.md").write_text(reconciliation_text, encoding="utf-8")
    return str(tmp_path / "evidence")


# --------------------------------------------------------------------------
# 1. bel exists
# --------------------------------------------------------------------------
def test_bel_exists_when_extra_func_is_populated_at_the_anchor():
    db = FakeDevice(extra_func=_populated_ae350_extra_func())
    ok, detail = cc.check_ae350_bel_exists(db)
    assert ok
    assert str(ANCHOR) in detail


def test_bel_missing_when_extra_func_has_no_ae350_entry():
    db = FakeDevice(extra_func={})
    ok, _detail = cc.check_ae350_bel_exists(db)
    assert not ok


def test_bel_missing_when_ins_or_outs_is_empty():
    db = FakeDevice(extra_func={ANCHOR: {"ae350": {"ins": {}, "outs": {"P1": "W1"}}}})
    ok, _detail = cc.check_ae350_bel_exists(db)
    assert not ok


# --------------------------------------------------------------------------
# 2. CORE_CLK non-routable
# --------------------------------------------------------------------------
def test_core_clk_nonroutable_when_tap_present_and_evidence_confirms(tmp_path):
    db = FakeDevice(nodes=_core_clk_node())
    evidence = _write_evidence_ae350(
        tmp_path, e1_text="the tap is a fixed, non-routable connection to CORE_CLK")
    ok, _detail = cc.check_ae350_core_clk_nonroutable(db, evidence)
    assert ok


def test_core_clk_fails_when_chipdb_has_no_matching_tap(tmp_path):
    db = FakeDevice(nodes={})  # no AE350_SOC node routes anywhere
    evidence = _write_evidence_ae350(
        tmp_path, e1_text="a fixed, non-routable connection")
    ok, detail = cc.check_ae350_core_clk_nonroutable(db, evidence)
    assert not ok
    assert "no AE350_SOC node" in detail


def test_core_clk_fails_when_evidence_does_not_confirm_it(tmp_path):
    db = FakeDevice(nodes=_core_clk_node())
    evidence = _write_evidence_ae350(tmp_path, e1_text="nothing said about routability here")
    ok, detail = cc.check_ae350_core_clk_nonroutable(db, evidence)
    assert not ok
    assert "e1-138c.md" in detail


# --------------------------------------------------------------------------
# 3. fuse set
# --------------------------------------------------------------------------
def test_fuse_set_ok_when_e1_records_zero(tmp_path):
    evidence = _write_evidence_ae350(
        tmp_path, e1_text="... so the band is per-design and no bit marks the block's presence.")
    ok, detail = cc.check_ae350_fuse_set(evidence)
    assert ok
    assert "zero" in detail


def test_fuse_set_ok_when_a_nonzero_set_is_enumerated(tmp_path):
    evidence = _write_evidence_ae350(
        tmp_path, e1_text="unrelated", config_fuses_text="the set is 77 bits over 9 tiles")
    ok, detail = cc.check_ae350_fuse_set(evidence)
    assert ok
    assert "enumerated" in detail


def test_fuse_set_fails_when_neither_file_records_a_result(tmp_path):
    evidence = _write_evidence_ae350(tmp_path, e1_text="unrelated text")
    ok, _detail = cc.check_ae350_fuse_set(evidence)
    assert not ok


# --------------------------------------------------------------------------
# 4. reconciliation
# --------------------------------------------------------------------------
def test_reconciliation_ok_when_the_637_token_is_present(tmp_path):
    evidence = _write_evidence_ae350(tmp_path, reconciliation_text="637 table entries reconciled")
    ok, _detail = cc.check_ae350_reconciliation(evidence)
    assert ok


def test_reconciliation_fails_when_file_is_absent(tmp_path):
    evidence = _write_evidence_ae350(tmp_path, reconciliation_text=None)
    ok, detail = cc.check_ae350_reconciliation(evidence)
    assert not ok
    assert "absent" in detail


def test_reconciliation_fails_when_token_is_missing(tmp_path):
    evidence = _write_evidence_ae350(tmp_path, reconciliation_text="reconciled, no number given")
    ok, _detail = cc.check_ae350_reconciliation(evidence)
    assert not ok


# --------------------------------------------------------------------------
# 5. `check_ae350` aggregation and CLI wiring
# --------------------------------------------------------------------------
def _fake_chipdb_file(tmp_path, name="fake.msgpack.xz"):
    """`check_ae350` requires the path to exist before it even loads it."""
    path = tmp_path / name
    path.write_bytes(b"")
    return str(path)


def test_check_ae350_reports_4_of_4_and_exit_0_when_everything_is_measured(tmp_path, monkeypatch):
    db = FakeDevice(extra_func=_populated_ae350_extra_func(), nodes=_core_clk_node())
    evidence = _write_evidence_ae350(
        tmp_path,
        e1_text="fixed, non-routable connection; no bit marks the block's presence")

    # Bypass the real chipdb loader: check_ae350 takes a path and loads it
    # itself, so this test drives the per-check functions through the same
    # aggregation loop via a monkeypatched loader.
    import types
    monkeypatch.setattr(cc, "_import_apycula_chipdb",
                         lambda: types.SimpleNamespace(load_chipdb=lambda _p: db))

    satisfied, total, exit_code, lines = cc.check_ae350(_fake_chipdb_file(tmp_path), evidence)

    assert (satisfied, total) == (4, 4)
    assert exit_code == 0
    assert any(line.startswith("AE350 FAIL") for line in lines) is False


def test_check_ae350_fails_and_names_the_broken_check_when_core_clk_is_routable(tmp_path, monkeypatch):
    """Proof the guard can fail: no chipdb tap at all for CORE_CLK."""
    db = FakeDevice(extra_func=_populated_ae350_extra_func(), nodes={})
    evidence = _write_evidence_ae350(
        tmp_path,
        e1_text="fixed, non-routable connection; no bit marks the block's presence")

    import types
    monkeypatch.setattr(cc, "_import_apycula_chipdb",
                         lambda: types.SimpleNamespace(load_chipdb=lambda _p: db))

    satisfied, total, exit_code, lines = cc.check_ae350(_fake_chipdb_file(tmp_path), evidence)

    assert satisfied == 3
    assert total == 4
    assert exit_code == 1
    assert any("CORE_CLK non-routable" in line and "AE350 FAIL" in line for line in lines)


def test_check_ae350_fails_cleanly_when_chipdb_path_does_not_exist(tmp_path):
    evidence = _write_evidence_ae350(
        tmp_path,
        e1_text="fixed, non-routable connection; no bit marks the block's presence")
    satisfied, total, exit_code, lines = cc.check_ae350(
        str(tmp_path / "does-not-exist.msgpack.xz"), evidence)
    assert exit_code == 1
    assert satisfied < total
    assert any("chipdb not found" in line for line in lines)


def test_cli_ae350_flag_does_not_require_the_positional_arguments(tmp_path, capsys):
    """`--ae350` must not crash on the missing `spec_primitives`/`evidence_dir`
    positionals -- `V18`'s literal invocation never supplies them."""
    evidence = _write_evidence_ae350(
        tmp_path,
        e1_text="fixed, non-routable connection; no bit marks the block's presence")
    exit_code = cc.main([
        "--ae350",
        "--chipdb", str(tmp_path / "missing.msgpack.xz"),
        "--evidence", evidence,
    ])
    out = capsys.readouterr().out
    assert "AE350 ok:" in out
    assert exit_code in (0, 1)  # must not raise -- the chipdb legitimately can't load here


# --------------------------------------------------------------------------
# 6. end-to-end against the real installed chipdb and evidence tree
# --------------------------------------------------------------------------
def _real_chipdb_path():
    return os.path.join(
        os.path.dirname(TOOLS_DIR), "..", "apicula", "apycula", "GW5AST-138C.msgpack.xz")


def _real_evidence_dir():
    return os.path.join(TOOLS_DIR, "..", "evidence")


def test_ae350_ok_4_of_4_against_the_real_chipdb_and_evidence():
    chipdb_path = os.path.abspath(_real_chipdb_path())
    evidence_dir = os.path.abspath(_real_evidence_dir())
    if not os.path.isfile(chipdb_path):
        pytest.skip(f"{chipdb_path} is absent; run `make apycula/GW5AST-138C.msgpack.xz`")
    satisfied, total, exit_code, lines = cc.check_ae350(chipdb_path, evidence_dir)
    assert (satisfied, total) == (4, 4), lines
    assert exit_code == 0
