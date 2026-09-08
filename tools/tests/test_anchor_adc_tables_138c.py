"""The ADC table anchor locates by rule and confirms by measurement.

`P3.T28a`. The point of these guards is that neither half can quietly become
the other: a window that passes the three structural filters is a *candidate*,
and only the vendor bitstream's own routing turns a candidate record into a
confirmed one. A tool that scored an unmeasured window as confirmed would hand
`chipdb` a portmap with no evidence behind it, which is the failure `D30` names.
"""
from tools import anchor_adc_tables_138c as anchor

WIRENAMES = {1: "A0", 2: "A1", 3: "B3", 4: "F5", 5: "Q0", 6: "CLK0"}
ABSENT = (0xffff, 0xffff, 0xffff)


def _words(records):
    out = []
    for rec in records:
        out.extend(rec)
    return out


def test_a_window_of_input_role_wires_in_the_block_cells_is_a_candidate():
    words = _words([(109, 181, 1), (109, 181, 2), (109, 181, 3)] + [ABSENT])
    found = anchor.windows(words, WIRENAMES, 4, anchor.ADCLRC_DAT_CELLS,
                           anchor.INPUT_WIRE_RE, 3)
    assert len(found) == 1
    assert found[0]["base"] == 0
    assert found[0]["absent"] == 1


def test_a_wire_of_the_wrong_role_disqualifies_the_window():
    """`F`/`Q` are what the block drives; they cannot be in its input table."""
    words = _words([(109, 181, 1), (109, 181, 5), (109, 181, 3), ABSENT])
    assert anchor.windows(words, WIRENAMES, 4, anchor.ADCLRC_DAT_CELLS,
                          anchor.INPUT_WIRE_RE, 3) == []


def test_a_cell_outside_the_block_disqualifies_the_window():
    words = _words([(109, 181, 1), (50, 50, 2), (109, 181, 3), ABSENT])
    assert anchor.windows(words, WIRENAMES, 4, anchor.ADCLRC_DAT_CELLS,
                          anchor.INPUT_WIRE_RE, 3) == []


def test_a_wire_named_twice_disqualifies_the_window():
    """A second port cannot share a tap."""
    words = _words([(109, 181, 1), (109, 181, 1), (109, 181, 3), ABSENT])
    assert anchor.windows(words, WIRENAMES, 4, anchor.ADCLRC_DAT_CELLS,
                          anchor.INPUT_WIRE_RE, 3) == []


def test_confirmation_counts_only_records_the_bitstream_can_speak_to():
    """A cell with no measured wire set is not evidence either way."""
    window = {"live": [(109, 181, "A0"), (109, 181, "A1"), (109, 169, "B3")]}
    measured = {(109, 181): {"A0", "A1"}}
    assert anchor.confirm(window, measured) == (2, 2)


def test_confirmation_fails_a_record_the_bitstream_contradicts():
    window = {"live": [(109, 181, "A0"), (109, 181, "C7")]}
    measured = {(109, 181): {"A0", "A1"}}
    assert anchor.confirm(window, measured) == (1, 2)


def test_the_two_corners_are_named_in_dat_coordinates():
    """The `.dat` cell is one row and one column on from the bitstream tile."""
    assert (109, 168) in anchor.ADCLRC_DAT_CELLS      # tile (108, 167)
    assert (109, 181) in anchor.ADCLRC_DAT_CELLS      # tile (108, 180)
    assert (2, 2) in anchor.ADCULC_DAT_CELLS          # tile (1, 1)


def test_the_role_patterns_do_not_overlap():
    for name in ("A0", "B3", "CLK0", "CE1", "LSR0", "SEL2"):
        assert anchor.INPUT_WIRE_RE.fullmatch(name)
        assert not anchor.OUTPUT_WIRE_RE.fullmatch(name)
    for name in ("F5", "Q0", "OF7"):
        assert anchor.OUTPUT_WIRE_RE.fullmatch(name)
        assert not anchor.INPUT_WIRE_RE.fullmatch(name)
