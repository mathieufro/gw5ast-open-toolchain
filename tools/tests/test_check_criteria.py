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
