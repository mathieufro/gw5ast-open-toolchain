"""Tests for the ``AE350_RAM`` port inventory (``P2.T05``).

The counts are asserted against the vendor ``primitive.xml`` directly, so the
evidence file cannot drift away from its source without a test failing.
"""

import json
import os
import re
from pathlib import Path

import pytest

EVIDENCE = Path(__file__).resolve().parents[2] / "evidence" / "ae350-ram"
PORT_RE = re.compile(r'<(INPUT|OUTPUT|INOUT) width="(\d+)">([A-Za-z0-9_]+)</\1>')


def _primitive_block(name: str) -> str:
    gowinhome = os.environ.get("GOWINHOME")
    if not gowinhome:
        pytest.skip("GOWINHOME is not set")
    xml = Path(gowinhome) / "IDE/bin/prim_syns/gw5a/primitive.xml"
    if not xml.exists():
        pytest.skip(f"{xml} not present")
    match = re.search(
        rf"<module>\s*<name>{name}</name>(.*?)</module>",
        xml.read_text(errors="replace"),
        re.S,
    )
    assert match, f"no <module> block named {name}"
    return match.group(1)


def test_ae350_ram_port_inventory_count_is_26():
    block = _primitive_block("AE350_RAM")
    assert len(PORT_RE.findall(block)) == 26

    assert (EVIDENCE / "port-inventory.md").read_text().splitlines()[0] == "PORTS 26"
    assert json.loads((EVIDENCE / "port-inventory.json").read_text())["ports"] == 26


def test_ae350_ram_zero_parameters():
    assert "<PARAMETER" not in _primitive_block("AE350_RAM")
    assert json.loads((EVIDENCE / "port-inventory.json").read_text())["parameters"] == 0
