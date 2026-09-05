"""`P1.T17` -- the 138C PLL-site enumeration artefacts.

Asserts the **committed** artefacts (`evidence/plla/sites-138c.md`,
`sites-138c.json`, `attrids-138c.tsv`), not a throwaway fixture, and needs no
`GOWINHOME`: the enumeration itself was measured once by
`evidence/plla/gen_sites_138c.py` against the shipped `.fse`/`.dat`, and what
the gate re-checks on every run is that the recorded table still says what
`P1.T18`/`P1.T19` are entitled to read.

Blueprint deviation recorded here on purpose (standing order: measure, then
record the refutation rather than assert the guess). `P1.T17` specifies
`5 <= count(source == "dat") <= 6`, on the premise that the 138C `.dat` names
5-6 of the 12 sites the way the 25A's does. **Measured: it names zero** -- all
eight `Pll{L,R}{T,B}{Ins,Outs}` tables of `GW5AST-138C.dat` are entirely
`0xffff`, while the same tables in `GW5A-25A.dat` carry 36/32 populated rows
each. The site positions come from the `.fse` instead (`source == "fse"`), so
the bound this file asserts is `count(dat) == 0` plus a positive assertion that
the artefact states the refutation. See `sites-138c.md` §6.
"""
import json
import os
import re

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC_ROOT = os.path.dirname(TOOLS_DIR)
PLLA_DIR = os.path.join(OTC_ROOT, "evidence", "plla")
SITES_MD = os.path.join(PLLA_DIR, "sites-138c.md")
SITES_JSON = os.path.join(PLLA_DIR, "sites-138c.json")
ATTRIDS_TSV = os.path.join(PLLA_DIR, "attrids-138c.tsv")

#: DS1239E Table 1-1, `Phase Locked Loop (PLLs)`.
DATASHEET_PLL_COUNT = 12

#: The six 25A entries of `fse_create_slot_plls`, as they stand before
#: `P1.T18` moves them into `_gw5a_pll_slots`. `(row, col, slot_idx, io_table)`.
GW5A_25A_SLOT_PLLS = {
    (27, 0, 6, "PllLB"),
    (27, 91, 2, "PllRB"),
    (0, 0, 5, "PllLT"),
    (0, 91, 3, "PllRT"),
    (0, 45, 4, "old_style"),
    (36, 45, 8, "old_style"),
}

_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([LRB])\s*\|\s*([^|]+?)\s*\|\s*\((\d+),\s*(\d+)\)\s*\|"
    r"\s*([^|]+?)\s*\|\s*(\w+)\s*\|"
)


def _md_rows():
    with open(SITES_MD, encoding="utf-8") as fh:
        return [m.groupdict() if False else m for m in
                (_ROW_RE.match(line) for line in fh) if m]


def test_plla_sites_artifact_counts():
    assert os.path.isfile(SITES_MD), f"missing artefact: {SITES_MD}"
    assert os.path.isfile(SITES_JSON), f"missing artefact: {SITES_JSON}"
    assert os.path.isfile(ATTRIDS_TSV), f"missing artefact: {ATTRIDS_TSV}"

    with open(SITES_MD, encoding="utf-8") as fh:
        md = fh.read()
    rows = _md_rows()

    # 1. exactly 12 PLL rows, and the artefact says so against the datasheet.
    assert len(rows) == DATASHEET_PLL_COUNT, (
        f"sites-138c.md has {len(rows)} PLL rows, expected {DATASHEET_PLL_COUNT}")
    assert str(DATASHEET_PLL_COUNT) in md
    idxs = sorted(int(m.group(1)) for m in rows)
    assert idxs == list(range(DATASHEET_PLL_COUNT)), f"pll_idx not 0..11: {idxs}"
    coords = {(int(m.group(4)), int(m.group(5))) for m in rows}
    assert len(coords) == DATASHEET_PLL_COUNT, "duplicate (row, col) in the table"

    # 2. the source column, and the blueprint bound this measurement refutes.
    sources = [m.group(7) for m in rows]
    assert sources.count("dat") == 0, (
        "the 138C .dat names no PLL site; a non-zero `dat` count means the "
        "artefact and the measurement have diverged")
    assert sources.count("unknown") == 0, (
        "every site position is measured from the .fse; `unknown` is not a "
        "legal source in this artefact")
    assert sources.count("fse") + sources.count("traced") == DATASHEET_PLL_COUNT
    assert "refuted" in md.lower(), (
        "sites-138c.md must record the refutation of the blueprint's 5-6 "
        "`dat`-named sites")

    # 3. sides: DS1239E Figure 2-1 draws 4 left, 4 right, 4 bottom.
    sides = [m.group(2) for m in rows]
    assert (sides.count("L"), sides.count("R"), sides.count("B")) == (4, 4, 4)

    # 4. the JSON agrees with the prose, field for field.
    with open(SITES_JSON, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert doc["device"] == "GW5AST-138C"
    assert doc["datasheet_pll_count"] == DATASHEET_PLL_COUNT
    assert doc["measured_site_count"] == DATASHEET_PLL_COUNT
    assert len(doc["sites"]) == DATASHEET_PLL_COUNT
    assert {(s["row"], s["col"]) for s in doc["sites"]} == coords
    assert all(len(s["tiles"]) == 3 for s in doc["sites"]), (
        "each 138C PLL site is three grid tiles wide (measured)")
    assert all(s["slot_idx"] is None for s in doc["sites"]), (
        "138C has no PLL slots: no pseudo-ttyp >= 1024 in its .fse")
    assert doc["fse"]["pseudo_ttyps"] == []
    assert doc["fse"]["has_drpfuse"] is False
    assert doc["reference_25a"]["pseudo_ttyps"] == [1024, 1025, 1026]
    assert all(v == 0 for v in doc["dat"]["named_tables_populated_rows"].values())

    # 5. the attrid census: > 0 rows, and its row count recorded verbatim.
    # `P1.T22` appended further blocks to this file (its reconciliation counts
    # and the nameless-id list), each separated by a blank line and introduced
    # by `#` comments. The census this task owns is the FIRST block, so read
    # exactly that -- the row count below is a `P1.T17` invariant about the
    # per-tile census, not about the file's total line count.
    with open(ATTRIDS_TSV, encoding="utf-8") as fh:
        first_block = fh.read().split("\n\n")[0]
    tsv = [ln for ln in first_block.splitlines()
           if ln.strip() and not ln.startswith("#")]
    header, data = tsv[0], tsv[1:]
    assert header.split("\t")[0] == "device"
    assert len(data) > 0
    # 12 sites x 3 tiles, plus the 25A pseudo-ttyp-1024 reference row.
    assert len(data) == DATASHEET_PLL_COUNT * 3 + 1
    assert f"**{len(data)} data rows**" in md, (
        f"sites-138c.md must record the TSV row count verbatim ({len(data)})")

    # 6. the attribute-id counts are recorded as numbers, not words.
    assert "2416" in md and "192" in md, (
        "sites-138c.md must record the 25A .fse attr-id count and "
        "len(attrids.pll_attrids) as numbers")
    per_site = {s["attr_id_count"] for s in doc["sites"]}
    assert per_site == {2433, 2437}, per_site
    assert all(str(n) in md for n in sorted(per_site))
    assert doc["attrids_py_pll_attrids"] == 192
    assert doc["reference_25a"]["slot_table_attr_ids"] == 2416


def test_plla_25a_enumeration_unchanged():
    """The 25A enumeration is identical before and after `P1.T17`.

    `P1.T17` adds no apicula code, so this pins the baseline `P1.T18` must
    preserve byte-for-byte when it replaces the hardcoded literal in
    `fse_create_slot_plls` with a per-device `_gw5a_pll_slots` table: the same
    six `(row, col, slot_idx, io_table)` entries, no more and no fewer.
    """
    import sys
    sys.path.insert(0, TOOLS_DIR)
    import paths  # noqa: E402

    apicula = paths.apicula_root()
    if apicula is None:                                   # pragma: no cover
        import pytest
        pytest.skip("apicula checkout not found")
    chipdb_py = os.path.join(apicula, "apycula", "chipdb.py")
    with open(chipdb_py, encoding="utf-8") as fh:
        src = fh.read()

    # `P1.T18` moves the literal out of the function body and into the
    # per-device table `_gw5a_pll_slots`, so look there first and fall back to
    # the body. What this test pins is the six ENTRIES, not where they live:
    # re-pointing it at the new home is the whole point of the move, while
    # letting an entry change is not.
    if "_gw5a_pll_slots = {" in src:
        table = src.split("_gw5a_pll_slots = {", 1)[1]
        body = table.split("'GW5A-25A':", 1)[1].split("},", 1)[0]
    else:
        body = src.split("def fse_create_slot_plls(", 1)[1].split("\ndef ", 1)[0]
    entries = set(
        (int(r), int(c), int(s), t)
        for r, c, s, t in re.findall(
            r"\((\d+),\s*(\d+),\s*(\d+),\s*'([A-Za-z_]+)'\)", body))
    assert entries == GW5A_25A_SLOT_PLLS, (
        "the six GW5A-25A PLL slot entries changed; P1.T18 must keep them "
        f"identical.\n  now: {sorted(entries)}\n  was: {sorted(GW5A_25A_SLOT_PLLS)}")

    # And the 25A JSON reference in the artefact carries the same six entries.
    with open(SITES_JSON, encoding="utf-8") as fh:
        doc = json.load(fh)
    recorded = {tuple(e) for e in doc["reference_25a"]["chipdb_slots"]}
    assert recorded == GW5A_25A_SLOT_PLLS
