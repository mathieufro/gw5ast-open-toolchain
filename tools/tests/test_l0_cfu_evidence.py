"""`P0.T37` -- the recorded L0 CFU band measurement (`V12a --classes cfu`, `D60`).

These tests assert the *evidence*, not the tool: that
`evidence/timing-l0-cfu/summary.md` carries one verbatim `V12a` contract line
with its condition line, that every exception the contract line counts is
actually listed, and that the `runs.jsonl` row records the SDF condition and a
chipdb sha256 from the post-`P0.T40` de-aliased rebuild (`F2`).
"""
import json
import os
import re

OTC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLUG = os.path.join(OTC, "evidence", "timing-l0-cfu")
SUMMARY = os.path.join(SLUG, "summary.md")
ROWS = os.path.join(SLUG, "runs.jsonl")
CHIPDB_SHAS = os.path.join(OTC, "evidence", "chipdb", "chipdb-sha256.txt")

CONTRACT_RE = re.compile(r"^L0 ok: (\d+)/(\d+) arcs within ±10%, (\d+) exceptions listed$")


def _summary_lines():
    with open(SUMMARY, encoding="utf-8") as f:
        return f.read().splitlines()


def _rows():
    with open(ROWS, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def _row(primitive="L0-cfu-band"):
    """The one row for `primitive`.

    The slug's `runs.jsonl` holds one row per L0 class band, not one row full
    stop: `P1.T33` added `L0-pll-band` beside `P0.T37`'s `L0-cfu-band`. These
    tests assert the CFU measurement, so they select it by primitive rather
    than by being the only line in the file.
    """
    rows = [r for r in _rows() if r["primitive"] == primitive]
    assert len(rows) == 1, f"expected exactly 1 {primitive} row, got {len(rows)}"
    return rows[0]


def _contract():
    lines = _summary_lines()
    hits = [(i, CONTRACT_RE.match(ln)) for i, ln in enumerate(lines)]
    hits = [(i, m) for i, m in hits if m]
    assert len(hits) == 1, f"expected exactly 1 V12a contract line, got {len(hits)}"
    return lines, hits[0][0], hits[0][1]


def test_l0_cfu_measured_and_recorded():
    lines, idx, m = _contract()
    assert int(m.group(1)) >= 1, "no arc was measured in band"
    assert int(m.group(2)) >= 1
    condition = lines[idx + 1]
    assert condition.strip(), "no SDF condition line after the contract line"
    # exactly one condition line in the whole file
    assert sum(1 for ln in lines if ln == condition) == 1


def test_l0_cfu_exceptions_enumerated():
    lines, idx, m = _contract()
    k = int(m.group(3))
    listed = [ln for ln in lines if ln.startswith("exception: ")]
    assert len(listed) == k, f"contract line says {k} exceptions, {len(listed)} listed"


def test_l0_cfu_row_has_sdf_condition():
    lines, idx, _m = _contract()
    row = _row()
    assert row["sdf_condition"], "runs.jsonl row has an empty sdf_condition"
    assert row["sdf_condition"] == lines[idx + 1]


def test_l0_cfu_chipdb_is_post_dealias():
    with open(CHIPDB_SHAS, encoding="utf-8") as f:
        text = f.read()
    post = text.split("# post-T35 rebuild", 1)[1]
    pre = text.split("# post-T35 rebuild", 1)[0]
    dev_re = re.compile(r"^std GW5AST-138C\s+([0-9a-f]{64})", re.M)
    post_shas = dev_re.findall(post)
    pre_shas = dev_re.findall(pre)
    assert post_shas and pre_shas
    row = _row()
    assert sum(1 for s in post_shas if s == row["chipdb_sha256"]) == 1
    assert row["chipdb_sha256"] not in pre_shas


# --------------------------------------------------------------------------
# P1.T33: the PLL class band lives in the same slug (`D60`)
# --------------------------------------------------------------------------
def test_l0_pll_row_recorded():
    """The `L0-pll-band` row records the zero-arc result and its condition line."""
    row = _row("L0-pll-band")
    assert row["sweep"]["classes"] == "pll"
    assert row["verdict"] == "ok"
    assert row["sdf_condition"], "no SDF condition line recorded (D49f)"
    assert "7/7 arcs within +/-10%" in row["notes"]
    assert os.path.isfile(os.path.join(SLUG, "pll-slice.md"))
