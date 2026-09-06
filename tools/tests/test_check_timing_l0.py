"""Tests for `tools/check_timing_l0.py` (P0.T32, DEL-e first cut, drives V12a).

The four `V12a` contract tests use a synthetic timing dict (the shape of
`db.timing`, loaded through `--chipdb <file>.json`) plus a synthetic SDF,
so they exercise the real emission/comparison code without a chipdb build.
The last two tests run against the live GW5AST-138C chipdb.
"""
import json
import os
import re
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


@pytest.mark.parametrize("cls", ["io", "dsp"])
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


# --------------------------------------------------------------------------
# P0.T37: fixes forced by the first real vendor SDF
# (attosoc-tangmega138k, Gowin SDF Writer 1.0, IDE 1.9.12.03)
# --------------------------------------------------------------------------
def test_check_timing_l0_condition_joins_multiline_header(tmp_path):
    """A real Gowin SDF puts VOLTAGE / PROCESS / TEMPERATURE on three lines.

    `D49f` requires *the corner* recorded, so all three header condition
    lines are echoed as ONE line (`V12a` allows exactly one), each verbatim
    and in file order. Taking only the first (VOLTAGE) loses the process and
    temperature corner entirely.
    """
    multi = ("(VOLTAGE 0.93:0.90:0.87)\n"
             '  (PROCESS "best=0.65: nom=1.0: worst=1.8")\n'
             "  (TEMPERATURE 85:25:0)")
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf = write_sdf(tmp_path, [1.25] * 10, condition=multi)
    rc, out, err = run_tool("--classes", "cfu", "--sdf", sdf, "--chipdb", chipdb)
    assert rc == 0, out + err
    lines = out.splitlines()
    assert lines[0] == "L0 ok: 10/10 arcs within ±10%, 0 exceptions listed"
    assert lines[1] == ('(VOLTAGE 0.93:0.90:0.87) '
                        '(PROCESS "best=0.65: nom=1.0: worst=1.8") '
                        "(TEMPERATURE 85:25:0)")
    # still exactly one condition line
    assert sum(1 for ln in lines if ln.startswith("(VOLTAGE")) == 1


def test_check_timing_l0_matches_bus_indexed_pins(tmp_path):
    """`DO[0]` in the SDF and `DO0` in nextpnr's model are the same arc.

    nextpnr's BSRAM cell variants name the data-out bits `DO0..DO31`
    (`gowin_arch_gen.py`), while the vendor SDF names the Verilog port bit
    `DO[0]`. Without normalisation every BSRAM arc on a real design lands in
    `unmapped` and the BSRAM half of the `D60` CFU class is never measured.
    """
    assert ctl.norm_pin("DO[0]") == ctl.norm_pin("DO0")
    assert ctl.norm_pin("RAD[3]") == ctl.norm_pin("RAD3")
    assert ctl.norm_pin("CLKB") == "CLKB"
    # different indices must stay different
    assert ctl.norm_pin("DO[0]") != ctl.norm_pin("DO1")


# --------------------------------------------------------------------------
# P1.T33: the PLL slice of the L0 band (`D60`) -- a zero-arc class by
# measurement.  The `.tm` carries no PLL model for this die (its 0x7cc block is
# inherited GW2A rPLL data), nextpnr installs no PLL cell arc, and the vendor
# SDF gives every `CLKIN -> CLKOUTn` IOPATH as `0.000`.  The band therefore
# compares each vendor PLL arc against a model delay of 0.0.
# --------------------------------------------------------------------------
PLL_SDF_ARCS = [("PLL", "dut_pll", "CLKIN", f"CLKOUT{n}") for n in range(7)]


def write_pll_sdf(tmp_path, delays, name="pll.sdf", condition=CONDITION_LINE):
    """A vendor-shaped SDF with one `PLL` cell plus one unrelated `LUT4` cell."""
    body = []
    for (cell, inst, frm, to), d in zip(
            PLL_SDF_ARCS + [("LUT4", "lut_a", "I0", "F")], list(delays) + [1.25]):
        triple = f"{d:.3f}:{d:.3f}:{d:.3f}"
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
        '  (VENDOR "Gowin")\n'
        '  (PROGRAM "Gowin SDF Writer")\n'
        "  (DIVIDER /)\n"
        f"  {condition}\n"
        "  (TIMESCALE 1 ns)\n" + "\n".join(body) + "\n)\n"
    )
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def test_v12a_pll_band(tmp_path):
    """`--classes pll --sdf <pll design>` prints the V12a contract and exits 0."""
    chipdb = write_timing(tmp_path, synthetic_timing())   # no `pll` group
    sdf = write_pll_sdf(tmp_path, [0.0] * 7)
    rc, out, err = run_tool("--classes", "pll", "--sdf", sdf, "--chipdb", chipdb)
    lines = out.splitlines()
    assert re.match(
        r"^L0 ok: \d+/\d+ arcs within ±10%, \d+ exceptions listed$", lines[0]
    ), lines[0]
    assert lines[0] == "L0 ok: 7/7 arcs within ±10%, 0 exceptions listed"
    assert lines[1] == CONDITION_LINE          # the SDF condition line (D49f)
    assert rc == 0, out + err


def test_v12a_pll_band_ignores_non_pll_cells(tmp_path):
    """The `pll` class compares PLL cells only; the LUT4 in the same SDF is not counted."""
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf = write_pll_sdf(tmp_path, [0.0] * 7)
    rc, out, _ = run_tool("--classes", "pll", "--sdf", sdf, "--chipdb", chipdb)
    assert out.splitlines()[0].startswith("L0 ok: 7/7 ")
    assert "unmapped" not in out
    assert rc == 0


def test_v12a_pll_band_fails_if_vendor_publishes_a_delay(tmp_path):
    """A future vendor release with a non-zero PLL arc must fail, not pass quietly."""
    chipdb = write_timing(tmp_path, synthetic_timing())
    sdf = write_pll_sdf(tmp_path, [0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0])
    rc, out, _ = run_tool("--classes", "pll", "--sdf", sdf, "--chipdb", chipdb)
    assert out.splitlines()[0] == "L0 ok: 6/7 arcs within ±10%, 1 exceptions listed"
    assert "exception: PLL/dut_pll CLKIN->CLKOUT2" in out
    assert rc != 0


def test_pll_inventory_reports_the_zero_arc_class(tmp_path):
    """Inventory mode reports `pll` with its justification and exits 0."""
    chipdb = write_timing(tmp_path, synthetic_timing())
    rc, out, err = run_tool("--classes", "pll", "--chipdb", chipdb)
    assert rc == 0, out + err
    assert "BY DESIGN (P1.T33)" in out
    assert "0x7cc" in out and "GW2A-18.tm" in out
    assert out.rstrip().splitlines()[-1].startswith("L0 INVENTORY ok: 0/0 ")


@pytest.mark.skipif(not os.path.isfile(REAL_CHIPDB), reason="no built chipdb")
def test_real_chipdb_has_no_pll_timing_group():
    """`parse_pll` publishes nothing, so no grade carries a `pll` group (P1.T33)."""
    timing = ctl.load_timing(REAL_CHIPDB)
    for grade, groups in timing.items():
        assert "pll" not in groups, f"{grade} gained a pll timing group"
