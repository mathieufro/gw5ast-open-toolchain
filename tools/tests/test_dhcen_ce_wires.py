"""`P1.T25` -- the 138C DHCEN control-pin (`CE`) wire table.

Asserts the **committed** artefacts (`evidence/dhcen/ce-wires-138c.json` and
`ce-wires-138c.md`), not a throwaway fixture, and needs no `GOWINHOME`: the
table was measured once by `evidence/dhcen/probe_dhce.py` against the licensed
vendor oracle, and what the gate re-checks on every run is that the recorded
table still says what `P1.T26` is entitled to read.

Two blueprint deviations are asserted here on purpose (standing order: measure,
then record the refutation rather than assert the guess).

1. **The primitive is not called `DHCEN` on this family.** `P1.T25` speaks of
   `DHCEN` because that is apicula's name for it. Measured: GowinSynthesis
   refuses `DHCEN` on `GW5AST-138C` with ``ERROR (EX3937) : Instantiating
   unknown module 'DHCEN'``; the vendor's own GW5A primitive table
   (`IDE/bin/prim_syns/gw5a/primitive.xml`) spells it **`DHCE`** with the
   enable port **`CEN`**, and the `DHCEN` IP spec lists no `GW5*` device at
   all. Every run in this campaign therefore instantiates `DHCE`.
2. **The table is not `4 sides x 6 entries`.** The blueprint's shape comes from
   the GW1N/GW2A devices, which have one HCLK block per side. The 138C has
   **six** HCLK blocks and **no top-edge block** (`P1.T04`), and the vendor
   states the capacity as `DHCE n/24` in its own `Clock Resource Usage
   Summary`. The artefact is asserted against the measured grouping, and the
   total is asserted to be the vendor-stated capacity.
"""
import json
import os
import re

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC_ROOT = os.path.dirname(TOOLS_DIR)
DHCEN_DIR = os.path.join(OTC_ROOT, "evidence", "dhcen")
WIRES_JSON = os.path.join(DHCEN_DIR, "ce-wires-138c.json")
WIRES_MD = os.path.join(DHCEN_DIR, "ce-wires-138c.md")
TRACE_MD = os.path.join(DHCEN_DIR, "trace-138c.md")

#: Measured grid of the GW5AST-138C (`P1.T04`): 109 rows x 182 columns.
GRID_ROWS = 109
GRID_COLS = 182

#: The six measured HCLK block cells (`P1.T04`), 0-based `(row, col)`.
HCLK_CELLS = [(27, 0), (27, 181), (81, 0), (81, 181), (108, 64), (108, 117)]

#: Vendor-stated DHCE capacity, read from `Clock Resource Usage Summary`.
DHCE_CAPACITY = 24


def _load():
    assert os.path.isfile(WIRES_JSON), f"missing artefact: {WIRES_JSON}"
    with open(WIRES_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def test_dhcen_ce_wires_artifact_shape():
    """The recorded table has the measured shape and no duplicate entry."""
    doc = _load()
    entries = doc["entries"]
    assert doc["device"] == "GW5AST-138C"
    assert doc["primitive"] == "DHCE", "the GW5A spelling of apicula's DHCEN"
    assert doc["enable_port"] == "CEN"
    assert doc["capacity"] == DHCE_CAPACITY

    assert len(entries) == DHCE_CAPACITY, (
        f"the vendor states DHCE {DHCE_CAPACITY} sites; the table has "
        f"{len(entries)}")

    triples = [(e["row"], e["col"], e["wire"]) for e in entries]
    assert len(set(triples)) == len(triples), "duplicate (row, col, wire)"

    for e in entries:
        assert 0 <= e["row"] < GRID_ROWS, e
        assert 0 <= e["col"] < GRID_COLS, e
        assert (e["row"], e["col"]) in HCLK_CELLS, (
            f"{e} is not in a measured HCLK block cell")
        assert e["side"] in {"L", "R", "B", "T"}, e
        assert isinstance(e["idx"], int) and 0 <= e["idx"] < 6, e


def test_dhcen_ce_wires_resolve_in_wirenames():
    """Every recorded wire name resolves in the device's wire-name tables."""
    from apycula import wirenames as wn
    doc = _load()
    known = set()
    for table in ("wirenames_5ast138c", "clknames_5ast138c",
                  "hclknames_5ast138c", "wirenames", "clknames", "hclknames"):
        t = getattr(wn, table, None)
        if isinstance(t, dict):
            known |= {v for v in t.values() if isinstance(v, str)}
            known |= {k for k in t if isinstance(k, str)}
        elif isinstance(t, (list, tuple)):
            known |= {v for v in t if isinstance(v, str)}
    missing = sorted({e["wire"] for e in doc["entries"]} - known)
    assert not missing, f"wire names not in any wire-name table: {missing}"


def test_dhcen_ce_wires_grouping_matches_blocks():
    """Each HCLK block that carries entries carries the same number of them."""
    doc = _load()
    per_block = {}
    for e in doc["entries"]:
        per_block.setdefault((e["row"], e["col"]), []).append(e)
    counts = sorted({len(v) for v in per_block.values()})
    assert len(counts) == 1, f"uneven entries per block: {counts}"
    assert len(per_block) * counts[0] == DHCE_CAPACITY
    for block, es in per_block.items():
        idxs = sorted(e["idx"] for e in es)
        assert idxs == list(range(len(es))), f"{block}: non-contiguous idx {idxs}"


def test_dhcen_artifacts_record_the_deviations():
    """The prose artefacts state the two refutations, not just the numbers."""
    for path in (WIRES_MD, TRACE_MD):
        assert os.path.isfile(path), f"missing artefact: {path}"
        text = open(path, encoding="utf-8").read()
        assert "EX3937" in text, f"{path} must record the DHCEN refusal"
        assert "DHCE" in text and "CEN" in text
        assert re.search(r"\bDHCE\s*\|?\s*[0-9]+/24\b|DHCE\s+n?/?24|24\b", text)
