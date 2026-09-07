"""Tests for the `P3.T07`/`P3.T08` pin -> HCLK evidence rows.

One test per property the row set exists to carry: that every candidate ball
was run, that the HCLK landing came out of a decode rather than a report, that
the two controls disagree with the unpinned sweep, and that the reason the row
stops at `E0` is written down on every row rather than left to a summary.
"""

import json
from pathlib import Path

import pytest

ROWS = (Path(__file__).resolve().parents[2] / "evidence" / "pin-to-hclk"
        / "runs.jsonl")

#: The twelve balls `io_basic.CLOCK_CANDIDATES` names, over four banks.
CANDIDATES = {"V22", "V19", "W20", "P20", "N15", "F20", "D21", "F21",
              "Y17", "W14", "AA9", "G15"}


@pytest.fixture(scope="module")
def rows():
    if not ROWS.is_file():
        pytest.skip(f"{ROWS} not written yet")
    return [json.loads(line) for line in ROWS.read_text().splitlines() if line]


def test_pin_to_hclk_every_candidate_ball_has_a_row(rows):
    """The row's done criterion is the enumerated set, so a ball with no row
    is a hole in the answer, not a smaller answer."""
    swept = {r["sweep"]["clk_ball"] for r in rows
             if r["sweep"]["step"].startswith("sweep-")}
    assert swept == CANDIDATES


def test_pin_to_hclk_rows_are_vendor_measurements(rows):
    """Every row names the device and the vendor log it was decoded from."""
    assert len(rows) == 14
    for row in rows:
        assert row["device"] == "GW5AST-138C", row["run_id"]
        assert row["oracle_log"], row["run_id"]
        assert Path(row["oracle_log"]).is_file(), row["run_id"]


def test_pin_to_hclk_every_ball_reaches_the_hclk_network(rows):
    """`reaches_fclk` is the sweep's verdict column and must be backed by a
    decoded block, lane and entry wire -- never set on its own."""
    reached = [r for r in rows if r["sweep"]["reaches_fclk"]]
    assert len(reached) == len(rows)
    for row in reached:
        sweep = row["sweep"]
        assert sweep["hclk_block"] in range(6), row["run_id"]
        assert sweep["hclk_lane"] in range(4), row["run_id"]
        assert sweep["hclk_entry_wire"] == "L2HCLK%d%d" % (
            sweep["hclk_block"], sweep["hclk_lane"]), row["run_id"]


def test_pin_to_hclk_controls_land_on_another_edge_than_the_sweep(rows):
    """The measurement that turns a placer preference into a property of the
    die: the same ball, pinned to a block on another edge, still routes."""
    by_step = {(r["sweep"]["step"], r["sweep"]["clk_ball"]): r for r in rows}
    for step, ball in (("ctl-v22-rightside", "V22"),
                       ("ctl-f20-bottomside", "F20")):
        control = by_step[(step, ball)]
        free = next(r for r in rows
                    if r["sweep"]["clk_ball"] == ball
                    and r["sweep"]["step"].startswith("sweep-"))
        assert control["sweep"]["ins_loc"], step
        assert control["sweep"]["hclk_block"] != free["sweep"]["hclk_block"]


def test_pin_to_hclk_iologic_is_an_ides4_on_its_own_fclk_wire(rows):
    """The IOLOGIC half of the claim: the probe's gearbox is realised and its
    fast clock is bound to the tile's own FCLK wire."""
    seen = 0
    for row in rows:
        for cell in row["sweep"].get("iologic") or ():
            assert cell["mode"] == "IDES4", row["run_id"]
            assert cell["fclk"].endswith("_FCLK"), row["run_id"]
            seen += 1
    assert seen >= 5


def test_pin_to_hclk_rows_say_why_they_stop_at_e0(rows):
    """`EC9`: a row that cannot reach `E1` records the reason on itself, so a
    reader of one row never has to find a summary to know what it is not."""
    for row in rows:
        assert row["level"] == "E0", row["run_id"]
        assert "io2hclk" in row["notes"], row["run_id"]
        assert row["open_fs"] == [], row["run_id"]
