"""`P3.T05` -- nextpnr sees the IOLOGIC bels and the HCLK flag on GW5AST-138C.

The three checks read the artefacts the rebuild produced (`.bba` text, `.bin`,
and the `nextpnr-himbaechel --verbose` log of a real placement), never a
report about them. They skip rather than fail when those artefacts are absent,
because rebuilding them is the task's job, not the test's.
"""
import os
import re

import pytest

DATASTORE = os.environ.get(
    "DATASTORE", "/Users/alex/fine-line-data/open-toolchain-gw5ast")
P3 = os.path.join(DATASTORE, "p3")
BBA = os.path.join(P3, "chipdb-GW5AST-138C.bba")
BIN = os.path.join(P3, "chipdb-GW5AST-138C.bin")
NEXTPNR_LOG = os.path.join(P3, "nextpnr-oddr-probe.log")

#: `gowin.h:251` -- `HAS_5A_HCLK` as nextpnr sees it (`F56`).
CHIP_HAS_5A_HCLK = 0x10000


def _need(path):
    if not os.path.isfile(path):
        pytest.skip(f"{path} absent; run the P3.T05 rebuild first")
    return path


def _chip_flags_word():
    """The first `u32` after `label extra_data` -- `ChipExtraData.serialise`."""
    with open(_need(BBA), encoding="utf-8", errors="replace") as handle:
        seen = False
        for line in handle:
            if seen and line.startswith("u32 "):
                return int(line.split()[1])
            if line.startswith("label extra_data") and line.strip() == "label extra_data":
                seen = True
    raise AssertionError("no `label extra_data` block in the .bba")


def test_nextpnr_chipdb_has_iologic_bels():
    """IOLOGIC survives the crossing: named in the `.bba`, counted by nextpnr.

    The bel names the generator emits are `IOLOGICA{I,O}` / `IOLOGICB{I,O}`
    (`gowin_arch_gen.py`), and nextpnr reports them by *type*, `IOLOGICI` /
    `IOLOGICO` -- so the two sides are checked in their own vocabularies.
    """
    text = open(_need(BBA), encoding="utf-8", errors="replace").read()
    assert text.count("IOLOGICA") >= 1
    log = open(_need(NEXTPNR_LOG), encoding="utf-8", errors="replace").read()
    match = re.search(r"IOLOGICI:\s*(\d+)/\s*(\d+)", log)
    assert match, "nextpnr printed no IOLOGICI utilisation line"
    used, available = int(match.group(1)), int(match.group(2))
    assert available >= 1
    assert used >= 1, "the probe design placed no IOLOGIC cell"


def test_nextpnr_chipdb_hclk_flag():
    """`CHIP_HAS_5A_HCLK` is set in the chip-level flags word."""
    assert _chip_flags_word() & CHIP_HAS_5A_HCLK == CHIP_HAS_5A_HCLK


def test_nextpnr_oddr_places():
    """The probe placed and routed: exit 0 and not one `ERROR` line."""
    _need(BIN)
    log = open(_need(NEXTPNR_LOG), encoding="utf-8", errors="replace").read()
    assert sum(1 for line in log.splitlines() if line.startswith("ERROR")) == 0
    assert "Program finished normally." in log
