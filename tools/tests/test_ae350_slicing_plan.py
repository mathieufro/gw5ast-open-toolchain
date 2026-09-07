"""Tests for the ``AE350_SOC`` bus-slicing plan (``P2.T06``).

``needed`` is taken from ``reconciliation.md`` when ``P2.T04`` has landed it, and
otherwise re-measured from the same ``primitive.xml`` block the reconciliation
measures, so the plan is checked against a source rather than against itself.
"""

import os
import re
from pathlib import Path

import pytest

EVIDENCE = Path(__file__).resolve().parents[2] / "evidence" / "ae350"
PLAN = EVIDENCE / "slicing-plan.md"
RECONCILIATION = EVIDENCE / "reconciliation.md"
CLOCKS = {"CORE_CLK", "DDR_CLK", "AHB_CLK", "APB_CLK", "RTC_CLK", "DBG_TCK"}
ROW_RE = re.compile(
    r"^\|\s*([A-Za-z0-9_]+)\s*\|\s*(\d+)\s*\|\s*"
    r"(McuIns\[\d+:\d+\]|McuOuts\[\d+:\d+\]|EC5-discovery)\s*\|\s*"
    r"(AE350_IN|AE350_OUT|TILE_CLK)\s*\|$"
)


def plan_rows():
    if not PLAN.exists():
        pytest.skip("slicing-plan.md not written yet")
    rows = [m.groups() for m in map(ROW_RE.match, PLAN.read_text().splitlines()) if m]
    assert rows, "no plan rows parsed"
    return rows


def needed_bits():
    if RECONCILIATION.exists():
        m = re.search(r"^RECONCILIATION-VERDICT: \d+/(\d+) ", RECONCILIATION.read_text(), re.M)
        if m:
            return int(m.group(1))
    gowinhome = os.environ.get("GOWINHOME")
    if not gowinhome:
        pytest.skip("no reconciliation.md and GOWINHOME is not set")
    xml = Path(gowinhome) / "IDE/bin/prim_syns/gw5a/primitive.xml"
    block = re.search(
        r"<module>\s*<name>AE350_SOC</name>(.*?)</module>",
        xml.read_text(errors="replace"),
        re.S,
    ).group(1)
    return sum(
        int(w)
        for _, w, _ in re.findall(
            r'<(INPUT|OUTPUT|INOUT) width="(\d+)">([A-Za-z0-9_]+)</\1>', block
        )
    )


def test_slicing_plan_covers_every_port():
    assert sum(int(w) for _, w, _, _ in plan_rows()) == needed_bits()


def test_slicing_plan_slices_do_not_overlap():
    seen = {"McuIns": set(), "McuOuts": set()}
    for _, _, source, _ in plan_rows():
        m = re.match(r"(McuIns|McuOuts)\[(\d+):(\d+)\]", source)
        if not m:
            continue
        table, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
        span = set(range(lo, hi))
        assert not span & seen[table], f"{source} overlaps an earlier slice"
        seen[table] |= span


def test_slicing_plan_six_clocks_are_tile_clk():
    tile_clk = {name for name, _, _, wtype in plan_rows() if wtype == "TILE_CLK"}
    assert tile_clk == CLOCKS
