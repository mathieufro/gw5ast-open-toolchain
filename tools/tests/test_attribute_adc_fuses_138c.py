"""The ADC attribution instrument, against a die stubbed to a known answer.

The point of the tool is the three-way ownership question -- pip, shortval
entry, or nothing -- so these fixtures make each of the three happen and check
the tool says which.  A tool that reports "moved" without saying who owns the
bits cannot tell a routed port from a configuration fuse, which is exactly the
distinction the ADC row turned on.
"""
import pytest

from tools import attribute_adc_fuses_138c as attr


class _TileData:
    def __init__(self, ttyp, pips=None, clock_pips=None):
        self.ttyp = ttyp
        self.pips = pips or {}
        self.clock_pips = clock_pips or {}


class _Db:
    """Two cells: one whose moved bits are pips, one whose are a table."""

    def __init__(self):
        self.shortval = {
            1: {},
            2: {"unknown_137": {(57, 0): [(20, 63)], (58, 0): [(20, 62)]},
                "unknown_138": {(57, 0): [(20, 32)], (58, 0): [(20, 31)]},
                "named": {(1, 0): [(0, 0)]}},
        }
        self._tiles = {
            (108, 180): _TileData(1, pips={"A0": {"F7": [(9, 0), (9, 1)]}}),
            (108, 181): _TileData(2),
        }

    def __getitem__(self, key):
        return self._tiles[key]


BASE = {(108, 180): {(9, 0)}, (108, 181): set()}


def _measured(point, tiles):
    return {attr.BASELINE: BASE, point: tiles}


def test_routed_bits_are_named_as_routing_not_as_a_fuse():
    """A port driven from the fabric moves pips; it needs no attribution."""
    records = attr.classify(
        _Db(), _measured("adclrc-vsen3",
                         {(108, 180): {(9, 1)}, (108, 181): set()}))
    assert len(records) == 1
    assert records[0]["tile"] == (108, 180)
    assert records[0]["routing"] == records[0]["moved"] == 2
    assert records[0]["entries"] == []
    assert records[0]["unattributed"] == []


def test_a_configuration_bit_resolves_to_its_table_entry():
    """A parameter's bits are named by the entry that reproduces them."""
    records = attr.classify(
        _Db(), _measured("adclrc-divctl1",
                         {(108, 180): {(9, 0)},
                          (108, 181): {(20, 32), (20, 63)}}))
    assert [r["entries"] for r in records] == [
        [("unknown_137", (57, 0)), ("unknown_138", (57, 0))]]
    assert attr.div_ctl_codes(records) == {
        1: [("unknown_137", (57, 0)), ("unknown_138", (57, 0))]}


def test_a_bit_no_owner_explains_is_reported_unattributed():
    """Silence about an unexplained bit is what `D30` forbids."""
    records = attr.classify(
        _Db(), _measured("adclrc-divctl3",
                         {(108, 180): {(9, 0)}, (108, 181): {(4, 4)}}))
    assert records[0]["unattributed"] == [(4, 4)]
    assert attr.div_ctl_codes(records) == {}


def test_an_incomplete_axis_is_refused_rather_than_reported():
    """Half an axis cannot identify a code, so the tool must not try."""
    assert attr.main(["--rows", "/dev/null"]) == 1


def test_every_swept_point_is_on_one_axis_only():
    """A point that moved two parameters at once would confound both."""
    for point, pairs in attr.POINTS.items():
        if point == attr.BASELINE:
            continue
        assert len(pairs) == 1, point
