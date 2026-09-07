"""The Phase-2 gate file records its four `V` steps before it records a verdict.

`blueprints/P2-ae350.md` §5 ends by grepping one `PHASE2-GATE:` line, which on
its own is a claim with nothing under it. `F16` made the gate depend on the
budget box and the dual-purpose namespace tests as well as on `V14`/`V18`, so
the file has to name all four and the verdict has to be singular: a second line
would mean two runs disagreed and neither was retired.
"""
import os
import re

OTC_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASE_GATE_MD = os.path.join(OTC_ROOT, "evidence", "ae350", "phase-gate.md")

VERDICT_RE = re.compile(r"^PHASE2-GATE: (pass|fail)$", re.MULTILINE)
#: The four steps `F16` requires the gate to have run.
REQUIRED_STEPS = ("V18", "V14", "V20", "D50")


def _text():
    with open(PHASE_GATE_MD, encoding="utf-8") as handle:
        return handle.read()


def test_phase_gate_records_four_v_steps():
    text = _text()
    for step in REQUIRED_STEPS:
        assert f"`{step}`" in text, f"the gate does not record {step}"


def test_phase_gate_verdict_is_present_exactly_once():
    assert len(VERDICT_RE.findall(_text())) == 1


def test_phase_gate_passes_only_with_every_step_recorded():
    """A `pass` verdict may not stand on a file that names fewer than four steps."""
    text = _text()
    if VERDICT_RE.search(text).group(1) == "pass":
        assert all(f"`{step}`" in text for step in REQUIRED_STEPS)
