"""`evidence/ae350/fuse-set-138c.md` carries the settled fuse count in one line.

`S19` asks for the `AE350_SOC` fuse set to be either zero or enumerated, and
`blueprints/P2-ae350.md` §5 reads the answer off a single machine-readable
line so that neither a reader nor a checker has to parse the prose around it.
The count and the enumerated rows have to agree: a non-zero count without that
many bit rows is a claim with no evidence under it, and bit rows under a zero
count are a set that was never retired.
"""
import os
import re

OTC_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUSE_SET_MD = os.path.join(OTC_ROOT, "evidence", "ae350", "fuse-set-138c.md")

MARKER_RE = re.compile(r"^AE350-FUSE-SET: (\d+) bits$", re.MULTILINE)
#: One enumerated bit of a non-zero set: `- (row, col) bit <n>`.
BIT_ROW_RE = re.compile(r"^- \(\d+, \d+\) bit \d+$", re.MULTILINE)


def _text():
    with open(FUSE_SET_MD, encoding="utf-8") as handle:
        return handle.read()


def test_fuse_set_marker_is_present_exactly_once():
    assert len(MARKER_RE.findall(_text())) == 1


def test_fuse_set_rows_match_count():
    text = _text()
    count = int(MARKER_RE.search(text).group(1))
    assert len(BIT_ROW_RE.findall(text)) == count


def test_fuse_set_marker_agrees_with_the_prose_verdict():
    text = _text()
    count = int(MARKER_RE.search(text).group(1))
    zero_verdict = "FUSE-SET-VERDICT: **zero, measured**" in text
    assert zero_verdict == (count == 0)
