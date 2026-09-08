"""Repacking a stored run must reproduce it, or it proves nothing."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repack_open_fs import PINCFG_FLAGS, pincfg_flags, repack  # noqa: E402


def _pnr(tmp_path, parameters):
    path = tmp_path / "top_pnr.json"
    path.write_text(json.dumps({"modules": {"top": {"cells": {
        "PINCFG": {"type": "PINCFG", "parameters": parameters},
        "GSR": {"type": "GSR", "parameters": {}},
    }}}}), encoding="utf-8")
    return str(path)


def test_no_dual_purpose_pin_flag_is_invented(tmp_path):
    assert pincfg_flags(_pnr(tmp_path, {})) == []


def test_a_set_parameter_becomes_its_flag(tmp_path):
    parameters = {"SSPI": "0" * 31 + "1"}
    assert pincfg_flags(_pnr(tmp_path, parameters)) == ["--sspi_as_gpio"]


def test_a_cleared_parameter_does_not(tmp_path):
    assert pincfg_flags(_pnr(tmp_path, {"SSPI": "0" * 32})) == []


def test_every_flag_the_packer_cross_checks_is_derivable():
    """`gowin_pack.get_PINCFG_fuses` raises when the two sides disagree on
    these two, so a wrong flag set is a hard error and never a silent
    mis-pack."""
    assert set(PINCFG_FLAGS) == {"SSPI", "I2C"}


def test_a_run_without_a_placement_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        repack(str(tmp_path), "top-f2.fs", "/nonexistent")
