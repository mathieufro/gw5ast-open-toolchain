"""Tests for the `P3.T06` pin -> bank -> HCLK-block table.

One test per property the artefact exists to carry: that every row says how it
was derived, that nothing unmeasured leaks into the chipdb-consumable list,
that the geometry closes against the `P1.T04` topology, and that the DDR banks
are flagged wherever they appear.
"""

import json
from pathlib import Path

import pytest

ARTEFACT = (Path(__file__).resolve().parents[2] / "evidence" / "iologic"
            / "pin-hclk-138c.json")

#: The 138C has I/O on three die edges only -- the `.dat`'s `TA`/`TB` bank
#: columns are `-1` for all 184 entries (`P3.T06`).
SIDES = {"L", "R", "B"}

#: MEASURED by `P1.T04` (`evidence/hclk/topology-138c.md`).
BLOCK_CELLS = {0: (27, 0), 1: (27, 181), 2: (81, 0), 3: (81, 181),
               4: (108, 64), 5: (108, 117)}


@pytest.fixture(scope="module")
def table():
    if not ARTEFACT.is_file():
        pytest.skip(f"{ARTEFACT} not generated yet")
    return json.loads(ARTEFACT.read_text())


def test_pin_hclk_every_pin_marks_its_derivation(table):
    """No cell of the table is silently sourced."""
    allowed = {"DAT-DERIVED", "FSE-DERIVED", "MEASURED",
               "MEASURED_NOT_PIN_DETERMINED"}
    expected = {"bank", "cell", "iologic", "hclk_block", "hclk_lanes"}
    for pin in table["pins"]:
        assert set(pin["derived"]) == expected, pin["site"]
        assert set(pin["derived"].values()) <= allowed, pin["site"]


def test_pin_hclk_block_is_measured_only_where_a_run_measured_it(table):
    """`P3.T07` refuted the nearest-block hypothesis: a ball does not decide
    the block. A pin therefore carries a block only if a named run put it
    there, and every other pin says so instead of carrying a guess."""
    assert table["block_rule"] == "MEASURED_NOT_PIN_DETERMINED"
    measured = table["measured_pin_to_hclk"]["balls"]
    for pin in table["pins"]:
        if pin["ball"] in measured:
            assert pin["derived"]["hclk_block"] == "MEASURED", pin["site"]
            assert pin["hclk_block"] == measured[pin["ball"]]["hclk_block"]
            assert pin["hclk_lanes"] == [measured[pin["ball"]]["hclk_lane"]]
            assert pin["hclk_run_id"] == measured[pin["ball"]]["run_id"]
        else:
            assert pin["hclk_block"] is None, pin["site"]
            assert pin["hclk_lanes"] is None, pin["site"]
            assert pin["hclk_block_source"].startswith("NOT_PIN_DETERMINED")


def test_pin_hclk_every_measured_ball_entered_on_the_logic_entry_wire(table):
    """The one finding the whole row turns on: no candidate used a dedicated
    pin -> HCLK edge, so `pin_to_hclk_entries` must stay empty."""
    measured = table["measured_pin_to_hclk"]["balls"]
    assert len(measured) == 12
    for ball, entry in measured.items():
        assert entry["entry_wire"] == "L2HCLK%d%d" % (entry["hclk_block"],
                                                      entry["hclk_lane"]), ball


def test_pin_hclk_controls_move_a_ball_to_another_edge(table):
    """A block a ball landed on unpinned proves nothing on its own; the
    controls are what make the "not pin-determined" claim a measurement."""
    controls = table["measured_pin_to_hclk"]["controls"]
    balls = table["measured_pin_to_hclk"]["balls"]
    assert set(controls) == {"V22", "F20"}
    for ball, control in controls.items():
        assert control["hclk_block"] != balls[ball]["hclk_block"], ball


def test_pin_hclk_chipdb_entries_are_empty_until_measured(table):
    """`pin_to_hclk_entries` feeds the routing graph, so it takes measured
    entries only -- and none exist yet."""
    assert table["pin_to_hclk_entries"] == []


def test_pin_hclk_bank_is_dat_derived_for_every_pin(table):
    """The bank column is the one the safety envelope rests on."""
    assert table["pins"], "artefact has no pins"
    for pin in table["pins"]:
        assert pin["derived"]["bank"] == "DAT-DERIVED", pin["site"]
        assert isinstance(pin["bank"], int) and pin["bank"] >= 0, pin["site"]


def test_pin_hclk_cells_lie_on_the_die_edge_of_their_side(table):
    """A site name's letter and its `(row, col)` must agree, or the `.dat`
    bank column was read with the wrong index."""
    rows, cols = table["grid"]["rows"], table["grid"]["cols"]
    for pin in table["pins"]:
        assert pin["side"] in SIDES, pin["site"]
        if pin["side"] == "L":
            assert pin["col"] == 0, pin["site"]
        elif pin["side"] == "R":
            assert pin["col"] == cols - 1, pin["site"]
        else:
            assert pin["row"] == rows - 1, pin["site"]


def test_pin_hclk_blocks_match_the_p1t04_topology(table):
    """The block list is `P1.T04`'s measurement, not a second opinion."""
    got = {b["hclk_idx"]: (b["row"], b["col"]) for b in table["hclk_blocks"]}
    assert got == BLOCK_CELLS


def test_pin_hclk_nearest_block_geometry_still_closes(table):
    """The nearest-block column survives as geometry, not as a claim about
    clocks: every pin still has one, on its own die edge."""
    side_of_block = {b["hclk_idx"]: b["side"] for b in table["hclk_blocks"]}
    expect = {"L": "left", "R": "right", "B": "bottom"}
    for pin in table["pins"]:
        nearest = pin["nearest_block_on_side"]
        assert nearest is not None, pin["site"]
        assert side_of_block[nearest] == expect[pin["side"]], pin["site"]


def test_pin_hclk_ddr_bank_pins_are_flagged(table):
    """`ddr_bank` is what a shape's safety check reads, so it must equal
    membership of the declared DDR bank set on every row."""
    ddr = set(table["ddr_banks"])
    assert ddr == {6, 7}
    for pin in table["pins"]:
        assert pin["ddr_bank"] == (pin["bank"] in ddr), pin["site"]


def test_pin_hclk_no_bank_is_split_across_two_blocks(table):
    """The corroboration that would have failed on a wrong `BLOCK_RULE`:
    the vendor lays a bank out along one die edge, so a bank whose pins land
    on two different blocks means the rule cut the edge in the wrong place."""
    assert table["corroboration"]["banks_split_across_blocks"] == []
    assert set(table["corroboration"]["bank_to_block"]) == {
        str(pin["bank"]) for pin in table["pins"]}


def test_pin_hclk_clock_balls_sit_beside_their_block(table):
    """The dedicated `SGCLK`/`MGCLK` balls are placed by the die layout, not by
    `BLOCK_RULE`, so their distance to the assigned block is an outside
    opinion on it -- they cluster around the block cell, never across the
    die."""
    corroboration = table["corroboration"]
    assert corroboration["clock_ball_count"] > 0
    assert corroboration["clock_ball_max_cells_from_its_block"] <= 8
