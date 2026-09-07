"""Tests for the ``P2.T26`` re-scope artefacts.

One test per artefact: the wire map (``wire-map-138c.json`` and its prose
companion) and the re-scoped task plan (``rescope.md``).  Each asserts the
property the artefact exists to carry, not its wording.
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


def load_map():
    if not MAP_JSON.is_file():
        pytest.fail(f"{MAP_JSON} is missing")
    return json.loads(MAP_JSON.read_text())


def test_wire_map_accounts_for_every_port_bit():
    """Resolved plus unresolved bits equal the measured port-bit total.

    The arithmetic identity that fails if a bus is silently dropped.
    """
    doc = load_map()
    assert doc["ports"]["bits"] == PORT_BITS
    assert doc["ports"]["input_bits"] + doc["ports"]["output_bits"] == PORT_BITS
    assert doc["resolved_port_bits"] + doc["unresolved_port_bits"] == PORT_BITS


def test_wire_map_footprint_is_measured_and_cites_its_runs():
    """The footprint is device data derived from named vendor runs."""
    doc = load_map()
    assert doc["provenance"] == "MEASURED"
    assert doc["device"] == "GW5AST-138C"
    runs = doc["runs"]
    assert runs, "a MEASURED footprint must name the runs it came from"
    ledger = BUDGET.read_text().splitlines()
    recorded = {line.split("\t")[0] for line in ledger[1:] if line.strip()}
    assert set(runs) <= recorded, f"runs {set(runs) - recorded} are not in {BUDGET}"
    fp = doc["placement"]["fabric_footprint"]
    assert fp["col_min"] < fp["col_max"]
    assert fp["moved_bits_in_band"] <= fp["moved_bits_total"]
    assert fp["fraction_in_band"] > 0.99, "a footprint that is not concentrated is not a footprint"


def test_wire_map_names_its_unresolved_classes_and_carries_one_verdict():
    """An incomplete map states what is missing; it is never a blank row."""
    doc = load_map()
    if doc["unresolved_port_bits"]:
        assert doc["status"] == "PARTIAL"
        assert doc["unresolved_classes"], "unresolved bits with no named class is a blank row"
    verdicts = [ln for ln in MAP_MD.read_text().splitlines()
                if ln.startswith("WIRE-MAP-VERDICT: ")]
    assert len(verdicts) == 1


def test_rescope_carries_one_verdict_and_a_budget_inside_the_cap():
    """The re-scope states a single verdict and does not overrun the cap."""
    text = RESCOPE.read_text()
    verdicts = [ln for ln in text.splitlines() if ln.startswith("RESCOPE-VERDICT: ")]
    assert len(verdicts) == 1, "exactly one RESCOPE-VERDICT line"
    spent = int(re.search(r"Runs used (\d+) of (\d+)", verdicts[0]).group(1))
    cap = int(re.search(r"Runs used (\d+) of (\d+)", verdicts[0]).group(2))
    assert cap == RUN_CAP
    rows = [ln.split("\t") for ln in BUDGET.read_text().splitlines()[1:] if ln.strip()]
    assert sum(int(r[2]) for r in rows) == spent, "the verdict's run count must match the ledger"
    assert spent <= cap


def test_rescope_disposes_of_every_task_the_reconciliation_routed_to_ec5():
    """`P2.T37` was the whole of the EC5 route; the re-scope must rule on it."""
    text = RESCOPE.read_text()
    for task in ("P2.T07", "P2.T08", "P2.T37"):
        assert re.search(rf"\|\s*\**`?{re.escape(task)}`?", text), f"{task} is not disposed of"
    assert "VOID" in text, "P2.T37's premise is superseded and the plan must say so"
