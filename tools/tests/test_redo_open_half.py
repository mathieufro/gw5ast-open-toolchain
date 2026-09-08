"""`redo_open_half` never spends a vendor run and never invents one.

A batch whose vendor step succeeded and whose open flow then aborted (a
`nextpnr`/`chipdb` pair mismatch, measured on `p3-oser-b`) must be repaired by
rebuilding the open half over the design directories already on disk.  The two
properties that make that safe are the ones asserted here.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from tools import redo_open_half  # noqa: E402


def test_redo_refuses_a_row_whose_vendor_bitstream_is_gone(tmp_path):
    """Rebuilding a run whose oracle output is missing would quietly need a
    new vendor run, which is the one thing this tool exists to avoid."""
    row = {"run_id": "r0", "sweep": {"POINT": "p"},
           "vendor_fs": [{"path": str(tmp_path / "absent.fs")}]}
    with pytest.raises(SystemExit) as excinfo:
        redo_open_half.redo(row, "io_ser", str(tmp_path))
    assert "no vendor bitstream on disk" in str(excinfo.value)


def test_redo_keeps_every_field_the_oracle_owns():
    """The repaired row's vendor half is the oracle's own record, not a
    re-measurement -- so the field list is explicit and cannot drift."""
    assert "vendor_fs" in redo_open_half.VENDOR_FIELDS
    assert "oracle_log" in redo_open_half.VENDOR_FIELDS
    assert "sdf" in redo_open_half.VENDOR_FIELDS
    assert "open_fs" not in redo_open_half.VENDOR_FIELDS


def test_redo_finds_the_bitstream_it_will_reuse(tmp_path):
    fs = tmp_path / "run.fs"
    fs.write_text("")
    row = {"vendor_fs": [{"path": str(fs)}]}
    assert redo_open_half.vendor_bitstream(row) == str(fs)
    assert redo_open_half.vendor_bitstream({"vendor_fs": []}) is None


def _rows_file(tmp_path, vendor_path):
    """A one-row batch whose vendor bitstream is at *vendor_path* (or gone)."""
    path = tmp_path / "batch.rows.jsonl"
    path.write_text(json.dumps({
        "run_id": "row-0", "verdict": "diff", "level": "E1", "sweep": {"X": 0},
        "vendor_fs": ([{"path": vendor_path}] if vendor_path else []),
    }) + "\n", encoding="utf-8")
    return str(path)


def test_a_batch_is_refused_when_a_vendor_bitstream_is_missing(tmp_path):
    """The default stays strict: rebuilding without the oracle output is the
    thing this tool exists to prevent."""
    rows = _rows_file(tmp_path, None)
    with pytest.raises(SystemExit):
        redo_open_half.main(["--rows", rows, "--shape", "io_basic",
              "--design-root", str(tmp_path)])


def test_the_missing_row_can_be_kept_instead_of_losing_the_batch(tmp_path,
                                                                capsys):
    """One deleted vendor bitstream must not cost the other measured rows."""
    rows = _rows_file(tmp_path, None)
    assert redo_open_half.main(["--rows", rows, "--shape", "io_basic",
                 "--design-root", str(tmp_path),
                 "--skip-missing-vendor"]) == 0
    assert "vendor bitstream absent" in capsys.readouterr().out
