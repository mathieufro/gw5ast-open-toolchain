"""Tests for the ``P2.T26``/``P2.T08a``/``P2.T08b`` wire-map artefacts.

One test per property the artefacts exist to carry -- the arithmetic that fails
if a bus is dropped, the geometry that fails if a table is misread, and the
run-ledger identity -- never their wording.
"""

import json
import re
from pathlib import Path

import pytest

EVIDENCE = Path(__file__).resolve().parents[2] / "evidence" / "ae350"
BUDGET = Path(__file__).resolve().parents[2] / "evidence" / "_budget" / "ae350-runs.tsv"
MAP_JSON = EVIDENCE / "wire-map-138c.json"
MAP_MD = EVIDENCE / "wire-map-138c.md"
RESCOPE = EVIDENCE / "rescope.md"

#: The cap ``P2.T37`` sets on this line of work.
RUN_CAP = 8
#: Port bit total, measured four independent ways by ``P2.T02``.
PORT_BITS = 911
#: Per direction, from the same inventory.
DIRECTION_BITS = {"Ae350SocIns": 416, "Ae350SocOuts": 495}


def load_map():
    if not MAP_JSON.is_file():
        pytest.fail(f"{MAP_JSON} is missing")
    return json.loads(MAP_JSON.read_text())


def test_wire_map_accounts_for_every_port_bit():
    """Every declared bit of every declared bus appears exactly once."""
    bits = load_map()["bits"]
    assert sum(len(v) for v in bits.values()) == PORT_BITS
    for table, expected in DIRECTION_BITS.items():
        assert [b["bit"] for b in bits[table]] == list(range(expected))


def test_every_bit_is_either_placed_or_named_unbound():
    """A bit with no record is an explicit verdict, never a silent gap."""
    for table, entries in load_map()["bits"].items():
        for entry in entries:
            placed = entry["row"] is not None
            assert placed == (entry["provenance"] != "UNBOUND"), entry
            if placed:
                assert entry["col"] is not None and entry["wire"]


def test_input_taps_are_row_zero_wires_the_fabric_drives():
    """An input tap can only be an F, Q or OF wire of the block's own row."""
    for entry in load_map()["bits"]["Ae350SocIns"]:
        if entry["provenance"] == "UNBOUND":
            continue
        assert entry["row"] == 0
        assert re.fullmatch(r"(?:F|Q|OF)\d", entry["wire"]), entry


def test_no_two_bits_share_one_fabric_wire():
    """Two ports on one wire would be a misread table, not a port map."""
    for table, entries in load_map()["bits"].items():
        placed = [(e["row"], e["col"], e["wire"]) for e in entries
                  if e["provenance"] != "UNBOUND"]
        assert len(set(placed)) == len(placed), table


def test_input_taps_sit_inside_the_measured_footprint():
    """The map describes the block the vendor placed, not a neighbour of it.

    ``P2.T08a`` read the input table at a base whose columns fall outside the
    footprint; this is the assertion that caught it.
    """
    doc = load_map()
    low, high = doc["footprint_cols"]
    columns = {e["col"] for e in doc["bits"]["Ae350SocIns"]
               if e["provenance"] != "UNBOUND"}
    assert columns
    assert min(columns) >= low and max(columns) <= high


def test_the_map_cites_runs_the_budget_ledger_records():
    """Measured evidence names the vendor runs it came from."""
    doc = load_map()
    assert doc["device"] == "GW5AST-138C"
    recorded = {line.split("\t")[0]
                for line in BUDGET.read_text().splitlines()[1:] if line.strip()}
    assert doc["runs"] and set(doc["runs"]) <= recorded


def _rescope_verdicts():
    """Every `RESCOPE-VERDICT` entry, in file order, with its revision number.

    An entry is the whole paragraph, not its first line: a verdict wraps, and
    the run count usually lands on a continuation line.

    The re-scope is a ledger, not a snapshot: each task that changes the plan
    appends a numbered revision and the earlier ones stay as the record of
    what was believed when. What must not happen is two lines claiming the
    same revision, or a gap where one was dropped.
    """
    out = []
    lines = RESCOPE.read_text().splitlines()
    for start, line in enumerate(lines):
        if not line.startswith("RESCOPE-VERDICT"):
            continue
        end = start
        while end < len(lines) and lines[end].strip():
            end += 1
        paragraph = " ".join(lines[start:end])
        match = re.search(r"rev (\d+)", paragraph)
        assert match, f"a verdict with no revision number: {paragraph}"
        out.append((int(match.group(1)), paragraph))
    return out


def test_each_artefact_carries_exactly_one_verdict_line():
    """One artefact, one verdict; a second would be an unreduced review."""
    text = MAP_MD.read_text()
    for prefix in ("WIRE-MAP-VERDICT: ", "WIRE-MAP-T08B-VERDICT: "):
        assert sum(ln.startswith(prefix) for ln in text.splitlines()) == 1, prefix


def test_the_rescope_revisions_are_numbered_uniquely_and_without_a_gap():
    """The ledger reads forwards: one line per revision, none missing."""
    revs = [rev for rev, _line in _rescope_verdicts()]
    assert revs, "the re-scope carries no verdict at all"
    assert revs == sorted(set(revs)), f"repeated or out-of-order revisions: {revs}"
    assert revs == list(range(revs[0], revs[0] + len(revs))), f"a gap: {revs}"


def test_the_rescope_stays_inside_the_run_cap_the_ledger_records():
    """The current verdict's run count is the ledger's, and it is inside the cap.

    The *current* verdict is the last revision: an earlier one records the
    count as it stood then, and re-checking it against today's ledger would
    fail for the ordinary reason that more runs have since been spent.
    """
    verdict = _rescope_verdicts()[-1][1]
    spent, cap = (int(g) for g in re.search(r"Runs used (\d+) of (\d+)", verdict).groups())
    assert cap == RUN_CAP
    rows = [ln.split("\t") for ln in BUDGET.read_text().splitlines()[1:] if ln.strip()]
    assert sum(int(r[2]) for r in rows) == spent
    assert spent <= cap


def test_rescope_disposes_of_every_task_the_reconciliation_routed_to_ec5():
    """`P2.T37` was the whole of the EC5 route; the re-scope must rule on it."""
    text = RESCOPE.read_text()
    for task in ("P2.T07", "P2.T08", "P2.T08b", "P2.T37"):
        row = rf"^\|[^|\n]*`{re.escape(task)}`"
        assert re.search(row, text, re.M), f"{task} is not disposed of"
    assert "VOID" in text, "P2.T37's premise is superseded and the plan must say so"
