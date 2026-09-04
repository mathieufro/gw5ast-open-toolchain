"""Tests for `tools/check_timing_l0.py` (P0.T32, DEL-e first cut, drives V12a).

The four `V12a` contract tests use a synthetic timing dict (the shape of
`db.timing`, loaded through `--chipdb <file>.json`) plus a synthetic SDF,
so they exercise the real emission/comparison code without a chipdb build.
The last two tests run against the live GW5AST-138C chipdb.
"""
import json
import os
import subprocess
import sys

import pytest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import check_timing_l0 as ctl  # noqa: E402

TOOL = os.path.join(TOOLS_DIR, "check_timing_l0.py")
OTC = os.path.dirname(TOOLS_DIR)
REAL_CHIPDB = os.path.join(
    os.path.dirname(OTC), "apicula", "apycula", "GW5AST-138C.msgpack.xz"
)

CONDITION_LINE = '(PROCESS "1.000::1.000") (VOLTAGE 0.855::0.855) (TEMPERATURE 100.000::100.000)'


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------
def _quad(v):
    """A chipdb timing entry: (ff, fr, rr, rf) all equal, so max == v."""
    return [v, v, v, v]


def synthetic_timing(scale=1.0):
    """A `db.timing`-shaped dict with the `lut` and `alu` groups populated.

    Every arc is 1.0 ns * `scale` in the C2/I1 grade; C1/I0 is the same
    table * 1.25, exactly as `tm_parser` derives it (P0.T35).
    """
    lut = {k: _quad(1.0 * scale) for k in
           ("a_f", "b_f", "c_f", "d_f", "m0_ofx0", "m1_ofx1", "fx_ofx1")}
    alu = {k: _quad(1.0 * scale) for k in
           ("a_f", "b_f", "d_f", "fci_f0", "a0_fco", "b0_fco", "d0_fco", "fci_fco")}
    c2 = {"lut": lut, "alu": alu}
    c1 = {g: {k: [x * 1.25 for x in v] for k, v in arcs.items()}
          for g, arcs in c2.items()}
    return {"C1/I0": c1, "C2/I1": c2}


def write_timing(tmp_path, timing, name="timing.json"):
    p = tmp_path / name
    p.write_text(json.dumps(timing))
    return str(p)


SDF_ARCS = [
    ("LUT4", "lut_a", "I0", "F"),
    ("LUT4", "lut_a", "I1", "F"),
    ("LUT4", "lut_a", "I2", "F"),
    ("LUT4", "lut_a", "I3", "F"),
    ("ALU", "alu_a", "I0", "SUM"),
    ("ALU", "alu_a", "I1", "SUM"),
    ("ALU", "alu_a", "I3", "SUM"),
    ("ALU", "alu_a", "CIN", "SUM"),
    ("ALU", "alu_a", "I0", "COUT"),
    ("ALU", "alu_a", "CIN", "COUT"),
]


def write_sdf(tmp_path, delays, name="run.sdf", condition=CONDITION_LINE):
    """`delays`: list of 10 `max`-field values, one per `SDF_ARCS` entry."""
    body = []
    for (cell, inst, frm, to), d in zip(SDF_ARCS, delays):
        triple = f"{d / 3:.3f}:{d / 2:.3f}:{d:.3f}"
        body.append(
            f'  (CELL (CELLTYPE "{cell}") (INSTANCE {inst})\n'
            f"    (DELAY (ABSOLUTE\n"
            f"      (IOPATH {frm} {to} ({triple}) ({triple}))\n"
            f"    ))\n"
            f"  )"
        )
    text = (
        "(DELAYFILE\n"
        '  (SDFVERSION "3.0")\n'
        '  (DESIGN "top")\n'
        '  (VENDOR "GOWIN")\n'
        '  (PROGRAM "GowinSynthesis")\n'
        "  (DIVIDER /)\n"
        f"  {condition}\n"
        "  (TIMESCALE 1ns)\n" + "\n".join(body) + "\n)\n"
    )
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def run_tool(*args):
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, env=env
    )
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------
# V12a stdout contract
# --------------------------------------------------------------------------
def test_check_timing_l0_stdout_contract(tmp_path):
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf = write_sdf(tmp_path, [1.25] * 10)  # model C1/I0 == 1.25 ns, in band
    rc, out, err = run_tool("--classes", "cfu", "--sdf", sdf, "--chipdb", chipdb)
    lines = out.splitlines()
    assert rc == 0, out + err
    assert lines[0] == "L0 ok: 10/10 arcs within ±10%, 0 exceptions listed"
    assert lines[1] == CONDITION_LINE


def test_check_timing_l0_lists_exceptions(tmp_path):
    chipdb = write_timing(tmp_path, synthetic_timing())
    # arcs 0 and 4 are 15% above the model -> out of the ±10% band
    delays = [1.25] * 10
    delays[0] = 1.25 * 1.15
    delays[4] = 1.25 * 1.15
    sdf = write_sdf(tmp_path, delays)
    rc, out, err = run_tool("--classes", "cfu", "--sdf", sdf, "--chipdb", chipdb)
    lines = out.splitlines()
    assert rc != 0, out
    assert lines[0] == "L0 ok: 8/10 arcs within ±10%, 2 exceptions listed"
    assert lines[1] == CONDITION_LINE
    assert "LUT4/lut_a I0->F" in out
    assert "ALU/alu_a I0->SUM" in out


def test_check_timing_l0_uses_max_field():
    assert ctl.sdf_triple_max("1.0:2.0:3.0") == 3.0
    assert ctl.sdf_triple_max("(1.0:2.0:3.0)") == 3.0
    # a partially specified triple keeps the max field
    assert ctl.sdf_triple_max("::3.0") == 3.0


def test_check_timing_l0_uses_max_field_end_to_end(tmp_path):
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf_path = tmp_path / "t.sdf"
    sdf_path.write_text(
        "(DELAYFILE\n"
        '  (SDFVERSION "3.0")\n'
        f"  {CONDITION_LINE}\n"
        "  (TIMESCALE 1ns)\n"
        '  (CELL (CELLTYPE "LUT4") (INSTANCE lut_a)\n'
        "    (DELAY (ABSOLUTE\n"
        "      (IOPATH I0 F (1.0:2.0:3.0) (1.0:2.0:3.0))\n"
        "    ))\n"
        "  )\n"
        ")\n"
    )
    rc, out, err = run_tool(
        "--classes", "cfu", "--sdf", str(sdf_path), "--chipdb", chipdb
    )
    # model is 1.25 ns, vendor max field is 3.0 ns -> one exception quoting 3.000
    assert out.splitlines()[0] == "L0 ok: 0/1 arcs within ±10%, 1 exceptions listed"
    assert "sdf=3.000ns" in out
    assert rc != 0


@pytest.mark.parametrize("cls", ["pll", "io", "dsp"])
def test_check_timing_l0_skips_unpopulated_classes(tmp_path, cls):
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf = write_sdf(tmp_path, [1.25] * 10)
    rc, out, err = run_tool("--classes", cls, "--sdf", sdf, "--chipdb", chipdb)
    assert rc == 0, out + err
    assert out == f"L0 skipped: class {cls} has no arcs yet\n"


# --------------------------------------------------------------------------
# inventory mode (no --sdf): the P0.T32 chipdb-side measurement
# --------------------------------------------------------------------------
def test_inventory_flags_derived_grade_and_ratio_band(tmp_path):
    chipdb = write_timing(tmp_path, synthetic_timing())
    rc, out, err = run_tool("--classes", "cfu", "--chipdb", chipdb)
    assert "C1/I0" in out and "derived" in out
    assert "1.250" in out
    # the synthetic dict has only lut+alu, so the other required groups are empty
    assert rc != 0
    assert "missing" in out


def test_inventory_fails_on_ratio_out_of_band(tmp_path):
    timing = synthetic_timing()
    timing["C1/I0"]["lut"]["a_f"] = _quad(2.0)  # ratio 2.0, outside the band
    chipdb = write_timing(tmp_path, timing)
    rc, out, err = run_tool("--classes", "cfu", "--chipdb", chipdb)
    assert rc != 0
    assert "ratio" in out and "FAIL" in out


@pytest.mark.skipif(not os.path.exists(REAL_CHIPDB), reason="no built chipdb")
def test_real_chipdb_cfu_inventory_passes():
    rc, out, err = run_tool("--classes", "cfu", "--chipdb", REAL_CHIPDB)
    assert rc == 0, out + err
    assert "L0 INVENTORY ok:" in out
    for group in ("lut", "alu", "dff", "sram", "bram", "wire", "glbsrc", "hclk"):
        assert group in out
    assert "derived" in out  # C1/I0 must never be reported as measured


@pytest.mark.skipif(not os.path.exists(REAL_CHIPDB), reason="no built chipdb")
def test_real_chipdb_reports_nextpnr_gaps():
    rc, out, err = run_tool("--classes", "cfu", "--chipdb", REAL_CHIPDB)
    assert "nextpnr emission" in out
    assert "unconsumed" in out
