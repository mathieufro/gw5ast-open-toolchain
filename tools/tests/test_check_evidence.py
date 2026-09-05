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
            first = proc.stdout.split("\n", 1)[0]
            return int(first.split("EVIDENCE ok: ")[1].split(" rows")[0])

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
        first_line = proc.stdout.split("\n", 1)[0]
        self.assertEqual(
            first_line,
            "EVIDENCE ok: 1 rows, 4 pending, 0 blank, 0 missing artifacts")


if __name__ == "__main__":
    unittest.main()
