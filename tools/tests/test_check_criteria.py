"""Tests for `tools/check_criteria.py` (P0.T31, DEL-e first cut).

Fixtures build a small `spec-primitives.md`-shaped table and a matching
evidence tree under `tmp_path`, so these tests exercise the real parsing
and evidence-matching code paths without depending on the live (partial)
pipeline table.
"""
import json
import os
import sys

import pytest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import check_criteria as cc  # noqa: E402


TABLE_HEADER = (
    "| Primitive | Phase | 25A status (file:line) | 138C status | "
    "Recipe — shape, sweep, runs | Done | Evidence |\n"
    "|---|---|---|---|---|---|---|\n"
)


def _table_row(id_, phase, evidence_slug):
    return (
        f"| **{id_}** | {phase} | full | full | one shape, 4 runs | "
        f"DONE-STD | `evidence/{evidence_slug}/` |\n"
    )


def write_spec_primitives(tmp_path, rows):
    """`rows`: list of `(id, phase, evidence_slug)`. Returns the file path."""
    path = tmp_path / "spec-primitives.md"
    text = (
        "# Spec satellite — per-primitive table\n\n"
        "**DONE-STD.** the standard done criterion.\n\n"
        "## 1. Fixture section\n\n"
        + TABLE_HEADER
        + "".join(_table_row(*r) for r in rows)
        + "\n"
    )
    path.write_text(text, encoding="utf-8")
    return str(path)


def _evidence_row(primitive, verdict="ok", level="E1", c1="ok", c2="ok",
                   notes=""):
    return {
        "run_id": f"{primitive}-A-0001",
        "primitive": primitive,
        "verdict": verdict,
        "level": level,
        "decode_check": {"c1": c1, "c2": c2},
        "unexplained_bits": [],
        "notes": notes,
    }


def write_evidence(tmp_path, slug_rows):
    """`slug_rows`: {slug: [evidence_row_dict, ...]}. Returns evidence dir."""
    root = tmp_path / "evidence"
    for slug, rows in slug_rows.items():
        slug_dir = root / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        with open(slug_dir / "runs.jsonl", "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        (slug_dir / "summary.md").write_text("summary\n", encoding="utf-8")
    return str(root)


SATISFIED = "GATE:PASS satisfied on the smoke design"


def test_check_criteria_stdout_contract(tmp_path, capsys):
    rows = [("R1", "0", "r1"), ("R2", "0", "r2"),
            ("R3", "1", "r3"), ("R4", "1", "r4")]
    spec = write_spec_primitives(tmp_path, rows)
    evidence = write_evidence(tmp_path, {
        slug: [_evidence_row(id_, notes=SATISFIED)]
        for id_, _phase, slug in rows
    })

    exit_code = cc.main([spec, evidence])

    out = capsys.readouterr().out
    assert out == "CRITERIA ok: 4/4\n"
    assert exit_code == 0


def test_check_criteria_clause_d_deferred_by_default(tmp_path, capsys):
    rows = [("R1", "0", "r1")]
    spec = write_spec_primitives(tmp_path, rows)
    # No GATE:PASS marker: this row fails clause (d) if enforced.
    evidence = write_evidence(tmp_path, {"r1": [_evidence_row("R1")]})

    exit_code = cc.main([spec, evidence, "--rows", "R1"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.count(cc.CLAUSE_D_DEFERRED_LINE) == 1


def test_check_criteria_clause_d_enforced_when_enabled(tmp_path, capsys):
    rows = [("R1", "0", "r1")]
    spec = write_spec_primitives(tmp_path, rows)
    evidence = write_evidence(tmp_path, {"r1": [_evidence_row("R1")]})

    exit_code = cc.main([spec, evidence, "--rows", "R1", "--enable-clause-d"])

    out = capsys.readouterr().out
    assert exit_code != 0
    assert "R1" in out


def test_check_criteria_unscoped_partial_is_a_survey(tmp_path, capsys):
    rows = [("R1", "0", "r1"), ("R2", "0", "r2"), ("R3", "1", "r3"),
            ("R4", "1", "r4"), ("R5", "1", "r5")]
    spec = write_spec_primitives(tmp_path, rows)
    slug_rows = {
        "r1": [_evidence_row("R1", notes=SATISFIED)],
        "r2": [_evidence_row("R2", notes=SATISFIED)],
        "r3": [],
        "r4": [],
        "r5": [],
    }
    evidence = write_evidence(tmp_path, slug_rows)

    exit_code = cc.main([spec, evidence])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "CRITERIA ok: 2/5" in out
    pending = {line.split(": ", 1)[1] for line in out.splitlines()
               if line.startswith("pending: ")}
    assert pending == {"R3", "R4", "R5"}


def test_check_criteria_scoped_unmet_rows_fail(tmp_path, capsys):
    rows = [("R1", "0", "r1"), ("R2", "0", "r2"), ("R3", "1", "r3"),
            ("R4", "1", "r4"), ("R5", "1", "r5")]
    spec = write_spec_primitives(tmp_path, rows)
    slug_rows = {
        "r1": [_evidence_row("R1", notes=SATISFIED)],
        "r2": [_evidence_row("R2", notes=SATISFIED)],
        "r3": [],
        "r4": [],
        "r5": [],
    }
    evidence = write_evidence(tmp_path, slug_rows)

    exit_code = cc.main([spec, evidence, "--rows", "R3,R4,R5"])
    out = capsys.readouterr().out
    assert exit_code != 0
    for id_ in ("R3", "R4", "R5"):
        assert id_ in out

    exit_code = cc.main([spec, evidence, "--rows", "R1,R2"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "CRITERIA ok: 2/2" in out


def test_check_criteria_phase_flag_resolves_rows(tmp_path, capsys):
    rows = [("R1", "0", "r1"), ("R2", "0", "r2"), ("R3", "1", "r3"),
            ("R4", "1", "r4"), ("R5", "1", "r5")]
    spec = write_spec_primitives(tmp_path, rows)
    evidence = write_evidence(tmp_path, {
        slug: [_evidence_row(id_, notes=SATISFIED)]
        for id_, _phase, slug in rows
    })

    exit_code_phase = cc.main([spec, evidence, "--phase", "0"])
    out_phase = capsys.readouterr().out
    assert exit_code_phase == 0

    exit_code_rows = cc.main([spec, evidence, "--rows", "R1,R2"])
    out_rows = capsys.readouterr().out
    assert exit_code_rows == 0

    assert out_phase == out_rows == "CRITERIA ok: 2/2\n"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# --------------------------------------------------------------------------
# `D90` (gestalt `G6`): a scoped run also asserts the phase's own ledger, and
# an assertion that examined nothing is no longer a pass.
# --------------------------------------------------------------------------
def write_phase_report(evidence_dir, phase, rows):
    """`rows`: list of `(first cell, verdict cell)`. Returns the file path."""
    phase_dir = os.path.join(evidence_dir, f"phase{phase}")
    os.makedirs(phase_dir, exist_ok=True)
    path = os.path.join(phase_dir, cc.PHASE_REPORT_NAME)
    lines = [f"# Phase {phase} — close report", "",
             "| S-id | Step | Verdict |", "|---|---|---|"]
    lines += [f"| {first} | `V1` | {verdict} |" for first, verdict in rows]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_slug_claim(evidence_dir, slug, criterion_ids, rows=()):
    """A slug whose `summary.md` claims `criterion_ids`, with `rows` rows."""
    slug_dir = os.path.join(evidence_dir, slug)
    os.makedirs(slug_dir, exist_ok=True)
    claim = " ".join(f"`{cid}`" for cid in criterion_ids)
    with open(os.path.join(slug_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# {slug} — {claim}, the criteria this slug backs\n")
    if rows:
        with open(os.path.join(slug_dir, "runs.jsonl"), "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")


def test_check_criteria_rejects_unbacked_reached(tmp_path, capsys):
    """Negative control: REACHED, claimed by a slug that carries no row."""
    spec = write_spec_primitives(tmp_path, [])
    evidence = str(tmp_path / "evidence")
    os.makedirs(evidence, exist_ok=True)
    write_phase_report(evidence, 0, [
        ("`S1` a criterion with rows", "**REACHED** — proven"),
        ("`S2` a criterion with none", "**REACHED** — claimed only"),
        ("`S3` an honest one", "**NOT REACHED** — owed to phase 1"),
    ])
    write_slug_claim(evidence, "backed-slug", ["S1"],
                     rows=[_evidence_row("S1", notes=SATISFIED)])
    write_slug_claim(evidence, "empty-slug", ["S2"])  # summary.md, no rows

    exit_code = cc.main([spec, evidence, "--phase", "0"])
    out = capsys.readouterr().out

    assert exit_code != 0, out
    assert "unbacked REACHED: S2" in out
    assert "empty-slug" in out
    assert "unbacked REACHED: S1" not in out
    assert "S3" not in out            # NOT REACHED is not a claim
    assert "CRITERIA ok: 1/2" in out


def test_check_criteria_accepts_backed_reached(tmp_path, capsys):
    """The same ledger passes once the claiming slug carries a row."""
    spec = write_spec_primitives(tmp_path, [])
    evidence = str(tmp_path / "evidence")
    os.makedirs(evidence, exist_ok=True)
    write_phase_report(evidence, 0, [
        ("`S1` a criterion with rows", "**REACHED** — proven"),
        ("standing: the gate is blocking", "**REACHED** — proven by tests"),
    ])
    write_slug_claim(evidence, "backed-slug", ["S1"],
                     rows=[_evidence_row("S1", notes=SATISFIED)])

    exit_code = cc.main([spec, evidence, "--phase", "0"])
    out = capsys.readouterr().out

    assert exit_code == 0, out
    assert "CRITERIA ok: 2/2" in out
    # A criterion no slug claims is reported, not silently counted as proven.
    assert "unlinked: standing: the gate is blocking" in out


def test_check_criteria_rejects_vacuous_zero(tmp_path, capsys):
    """Negative control: `CRITERIA ok: 0/0` is no longer a pass (`D90`)."""
    spec = write_spec_primitives(tmp_path, [("R1", "1", "r1")])
    evidence = write_evidence(tmp_path, {"r1": [_evidence_row("R1")]})

    # --phase 0 resolves to no spec-primitives row and there is no phase
    # report: the old tool printed "CRITERIA ok: 0/0" and exited 0.
    exit_code = cc.main([spec, evidence, "--phase", "0"])
    out = capsys.readouterr().out

    assert exit_code != 0, out
    assert "CRITERIA ok: 0/0" in out
    assert "vacuous assertion" in out


def test_check_criteria_vacuous_phase_report_is_examined(tmp_path, capsys):
    """A phase report with criteria makes `--phase N` non-vacuous by itself."""
    spec = write_spec_primitives(tmp_path, [])
    evidence = str(tmp_path / "evidence")
    os.makedirs(evidence, exist_ok=True)
    write_phase_report(evidence, 0, [("`S1` claimed", "**REACHED**")])
    write_slug_claim(evidence, "empty-slug", ["S1"])

    exit_code = cc.main([spec, evidence, "--phase", "0"])
    out = capsys.readouterr().out

    assert exit_code != 0, out
    assert "PHASE-REPORT" in out
    assert "vacuous assertion" not in out   # it examined 1 criterion
    assert "unbacked REACHED: S1" in out
