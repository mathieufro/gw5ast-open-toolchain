"""`P2.T23` -- the `AE350_SOC` evidence row.

One property per test, each read off the appended row rather than off a
recomputation, so a row that was edited by hand fails here.
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = os.path.join(ROOT, "evidence", "ae350", "runs.jsonl")

#: `spec-harness.md` §6, and the field list `harness/evidence.REQUIRED_FIELDS`
#: declares once.  Repeated here as names, never as a count.
SCHEMA_FIELDS = (
    "run_id", "timestamp", "primitive", "shape", "sweep", "device", "part",
    "ide_version", "yosys_version", "apicula_sha", "nextpnr_sha",
    "chipdb_sha256", "mask_sha256", "level", "verdict", "diff_count",
    "first_diff", "fuses_moved", "unexplained_bits", "decode_check",
    "sdf_condition", "oracle_log", "open_log", "vendor_fs", "open_fs", "sdf",
    "tr", "wall_clock_s", "notes",
)
TERMINAL = ("ok", "diff", "aborted", "refused")


@pytest.fixture(scope="module")
def row():
    with open(ROWS) as fh:
        return json.loads(fh.read().strip().splitlines()[-1])


def test_ae350_row_has_all_schema_fields(row):
    missing = [f for f in SCHEMA_FIELDS if f not in row]
    assert missing == []
    for field in ("run_id", "verdict", "level", "chipdb_sha256", "mask_sha256"):
        assert row[field] is not None


def test_ae350_row_verdict_is_terminal(row):
    assert row["verdict"] in TERMINAL
    assert not str(row["verdict"]).startswith("blocked:")


def test_ae350_row_unexplained_bits_empty_or_justified(row):
    for entry in row["unexplained_bits"]:
        assert entry.get("justification")


def test_ae350_row_decode_check_both_ok(row):
    assert row["decode_check"] == {"c1": "ok", "c2": "ok"}


def test_ae350_row_notes_present_when_e0(row):
    if row["level"] == "E0":
        assert row["notes"].strip()


def test_ae350_row_closes_the_primitive_in_scope(row):
    """The block's own tiles carry no difference at all."""
    assert row["primitive"] == "AE350_SOC" and row["shape"] == "ae350_soc"
    for category in ("cells", "attrs", "conns"):
        assert row["diff_count"][category] == 0
    assert row["level"] in ("E1", "E2") and row["verdict"] == "ok"
