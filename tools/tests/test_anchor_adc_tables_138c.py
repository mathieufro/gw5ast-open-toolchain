"""The ADC anchor report (`P3.T28b`).

The device-file half needs a Gowin install; the shape half does not.
"""
import os

import pytest

from tools import anchor_adc_tables_138c as anchor

GOWINHOME = os.environ.get("GOWINHOME")
needs_ide = pytest.mark.skipif(not GOWINHOME, reason="no GOWINHOME")


def _block(cell=(109, 169), base=0x135f9):
    return {
        "ins_base": base,
        "outs_base": base + 3 * 0x28,
        "inputs": {"CLK": (109, 180, "CLK0")},
        "outputs": {f"ADCVALUE{i}": (cell[0], cell[1], wire)
                    for i, wire in enumerate(anchor.VALUE_WIRES)},
    }


def test_value_wires_are_one_cells_fourteen_output_wires():
    assert len(anchor.VALUE_WIRES) == 14
    assert len(set(anchor.VALUE_WIRES)) == 14


def test_confirmation_counts_the_value_wires_a_run_drives(monkeypatch):
    monkeypatch.setattr(anchor, "driven_wires",
                        lambda fs, cells: {cells[0]: {"F0", "F1", "OF7"}})
    report = anchor.confirm([_block()], ["/runs/r0/run/impl/pnr/run.fs"])
    assert report[0]["runs"]["r0"] == 3


def test_confirmation_ignores_wires_outside_the_value_run(monkeypatch):
    monkeypatch.setattr(anchor, "driven_wires",
                        lambda fs, cells: {cells[0]: {"Q3", "A0"}})
    report = anchor.confirm([_block()], ["/runs/r0/run/impl/pnr/run.fs"])
    assert report[0]["runs"]["r0"] == 0


def test_run_id_strips_the_vendors_own_tree():
    assert anchor.run_id("/d/p3-adc-0000/run/impl/pnr/run.fs") == "p3-adc-0000"


def test_report_names_the_cell_the_bitstream_must_speak_to():
    report = anchor.confirm([_block()], [])
    assert report[0]["value_cell"] == [108, 168]


@needs_ide
def test_two_blocks_are_located_and_reported():
    blocks = anchor.locate(GOWINHOME)
    assert len(blocks) == 2
    report = anchor.confirm(blocks, [])
    assert {tuple(row["value_cell"]) for row in report} == {(108, 168),
                                                           (108, 165)}
