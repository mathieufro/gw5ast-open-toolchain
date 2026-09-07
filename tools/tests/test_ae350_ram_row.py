"""`P2.T25` -- the `AE350_RAM` evidence rows.

The row's verdict is `refused`, which is a deliverable and not a hole
(`D30`): the vendor's exact words are what the row is for.  One property per
test, each read off the appended rows rather than off a recomputation.
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = os.path.join(ROOT, "evidence", "ae350-ram", "runs.jsonl")
SUMMARY = os.path.join(ROOT, "evidence", "ae350-ram", "summary.md")

TERMINAL = ("ok", "diff", "aborted", "refused")
LEVELS = ("E0", "E1", "E2")

#: The vendor's refusal, byte for byte, as `gw_sh` printed it.
VENDOR_REFUSAL = ("ERROR (RP0008) : There is no AE350_RAM resource in "
                  "current device, please change device")


@pytest.fixture(scope="module")
def rows():
    with open(ROWS) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_ae350_ram_rows_all_terminal(rows):
    assert rows
    for row in rows:
        assert row["verdict"] in TERMINAL
        assert not str(row["verdict"]).startswith("blocked:")


def test_ae350_ram_row_level_at_least_e0(rows):
    for row in rows:
        assert row["level"] in LEVELS


def test_ae350_ram_evidence_dir_resolvable():
    assert os.path.isfile(SUMMARY)
    with open(SUMMARY) as fh:
        assert len(fh.readlines()) <= 200


def test_ae350_ram_refusals_carry_the_vendors_exact_words(rows):
    """A refusal without the tool's own sentence is an opinion, not evidence."""
    for row in rows:
        if row["verdict"] == "refused":
            assert VENDOR_REFUSAL in row["notes"]


def test_ae350_ram_asks_the_question_with_and_without_the_soc(rows):
    """One point alone cannot tell an absent resource from an occupied site."""
    assert {row["sweep"]["companion"] for row in rows} == {"soc", "solo"}


def test_ae350_ram_claims_no_decode_it_never_ran(rows):
    """No bitstream was produced, so `c1`/`c2` are `n/a` and never `ok`."""
    for row in rows:
        assert row["decode_check"] == {"c1": "n/a", "c2": "n/a"}
        assert row["vendor_fs"] is None and row["open_fs"] is None
