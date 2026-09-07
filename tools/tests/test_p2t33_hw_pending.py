"""Tests for `P2.T33` -- the `E0+hw-pending` rows and `spec-primitives.md`
status cells for `S19`'s hardware halves.

`D33`/`D59`: an `E0+hw-pending` row records, in its own `notes`, both the
reason `E1` was unavailable and the named hardware observation Phase 9 still
owes; the corresponding `spec-primitives.md` status cell must use only the
four-value vocabulary (`E1` / `E0+hw` / `E0+hw-pending` / `refused:<error>`)
and never the in-flight `blocked:` marker (`D33`).

These tests read the live pipeline documents rather than a fixture copy --
`P2.T33`'s job is to make specific real files true, and a fixture could pass
while the real files remain wrong.
"""
import glob
import json
import os
import re

PIPE = os.environ.get(
    "PIPE",
    "/Users/alex/fine-line/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84")
OTC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE_DIR = os.path.join(OTC, "evidence")
SPEC_PRIMITIVES = os.path.join(PIPE, "spec-primitives.md")

HW_PENDING_TOKEN = "E0+hw-pending"
STATUS_VOCAB_RE = re.compile(
    r"`(E0\+hw-pending|E0\+hw|E1|E2|E0|refused:[^`]*|refused)`")

#: The three rows this phase closes (`P2.T33`'s scope); `Dual-purpose pins`
#: is excluded -- it belongs to `P2.T29`, a separate branch.
ROW_IDS = ("AE350_SOC", "AE350_RAM", "Dual-purpose pins")
ROW_IDS_OWNED_BY_T33 = ("AE350_SOC", "AE350_RAM")

RUNS_FILES = (
    os.path.join(EVIDENCE_DIR, "ae350", "runs.jsonl"),
    os.path.join(EVIDENCE_DIR, "ae350-ram", "runs.jsonl"),
    os.path.join(EVIDENCE_DIR, "dualpin", "runs.jsonl"),
)


def _read_jsonl(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _all_rows():
    rows = []
    for path in RUNS_FILES:
        rows.extend(_read_jsonl(path))
    return rows


def _row_status_cell(row_id):
    """The `138C status` cell text for one `spec-primitives.md` row id."""
    with open(SPEC_PRIMITIVES, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(rf"\|\s*\*\*{re.escape(row_id)}\*\*\s*\|", text)
    assert m, f"no row named **{row_id}** in {SPEC_PRIMITIVES}"
    # Split the rest of the line into pipe-delimited cells; the row may
    # itself contain literal `|` only inside code spans, none of which
    # this row uses, so a plain split is safe here.
    line_start = text.rfind("\n", 0, m.start()) + 1
    line_end = text.find("\n", m.start())
    cells = [c.strip() for c in text[line_start:line_end].strip("|").split("|")]
    # column order: Primitive | ... | 138C status | ... -- locate it by
    # searching for the first cell (after the id) carrying a recognised
    # status token, robust to the differing column layouts across sections.
    for cell in cells[1:]:
        if STATUS_VOCAB_RE.search(cell):
            return cell
    raise AssertionError(f"no status-vocabulary cell found for {row_id}")


def test_hw_pending_rows_carry_token_and_observation():
    """Every `E0` row that names a deferred hardware observation is complete."""
    found_any = False
    for row in _all_rows():
        notes = str(row.get("notes") or "")
        if HW_PENDING_TOKEN not in notes:
            continue
        found_any = True
        assert row.get("level") == "E0", (
            f"{row.get('run_id')}: {HW_PENDING_TOKEN} requires level E0, "
            f"got {row.get('level')!r}")
        assert row.get("verdict") == "ok", (
            f"{row.get('run_id')}: {HW_PENDING_TOKEN} requires verdict ok, "
            f"got {row.get('verdict')!r}")
        said = notes.replace(HW_PENDING_TOKEN, "").replace(
            "timing_model=unverified", "").strip(" |").strip()
        assert said, (
            f"{row.get('run_id')}: {HW_PENDING_TOKEN} names no observation")
    assert found_any, (
        "no E0+hw-pending row found under evidence/ae350{,-ram}/dualpin -- "
        "P2.T33 was expected to write at least one")


def test_ae350_soc_s19_hw_row_names_both_owed_observations():
    rows = _read_jsonl(os.path.join(EVIDENCE_DIR, "ae350", "runs.jsonl"))
    hw_rows = [r for r in rows
               if r.get("primitive") == "AE350_SOC"
               and HW_PENDING_TOKEN in str(r.get("notes") or "")]
    assert hw_rows, "no AE350_SOC row records E0+hw-pending"
    notes = hw_rows[0]["notes"]
    assert "BUILD_LOAD" in notes and "debug TAP" in notes
    assert "UART2" in notes


def test_spec_primitives_three_status_cells_non_blank():
    for row_id in ROW_IDS:
        cell = _row_status_cell(row_id)
        assert cell.strip(), f"{row_id}'s status cell is blank"
        assert STATUS_VOCAB_RE.search(cell), (
            f"{row_id}'s status cell {cell!r} carries no recognised "
            "status-vocabulary token")


def test_spec_primitives_ae350_soc_records_both_the_row_and_s19_hw_status():
    cell = _row_status_cell("AE350_SOC")
    assert "`E1`" in cell, "AE350_SOC's own row status must stay E1"
    assert HW_PENDING_TOKEN in cell, (
        "AE350_SOC's cell must also record S19(hw) as E0+hw-pending")


def test_spec_primitives_ae350_ram_status_is_refused():
    cell = _row_status_cell("AE350_RAM")
    assert "refused" in cell.lower()


def test_no_blocked_status_anywhere():
    for path in RUNS_FILES:
        if not os.path.isfile(path):
            continue  # e.g. evidence/dualpin/ before P2.T29 lands
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        assert "blocked:" not in text, f"{path} carries a blocked: status"

    for row_id in ROW_IDS_OWNED_BY_T33:
        cell = _row_status_cell(row_id)
        assert "blocked:" not in cell, f"{row_id}'s status cell carries blocked:"
