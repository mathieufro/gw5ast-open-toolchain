"""Tests for `tools/check_evidence.py` (`P0.T30`, `DEL-e` first cut, `D63`).

Each test builds a throwaway `spec-primitives.md` + evidence tree (never
touching the live tree) and invokes `check_evidence.py` as a subprocess,
matching how `V9` actually runs it.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_EVIDENCE = os.path.join(TOOLS_DIR, "check_evidence.py")
PYTHON = sys.executable

sys.path.insert(0, TOOLS_DIR)
from paths import apicula_root  # noqa: E402

APICULA_ROOT = apicula_root()
MASK_PATH = (os.path.join(APICULA_ROOT, "fuzz", "gw5ast138c", "dontcare.mask")
             if APICULA_ROOT else None)


def _mask_sha256():
    if not MASK_PATH or not os.path.isfile(MASK_PATH):
        return "0" * 64  # no checked-in mask found; tests that need a real
                          # mismatch still work, mask-agreement tests are
                          # skipped via _mask_available()
    h = hashlib.sha256()
    with open(MASK_PATH, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def _mask_available():
    return bool(MASK_PATH and os.path.isfile(MASK_PATH))


PRIMITIVES_HEADER = "| Primitive | 25A status (file:line) | 138C status | Recipe | Done | Evidence |"
PRIMITIVES_SEP = "|---|---|---|---|---|---|"


def _primitives_row(name, slug, done="DONE-STD"):
    return f"| **{name}** | full | full | recipe | {done} | `evidence/{slug}/` |"


def write_spec_primitives(path, entries):
    """`entries`: list of (name, slug) or (name, slug, done_text)."""
    lines = ["# Spec satellite", "", "## 1. Section", "",
             PRIMITIVES_HEADER, PRIMITIVES_SEP]
    for entry in entries:
        name, slug = entry[0], entry[1]
        done = entry[2] if len(entry) > 2 else "DONE-STD"
        lines.append(_primitives_row(name, slug, done))
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def good_row(run_id, primitive, level="E1", verdict="ok", notes="",
             diff_count=None, unexplained_bits=None, mask_sha256=None):
    row = {
        "run_id": run_id, "timestamp": "2026-09-04T00:00:00+00:00",
        "primitive": primitive, "shape": "A", "sweep": {},
        "device": "GW5AST-138C", "part": "GW5AST-LV138PG484AC1/I0, device_version C",
        "ide_version": "1.9.12.03 Standard", "yosys_version": "0.63",
        "apicula_sha": "deadbeef", "nextpnr_sha": "deadbeef",
        "chipdb_sha256": "deadbeef", "mask_sha256": mask_sha256 or _mask_sha256(),
        "level": level, "verdict": verdict,
        "diff_count": diff_count if diff_count is not None else {},
        "first_diff": None, "fuses_moved": [],
        "unexplained_bits": unexplained_bits if unexplained_bits is not None else [],
        "decode_check": {"c1": "ok", "c2": "ok"}, "sdf_condition": "",
        "oracle_log": "", "open_log": "", "vendor_fs": [], "open_fs": [],
        "sdf": [], "tr": [], "wall_clock_s": {}, "notes": notes,
    }
    return row


def write_runs(evidence_dir, slug, rows):
    slug_dir = os.path.join(evidence_dir, slug)
    os.makedirs(slug_dir, exist_ok=True)
    with open(os.path.join(slug_dir, "runs.jsonl"), "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def run_tool(args, cwd=None):
    proc = subprocess.run([PYTHON, CHECK_EVIDENCE] + args,
                           capture_output=True, text=True, cwd=cwd)
    return proc


class CheckEvidenceTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="check-evidence-")
        self.spec_path = os.path.join(self.tmp, "spec-primitives.md")
        self.evidence_dir = os.path.join(self.tmp, "evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestStdoutContract(CheckEvidenceTestCase):
    def test_check_evidence_stdout_contract(self):
        write_spec_primitives(self.spec_path, [
            ("PLLA", "plla"), ("HCLK", "hclk"), ("DCS", "dcs"),
        ])
        write_runs(self.evidence_dir, "plla", [good_row("plla-A-0001", "PLLA")])
        write_runs(self.evidence_dir, "hclk", [good_row("hclk-A-0001", "HCLK")])
        write_runs(self.evidence_dir, "dcs", [good_row("dcs-A-0001", "DCS")])

        proc = run_tool([self.spec_path, self.evidence_dir])
        lines = proc.stdout.strip("\n").split("\n")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(lines, [
            # D90/G6: one RUNS line per discovered runs.jsonl, then the
            # roll-up, then the two contract lines.
            "RUNS dcs/runs.jsonl: 1 rows, 1 valid",
            "RUNS hclk/runs.jsonl: 1 rows, 1 valid",
            "RUNS plla/runs.jsonl: 1 rows, 1 valid",
            "RUNS: 3 files, 3 rows, 3 valid",
            "EVIDENCE ok: 3 rows, 0 pending, 0 blank, 0 missing artifacts",
            "0 admissibility findings",
        ])


class TestCallShapesEquivalent(CheckEvidenceTestCase):
    def test_check_evidence_call_shapes_equivalent(self):
        write_spec_primitives(self.spec_path, [("PLLA", "plla")])
        write_runs(self.evidence_dir, "plla", [good_row("plla-A-0001", "PLLA")])

        # bare: copy the tool + tree into <tmp>/tools/check_evidence.py so
        # the script's own path-based defaults ($PIPE/spec-primitives.md,
        # $PIPE/evidence) resolve to this fixture tree without cwd tricks.
        bare_tools = os.path.join(self.tmp, "tools")
        os.makedirs(bare_tools, exist_ok=True)
        shutil.copy(CHECK_EVIDENCE, os.path.join(bare_tools, "check_evidence.py"))
        shutil.copy(os.path.join(TOOLS_DIR, "paths.py"),
                    os.path.join(bare_tools, "paths.py"))
        bare = subprocess.run(
            [PYTHON, os.path.join(bare_tools, "check_evidence.py")],
            capture_output=True, text=True)

        both_positionals = run_tool([self.spec_path, self.evidence_dir])
        evidence_flag = run_tool([self.spec_path, "--evidence", self.evidence_dir])
        positional_plus_flag = run_tool(
            [self.spec_path, "/nonexistent/wrong-dir", "--evidence", self.evidence_dir])

        outputs = [bare.stdout, both_positionals.stdout, evidence_flag.stdout,
                   positional_plus_flag.stdout]
        for proc, out in zip(
                (bare, both_positionals, evidence_flag, positional_plus_flag), outputs):
            self.assertEqual(proc.returncode, 0, out + getattr(proc, "stderr", ""))
        self.assertEqual(len(set(outputs)), 1,
                          f"4 invocations produced {len(set(outputs))} distinct outputs: {outputs}")


class TestSlugScoping(CheckEvidenceTestCase):
    def test_check_evidence_slug_scoping(self):
        write_spec_primitives(self.spec_path, [
            ("PA", "a"), ("PB", "b"), ("PC", "c"),
        ])
        write_runs(self.evidence_dir, "a", [good_row("a-A-0001", "PA")])
        write_runs(self.evidence_dir, "b", [good_row("b-A-0001", "PB")])
        write_runs(self.evidence_dir, "c", [good_row("c-A-0001", "PC")])

        only_a = run_tool([self.spec_path, self.evidence_dir, "--slug", "a"])
        a_and_b = run_tool(
            [self.spec_path, self.evidence_dir, "--slug", "a", "--slug", "b"])
        bare = run_tool([self.spec_path, self.evidence_dir])

        def n_of(proc):
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            line = [l for l in proc.stdout.split("\n")
                    if l.startswith("EVIDENCE ok: ")][0]
            return int(line.split("EVIDENCE ok: ")[1].split(" rows")[0])

        self.assertEqual(n_of(only_a), 1)
        self.assertEqual(n_of(a_and_b), 2)
        self.assertEqual(n_of(bare), 3)


class TestFailsOnBlockedStatus(CheckEvidenceTestCase):
    def test_check_evidence_fails_on_blocked_status(self):
        write_spec_primitives(self.spec_path, [
            ("PLLA", "plla", "blocked:PLLA"),
        ])
        write_runs(self.evidence_dir, "plla", [good_row("plla-A-0001", "PLLA")])

        proc = run_tool([self.spec_path, self.evidence_dir])
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("blocked:", proc.stdout)
        self.assertIn("PLLA", proc.stdout)


class TestFailsOnMaskMismatch(CheckEvidenceTestCase):
    def test_check_evidence_fails_on_mask_mismatch(self):
        if not _mask_available():
            self.skipTest("no checked-in dontcare.mask found (apicula checkout absent)")
        write_spec_primitives(self.spec_path, [("PLLA", "plla")])
        write_runs(self.evidence_dir, "plla", [
            good_row("plla-A-0001", "PLLA", mask_sha256="f" * 64)])

        proc = run_tool([self.spec_path, self.evidence_dir])
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("mask_sha256", proc.stdout)


class TestFailsOnUnenumeratedResidual(CheckEvidenceTestCase):
    def test_check_evidence_fails_on_unenumerated_residual(self):
        write_spec_primitives(self.spec_path, [("PLLA", "plla")])
        write_runs(self.evidence_dir, "plla", [
            good_row("plla-A-0001", "PLLA", verdict="diff",
                      diff_count={"cells": 1, "attrs": 0, "conns": 0, "pips": 0},
                      unexplained_bits=["?"])])

        proc = run_tool([self.spec_path, self.evidence_dir])
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestTolerartesPartialSpec(CheckEvidenceTestCase):
    def test_check_evidence_tolerates_partial_spec(self):
        write_spec_primitives(self.spec_path, [
            ("PA", "a"), ("PB", "b"), ("PC", "c"), ("PD", "d"), ("PE", "e"),
        ])
        write_runs(self.evidence_dir, "a", [good_row("a-A-0001", "PA")])
        # b, c, d, e: no evidence directory at all -> PENDING, not a crash.

        proc = run_tool([self.spec_path, self.evidence_dir])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(
            "EVIDENCE ok: 1 rows, 4 pending, 0 blank, 0 missing artifacts",
            proc.stdout.split("\n"))


if __name__ == "__main__":
    unittest.main()


# --------------------------------------------------------------------------
# `D90` (gestalt `G6`): the sweep over every `runs.jsonl` in the tree, which
# the `spec-primitives.md` walk above cannot reach while the table is partial.
# These are `pytest` functions on purpose: they use `tmp_path`, and nothing in
# them names an absolute path outside it.
# --------------------------------------------------------------------------
import pytest  # noqa: E402


def _skip_without_apicula():
    if APICULA_ROOT is None:
        pytest.skip("no apicula checkout found (set $FL_APICULA); the §6 "
                    "evidence-row schema lives there and is never re-declared")


def _d90_tree(tmp_path):
    """A spec table naming **no** slug, so only the D90 sweep can see rows."""
    spec = tmp_path / "spec-primitives.md"
    write_spec_primitives(str(spec), [])
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    return str(spec), str(evidence)


def test_check_evidence_validates_runs_jsonl(tmp_path):
    """A slug no `spec-primitives.md` row names is still opened and counted."""
    _skip_without_apicula()
    spec, evidence = _d90_tree(tmp_path)
    write_runs(evidence, "unnamed-slug", [
        good_row("unnamed-A-0001", "PLLA"),
        good_row("unnamed-A-0002", "PLLA"),
    ])
    write_runs(evidence, "nested/deeper", [good_row("deep-A-0001", "HCLK")])

    proc = run_tool([spec, evidence])

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RUNS unnamed-slug/runs.jsonl: 2 rows, 2 valid" in proc.stdout
    assert os.path.join("nested", "deeper", "runs.jsonl") in proc.stdout
    assert "RUNS: 2 files, 3 rows, 3 valid" in proc.stdout
    # The old vacuous verdict: 0 rows matched from the table, and yet green.
    assert "EVIDENCE ok: 0 rows" in proc.stdout


def test_check_evidence_rejects_malformed_row(tmp_path):
    """Negative control: one bad row anywhere in the tree fails the run."""
    _skip_without_apicula()
    spec, evidence = _d90_tree(tmp_path)
    write_runs(evidence, "good-slug", [good_row("good-A-0001", "PLLA")])

    bad = good_row("bad-A-0001", "PLLA")
    bad["verdict"] = "probably-fine"          # not a §6 verdict
    write_runs(evidence, "bad-slug", [good_row("bad-A-0000", "PLLA"), bad])
    # ...and a line that is not JSON at all.
    with open(os.path.join(evidence, "bad-slug", "runs.jsonl"), "a") as fh:
        fh.write("{not json at all\n")

    proc = run_tool([spec, evidence])

    assert proc.returncode != 0, proc.stdout
    assert "bad-A-0001" in proc.stdout
    assert "probably-fine" in proc.stdout
    assert "not valid JSON Lines" in proc.stdout


def test_check_evidence_rejects_empty_runs_jsonl(tmp_path):
    """Negative control: a `runs.jsonl` that exists and carries no row."""
    _skip_without_apicula()
    spec, evidence = _d90_tree(tmp_path)
    write_runs(evidence, "empty-slug", [])

    proc = run_tool([spec, evidence])

    assert proc.returncode != 0, proc.stdout
    assert "RUNS empty-slug/runs.jsonl: 0 rows, 0 valid" in proc.stdout
    assert "0 valid evidence rows" in proc.stdout


def test_check_evidence_bookkeeping_row_is_not_a_run_row(tmp_path):
    """A row with no equivalence result answers to the bookkeeping floor.

    `spec-harness.md` §6 describes the (primitive, shape, sweep) run row; the
    chipdb build log and the `D26` budget rows are a different kind and are
    not judged against a schema they never claimed -- but they are still
    validated, and an unreadable one still fails.
    """
    _skip_without_apicula()
    spec, evidence = _d90_tree(tmp_path)
    write_runs(evidence, "chipdb-like", [
        {"task": "P0.T12", "device": "GW5AST-138C", "outcome": "ok",
         "sha256": "0" * 64, "bytes": 1234},
    ])
    ok_proc = run_tool([spec, evidence])
    assert ok_proc.returncode == 0, ok_proc.stdout + ok_proc.stderr
    assert "RUNS chipdb-like/runs.jsonl: 1 rows, 1 valid" in ok_proc.stdout

    # Negative control: a bookkeeping row using a verdict outside §6's own
    # vocabulary, and one that records nothing at all.
    write_runs(evidence, "chipdb-like", [
        {"task": "P0.T12", "verdict": "sort-of-ok"},
        {"task": "P0.T13"},
    ])
    bad_proc = run_tool([spec, evidence])
    assert bad_proc.returncode != 0, bad_proc.stdout
    assert "sort-of-ok" in bad_proc.stdout
