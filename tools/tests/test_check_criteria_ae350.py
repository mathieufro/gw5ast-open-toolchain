"""Tests for `check_criteria.py --ae350` (`V18`, `S19`'s non-hardware half).

`--ae350` is a separate mode: it takes `--chipdb`/`--evidence` instead of the
positional `spec_primitives`/`evidence_dir`, and every one of its four checks
is decided from the chipdb, from `gowin_pack`, or from a machine-readable
field. No check may pass because a document contains a sentence -- these tests
are what pins that, so each one has a companion showing the shape it refuses.
"""
import json
import os
import sys
import types

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import pytest

import check_criteria as cc  # noqa: E402

ANCHOR = cc.AE350_ANCHOR_TILE               # (0, 159)
CORE_CLK_TAP = cc.AE350_CORE_CLK_FABRIC_TAP  # (0, 87, "CLK1")
DEDICATED = "AE350_SOC_CORE_CLK"
PLL_WIRES = {"PLL_L[0]": [27, 1, "MPLLCLKOUT1"],
             "PLL_R[0]": [27, 177, "MPLLCLKOUT1"]}


class FakeTile:
    def __init__(self, pips):
        self.pips = pips


class FakeDevice:
    """The `Device` attributes `--ae350`'s checks actually read."""

    def __init__(self, extra_func=None, nodes=None, pips=None):
        self.extra_func = extra_func or {}
        self.nodes = nodes or {}
        self.grid = [[0] * (ANCHOR[1] + 1)]
        self.tiles = {0: FakeTile(pips if pips is not None else {})}


def _edge(sites=PLL_WIRES, fuses=frozenset()):
    sources = {site: {"alias": f"AE350_CORE_CLK_{site[:5].replace('_', '')}0",
                      "pll_wire": wire}
               for site, wire in sites.items()}
    return {"wire": DEDICATED, "routable": False, "sources": sources,
            "fabric_tap": [1, 88, 125]}, fuses


def _device_with_edge(sites=PLL_WIRES, fuses=frozenset(), bind_fabric=False,
                      bound_wire=DEDICATED):
    edge, fuse_set = _edge(sites, fuses)
    nodes = {}
    for site, source in edge["sources"].items():
        prow, pcol, pwire = source["pll_wire"]
        nodes[f"X159Y0/{source['alias']}"] = (
            "PLL_O", {(ANCHOR[0], ANCHOR[1], source["alias"]),
                      (prow, pcol, pwire)})
    if bind_fabric:
        nodes["X159Y0/AE350_SOCCORE_CLKCLK1"] = (
            "TILE_CLK", {(ANCHOR[0], ANCHOR[1], DEDICATED), CORE_CLK_TAP})
    pips = {DEDICATED: {s["alias"]: set(fuse_set) for s in edge["sources"].values()}}
    return FakeDevice(
        extra_func={ANCHOR: {"ae350": {"ins": {"CORE_CLK": bound_wire,
                                               "P0": "W0"},
                                       "outs": {"P1": "W1"},
                                       "core_clk": edge}}},
        nodes=nodes, pips=pips)


def _write_evidence(tmp_path, verdict_line="RECONCILIATION-VERDICT: 0/3 wires covered",
                    counts=None):
    ae350 = tmp_path / "evidence" / "ae350"
    ae350.mkdir(parents=True)
    if verdict_line is not None:
        (ae350 / "reconciliation.md").write_text(verdict_line, encoding="utf-8")
    counts = counts if counts is not None else {"McuIns": 265, "McuOuts": 372,
                                                "total": 637}
    (ae350 / "mcu-tables.json").write_text(json.dumps({"counts": counts}),
                                           encoding="utf-8")
    return str(tmp_path / "evidence")


# --------------------------------------------------------------------------
# 1. bel exists
# --------------------------------------------------------------------------
def test_bel_exists_when_extra_func_is_populated_at_the_anchor():
    ok, detail = cc.check_ae350_bel_exists(_device_with_edge())
    assert ok and str(ANCHOR) in detail


def test_bel_missing_when_extra_func_has_no_ae350_entry():
    assert not cc.check_ae350_bel_exists(FakeDevice())[0]


def test_bel_missing_when_ins_or_outs_is_empty():
    db = FakeDevice(extra_func={ANCHOR: {"ae350": {"ins": {}, "outs": {"P": "W"}}}})
    assert not cc.check_ae350_bel_exists(db)[0]


# --------------------------------------------------------------------------
# 2. CORE_CLK is a fixed connection, decided from the chipdb alone
# --------------------------------------------------------------------------
def test_core_clk_ok_with_one_fuseless_hop_per_pll_site():
    ok, detail = cc.check_ae350_core_clk_nonroutable(_device_with_edge())
    assert ok, detail
    assert "PLL_L[0]" in detail and "PLL_R[0]" in detail


def test_core_clk_fails_when_the_chipdb_models_no_dedicated_edge():
    db = FakeDevice(extra_func={ANCHOR: {"ae350": {"ins": {"CORE_CLK": "W"},
                                                   "outs": {}}}})
    ok, detail = cc.check_ae350_core_clk_nonroutable(db)
    assert not ok and "no dedicated" in detail


def test_core_clk_fails_when_the_port_is_bound_to_the_fabric_tap():
    """The shape this check exists to refuse: an ordinary routable tap."""
    ok, detail = cc.check_ae350_core_clk_nonroutable(
        _device_with_edge(bound_wire="AE350_SOCCORE_CLKCLK1"))
    assert not ok and "dedicated wire" in detail


def test_core_clk_fails_when_only_one_pll_site_has_the_edge():
    sites = {"PLL_R[0]": PLL_WIRES["PLL_R[0]"]}
    ok, detail = cc.check_ae350_core_clk_nonroutable(_device_with_edge(sites))
    assert not ok and "PLL_L[0]" in detail


def test_core_clk_fails_when_the_hop_costs_a_fuse():
    """A connection that costs a bit is configured, not fixed."""
    ok, detail = cc.check_ae350_core_clk_nonroutable(
        _device_with_edge(fuses=frozenset({(10, 3)})))
    assert not ok and "costs" in detail


def test_core_clk_fails_when_the_port_still_reaches_the_fabric_tap():
    ok, detail = cc.check_ae350_core_clk_nonroutable(
        _device_with_edge(bind_fabric=True))
    assert not ok and "fabric tap" in detail


# --------------------------------------------------------------------------
# 3. fuse set, read from the packer
# --------------------------------------------------------------------------
def test_fuse_set_reads_the_packer_not_a_document(monkeypatch):
    ok, detail = cc.check_ae350_fuse_set(_device_with_edge())
    assert ok
    assert "get_AE350_SOC_fuses" in detail


def test_fuse_set_reports_the_count_when_the_packer_emits_a_set(monkeypatch):
    from apycula import gowin_pack

    cell = types.SimpleNamespace(x=156, y=10, bits={(10, 24), (10, 31)})
    monkeypatch.setattr(gowin_pack.GW5AST_138C, "get_AE350_SOC_fuses",
                        lambda self, bel: [cell])
    ok, detail = cc.check_ae350_fuse_set(_device_with_edge())
    assert ok and "2 bits over 1 tiles" in detail


# --------------------------------------------------------------------------
# 4. reconciliation, cross-checked against the live map
# --------------------------------------------------------------------------
def test_reconciliation_ok_when_the_verdict_line_matches_the_chipdb(tmp_path):
    ok, detail = cc.check_ae350_reconciliation(
        _device_with_edge(), _write_evidence(tmp_path))
    assert ok, detail
    assert "0/3" in detail


def test_reconciliation_fails_when_the_denominator_is_not_the_live_map(tmp_path):
    """The check the substring `637` could never make."""
    ok, detail = cc.check_ae350_reconciliation(
        _device_with_edge(),
        _write_evidence(tmp_path, "RECONCILIATION-VERDICT: 0/911 wires covered"))
    assert not ok and "chipdb carries 3 port bits" in detail


def test_reconciliation_fails_without_a_verdict_line(tmp_path):
    ok, detail = cc.check_ae350_reconciliation(
        _device_with_edge(),
        _write_evidence(tmp_path, "the 637 entries were reconciled"))
    assert not ok and "RECONCILIATION-VERDICT" in detail


def test_reconciliation_fails_when_the_file_is_absent(tmp_path):
    ok, detail = cc.check_ae350_reconciliation(
        _device_with_edge(), _write_evidence(tmp_path, None))
    assert not ok and "absent" in detail


def test_reconciliation_fails_when_the_table_counts_disagree(tmp_path):
    ok, detail = cc.check_ae350_reconciliation(
        _device_with_edge(),
        _write_evidence(tmp_path, counts={"McuIns": 265, "McuOuts": 372,
                                          "total": 600}))
    assert not ok and "inconsistent" in detail


# --------------------------------------------------------------------------
# 5. aggregation and CLI wiring
# --------------------------------------------------------------------------
def _fake_chipdb_file(tmp_path, name="fake.msgpack.xz"):
    path = tmp_path / name
    path.write_bytes(b"")
    return str(path)


def _with_loader(monkeypatch, db):
    monkeypatch.setattr(cc, "_import_apycula_chipdb",
                        lambda: types.SimpleNamespace(load_chipdb=lambda _p: db))


def test_check_ae350_reports_4_of_4_when_everything_is_structural(tmp_path, monkeypatch):
    _with_loader(monkeypatch, _device_with_edge())
    satisfied, total, exit_code, lines = cc.check_ae350(
        _fake_chipdb_file(tmp_path), _write_evidence(tmp_path))
    assert (satisfied, total, exit_code) == (4, 4, 0), lines


def test_check_ae350_fails_and_names_the_broken_check(tmp_path, monkeypatch):
    _with_loader(monkeypatch, _device_with_edge(bind_fabric=True))
    satisfied, total, exit_code, lines = cc.check_ae350(
        _fake_chipdb_file(tmp_path), _write_evidence(tmp_path))
    assert (satisfied, total, exit_code) == (3, 4, 1)
    assert any("CORE_CLK non-routable" in l and "AE350 FAIL" in l for l in lines)


def test_check_ae350_fails_cleanly_when_chipdb_path_does_not_exist(tmp_path):
    satisfied, total, exit_code, lines = cc.check_ae350(
        str(tmp_path / "nope.msgpack.xz"), _write_evidence(tmp_path))
    assert exit_code == 1 and satisfied == 0 and total == 4
    assert all("chipdb not found" in l for l in lines)


def test_cli_ae350_flag_does_not_require_the_positional_arguments(tmp_path, capsys):
    exit_code = cc.main(["--ae350", "--chipdb", str(tmp_path / "missing.msgpack.xz"),
                         "--evidence", _write_evidence(tmp_path)])
    assert "AE350 ok:" in capsys.readouterr().out
    assert exit_code in (0, 1)


# --------------------------------------------------------------------------
# 6. end to end, against the real installed chipdb and evidence tree
# --------------------------------------------------------------------------
def test_ae350_ok_4_of_4_against_the_real_chipdb_and_evidence():
    chipdb_path = os.path.abspath(os.path.join(
        os.path.dirname(TOOLS_DIR), "..", "apicula", "apycula",
        "GW5AST-138C.msgpack.xz"))
    evidence_dir = os.path.abspath(os.path.join(TOOLS_DIR, "..", "evidence"))
    if not os.path.isfile(chipdb_path):
        pytest.skip(f"{chipdb_path} is absent; run `make apycula/GW5AST-138C.msgpack.xz`")
    satisfied, total, exit_code, lines = cc.check_ae350(chipdb_path, evidence_dir)
    assert (satisfied, total, exit_code) == (4, 4, 0), lines
