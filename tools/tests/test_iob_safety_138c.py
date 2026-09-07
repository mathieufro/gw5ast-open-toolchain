"""The IOB / bank-default safety row's verdict rules (`P3.T26`)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from derive_iob_safety_138c import (  # noqa: E402
    DesignReport, Site, _classify, pin_state,
)


def _report():
    return DesignReport(design="fixture")


SITE = Site(row=50, col=181, name="IOBA")


def test_pin_state_names_the_four_states():
    assert pin_state("IBUF") == "used_input"
    assert pin_state("OBUF") == "used_output"
    assert pin_state("IOBUF") == "used_inout"
    assert pin_state("TLVDS_OBUF") == "diff_pair"


def test_open_only_fuse_is_a_violation():
    report = _report()
    _classify(report, "fixture", SITE, "unused",
              vendor={"IO_TYPE": "LVCMOS33"},
              opened={"IO_TYPE": "LVCMOS33", "PULL_STRENGTH": "STRONG"})
    kinds = [(v.attr, v.kind) for v in report.violations]
    assert kinds == [("PULL_STRENGTH", "open_only")]


def test_vendor_only_fuse_is_not_a_violation():
    report = _report()
    _classify(report, "fixture", SITE, "unused",
              vendor={"IO_TYPE": "LVCMOS33", "DRIVE": "8"},
              opened={"IO_TYPE": "LVCMOS33"})
    assert report.violations == []
    assert report.classes["unused"]["DRIVE:vendor_only"] == 1


def test_safety_attr_value_difference_is_a_violation():
    report = _report()
    _classify(report, "fixture", SITE, "used_output",
              vendor={"IO_TYPE": "LVCMOS33", "PULL_STRENGTH": "MEDIUM"},
              opened={"IO_TYPE": "LVCMOS33", "PULL_STRENGTH": "STRONG"})
    assert [(v.attr, v.kind) for v in report.violations] == [
        ("PULL_STRENGTH", "value_diff")]


def test_used_pin_without_io_type_is_a_violation():
    report = _report()
    _classify(report, "fixture", SITE, "used_input",
              vendor={"IO_TYPE": "LVCMOS33"}, opened={})
    assert [(v.attr, v.kind) for v in report.violations] == [
        ("IO_TYPE", "unset_on_used")]


def test_unused_pin_without_io_type_is_not_a_violation():
    report = _report()
    _classify(report, "fixture", SITE, "unused",
              vendor={"IO_TYPE": "LVCMOS33"}, opened={})
    assert report.violations == []


def test_unused_io_attrvals_match_the_packer_default_set():
    """The set this row subtracts is the one `GW5A` actually emits.

    If `get_unused_io_attrvals` ever changes, the drive-bit attribution below
    stops meaning what it says, so the two are pinned together here.
    """
    from derive_iob_safety_138c import DRIVE_ATTRS, UNUSED_IO_ATTRVALS

    assert dict(UNUSED_IO_ATTRVALS) == {
        "OPENDRAIN": "OFF", "IO_TYPE": "LVCMOS33", "DRIVE": "8",
        "DRIVE_LEVEL": "8", "PADDI": "PADDI", "PULLMODE": "NONE",
    }
    assert set(DRIVE_ATTRS) <= set(dict(UNUSED_IO_ATTRVALS))
