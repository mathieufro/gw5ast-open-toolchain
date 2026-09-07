"""Phase-2 (`AE350`) evidence-shape tests -- `P2.T01`-`P2.T04`.

These assert the committed evidence tree, not a fixture: the entry gate's
verdict lines and provenance block, the measured `AE350_SOC` port inventory,
the `McuIns`/`McuOuts` dump, and the wire-count reconciliation that joins the
last two. They are shape and arithmetic checks -- the measurements themselves
live in the evidence files, and re-deriving them here would only re-assert the
same numbers from the same source.
"""
import json
import os
import re

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC_ROOT = os.path.dirname(TOOLS_DIR)
AE350_DIR = os.path.join(OTC_ROOT, "evidence", "ae350")

PRECOND_RE = re.compile(r"^PRECOND ([1-7]) (ok|FAIL)$", re.M)
PROVENANCE_FIELDS = ("ide_version", "yosys_version", "apicula_sha",
                     "nextpnr_sha", "chipdb_sha256", "mask_sha256")


def _read(name):
    with open(os.path.join(AE350_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _read_json(name):
    with open(os.path.join(AE350_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


# --- P2.T01 ---------------------------------------------------------------

def test_entry_gate_records_seven_preconditions():
    text = _read("entry-gate.md")
    verdicts = PRECOND_RE.findall(text)
    assert len(verdicts) == 7
    assert [n for n, _ in verdicts] == [str(i) for i in range(1, 8)]
    assert [v for _, v in verdicts if v == "FAIL"] == []
    for field in PROVENANCE_FIELDS:
        match = re.search(rf"^{field}: (.+)$", text, re.M)
        assert match is not None, f"provenance field missing: {field}"
        assert match.group(1).strip(), f"provenance field empty: {field}"


# --- P2.T02 ---------------------------------------------------------------

CLOCKS = ("CORE_CLK", "DDR_CLK", "AHB_CLK", "APB_CLK", "RTC_CLK")
RESETS = ("POR_N", "HW_RSTN")


def test_ae350_port_inventory_xml_count_is_149():
    data = _read_json("port-inventory.json")
    assert data["counts"]["xml_ports"] == 149
    assert _read("port-inventory.md").splitlines()[0] == "PORTS 149"


def test_ae350_port_inventory_vo_and_xml_agree():
    data = _read_json("port-inventory.json")
    assert len(data["discrepancies"]) <= 2
    for entry in data["discrepancies"]:
        assert entry["source"], entry
        assert entry["reason"], entry
    assert data["counts"]["distinct_names"] >= 149


def test_ae350_port_inventory_has_five_clocks_two_resets():
    by_name = {p["name"]: p for p in _read_json("port-inventory.json")["ports"]}
    for name in CLOCKS + RESETS:
        assert name in by_name, name
        assert by_name[name]["width"] == 1, by_name[name]


# --- P2.T03 ---------------------------------------------------------------

def test_mcu_tables_counts_265_372():
    data = _read_json("mcu-tables.json")
    assert len(data["McuIns"]) == 265
    assert len(data["McuOuts"]) == 372
    assert data["counts"] == {"McuIns": 265, "McuOuts": 372, "total": 637}


def test_mcu_tables_sentinels_counted():
    data = _read_json("mcu-tables.json")
    sentinels = sum(1 for table in ("McuIns", "McuOuts")
                    for triple in data[table] if triple[0] < 0 or triple[1] < 0)
    assert sentinels == data["sentinels"]["count"]
    assert data["live_entries"] == 637 - sentinels
    assert data["live_entries"] <= 637


def test_mcu_tables_parser_validated_against_a_live_table():
    """An empty table is only evidence once the reader is shown to read."""
    validation = _read_json("mcu-tables.json")["parser_validation"]
    assert validation["GW1NS-4"]["EMcuIns"]["live"] > 0
    assert validation["GW1NS-4"]["EMcuOuts"]["live"] > 0


def test_ae350_port_inventory_four_sources_agree_on_149():
    """`F80`'s three disagreeing published counts, settled by measurement."""
    data = _read_json("port-inventory.json")
    counts = data["counts"]
    assert (counts["xml_ports"] == counts["vo_ports"]
            == counts["vo_demo_ports"] == counts["published_ports"] == 149)
    agreement = data["published_sources"]["agreement_with_primitive_xml"]
    assert agreement["only_published"] == []
    assert agreement["only_xml"] == []
    assert agreement["width_or_direction_differences"] == {}
    assert counts["xml_bits"] == 911


# --- P2.T04 ---------------------------------------------------------------

VERDICT_RE = re.compile(
    r"^RECONCILIATION-VERDICT: (\d+)/(\d+) wires covered; uncovered buses: (.*)$",
    re.M)
COVERAGE_ROW_RE = re.compile(r"^\| `([A-Z0-9_]+)` \| (\d+) \| (\S+) \| (\d+) \|$",
                             re.M)


def _verdict():
    text = _read("reconciliation.md")
    matches = VERDICT_RE.findall(text)
    assert len(matches) == 1, matches
    covered, needed, buses = matches[0]
    listed = [] if buses.strip() in ("", "none") else [
        b.strip() for b in buses.split(",")]
    return int(covered), int(needed), listed, COVERAGE_ROW_RE.findall(text)


def test_reconciliation_has_exactly_one_verdict_line():
    assert len(VERDICT_RE.findall(_read("reconciliation.md"))) == 1


def test_reconciliation_covered_plus_uncovered_equals_needed():
    covered, needed, uncovered, rows = _verdict()
    bits = {name: int(width) for name, width, _, _ in rows}
    assert covered == sum(int(c) for _, _, _, c in rows)
    assert covered + sum(bits[b] for b in uncovered) == needed


def test_reconciliation_needed_at_least_149():
    _, needed, _, _ = _verdict()
    assert needed >= 149
