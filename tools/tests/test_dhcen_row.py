"""`P1.T27` -- the `evidence/dhcen/` row closes on the DHCE gate.

The blueprint asks for "exactly 6 rows" in `evidence/dhcen/runs.jsonl`. That
was written before `P1.T25` measured the control-pin table into the same file:
the slug already holds 28 tracing rows and 4 fuse-attribution rows, and
deleting them to satisfy a count would destroy the evidence the model rests
on. What is asserted instead is the same claim scoped to the task that makes
it -- the `clocking_dhce` rows, one per lane of the swept block.

Two further deviations, both measured (`evidence/dhcen/lane-138c.md`):

* the sweep is **one block x four lanes**, not six `(block, lane)` points. A
  `ShapeSpec` carries one static tile scope, and a scope holding both bottom
  blocks puts the `CEN` net's long-wire hops through the *other* block inside
  the comparison, where they are a route of a net the vendor has no
  endpoint-identical twin for. The cross-block half is measured vendor-side
  instead (`gate_probe.py`, block 4 lanes 0 and 2);
* **lane 3 is `aborted`, and that is the deliverable.** Its logic->HCLK entry
  is the fabric wire `LSR2` -- the vendor's own bitstream enters lane 3 over
  fabric too -- and `route_dhcen_net` refuses a DHCE-managed net that is not
  global end to end. The same design without the `DHCE` routes and packs, so
  the row records nextpnr policy, not a hole in the model.
"""
import json
import os
import re

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC_ROOT = os.path.dirname(TOOLS_DIR)
DHCEN_DIR = os.path.join(OTC_ROOT, "evidence", "dhcen")
RUNS = os.path.join(DHCEN_DIR, "runs.jsonl")
SUMMARY = os.path.join(DHCEN_DIR, "summary.md")
TABLE = os.path.join(OTC_ROOT, "evidence", "evidence-table.md")

#: The shape `P1.T27` runs, the four lanes it sweeps, and the one lane the
#: open flow cannot reach.
SHAPE = "clocking_dhce"
POINTS = {"b5l0", "b5l1", "b5l2", "b5l3"}
GLOBAL_ONLY_GAP = {"b5l3"}

#: UG306E p.19 names three consumers a DHCE may gate; the summary has to say
#: which of them this row does and does not speak for.
UG306E_CONSUMERS = ("DQS", "CLKDIV", "DDRDLL")

#: The `$PIPE` status cell this row sets, when the pipeline tree is reachable.
PIPE = os.environ.get(
    "PIPE",
    "/Users/alex/fine-line/.atelier/pipelines/"
    "2026-09-03-open-toolchain-gw5ast-7e84")
STATUS_RE = re.compile(r"^(E1|E0\+hw-pending|refused:.+)$")


def _rows():
    with open(RUNS) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_dhcen_row_closes():
    rows = [r for r in _rows() if r.get("shape") == SHAPE]
    assert len(rows) == 4, f"{len(rows)} {SHAPE} rows, expected 4"
    assert {r["sweep"]["site"] for r in rows} == POINTS
    for r in rows:
        rid = r["run_id"]
        if r["sweep"]["site"] in GLOBAL_ONLY_GAP:
            assert r["verdict"] == "aborted", f"{rid}: lane 3 is the gap"
            continue
        assert r["verdict"] == "ok", f"{rid}: verdict {r['verdict']}"
        assert r["level"] == "E1", f"{rid}: level {r['level']}"
        assert r["primitive"] == "DHCE", f"{rid}: primitive {r['primitive']}"
        for term in ("cells", "attrs", "conns"):
            assert r["diff_count"][term] == 0, f"{rid}: {term} differs"
        assert r["unexplained_bits"] == [], f"{rid}: unexplained bits"
        assert r["decode_check"] == {"c1": "ok", "c2": "ok"}, rid

    text = open(SUMMARY).read()
    assert len(text.splitlines()) <= 200, "summary.md is over 200 lines"
    assert "lane-138c.md" in text or "P1.T27" in text
    for consumer in UG306E_CONSUMERS:
        assert consumer in text, f"summary.md does not name {consumer}"

    assert "dhcen" in open(TABLE).read()

    primitives = os.path.join(PIPE, "spec-primitives.md")
    if os.path.isfile(primitives):
        for line in open(primitives).read().splitlines():
            if line.startswith("| **DHCE**"):
                cell = line.split("|")[3].strip().strip("`")
                assert STATUS_RE.match(cell), f"status cell {cell!r}"
                break
        else:
            raise AssertionError("no DHCE row in spec-primitives.md")
