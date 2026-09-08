"""A shape's `primitive` is a join key, not a label.

`check_evidence.py` matches an evidence row to its `spec-primitives.md` row by
comparing `row["primitive"]` to the table's row id.  A shape that spells the
same primitive differently therefore produces rows the table reads as absent
-- a BLANK finding on a row that is in fact fully measured, which is a silent
false negative in the one instrument that decides whether a row closed.  Three
shapes drifted that way before this guard existed.
"""
import os

import pytest

from tools import check_evidence, paths

#: Shapes that measure the harness rather than a primitive, so no row of the
#: table is theirs to join to.  `smoke` is the oracle's own reference design
#: (`evidence/oracle-smoke/`), which exists to prove the two flows run at all.
NOT_A_PRIMITIVE = ("smoke",)


def _row_ids():
    spec = paths.default_spec_primitives()
    if not spec or not os.path.isfile(spec):
        pytest.skip("no spec-primitives.md reachable from this checkout")
    return {row.id for row in check_evidence.parse_spec_primitives(spec)}


def _shape_names(gen):
    import fuzz.gw5ast138c.shapes as shapes
    directory = os.path.dirname(shapes.__file__)
    return sorted(name[:-3] for name in os.listdir(directory)
                  if name.endswith(".py") and not name.startswith("_"))


def test_every_shape_primitive_is_a_table_row_id():
    gen = pytest.importorskip("fuzz.gw5ast138c.harness.gen")
    ids = _row_ids()
    unjoined = {}
    for name in _shape_names(gen):
        if name in NOT_A_PRIMITIVE:
            continue
        try:
            spec = gen.load_shape(name)
        except (ImportError, AttributeError):
            continue
        primitive = getattr(spec, "primitive", None)
        if primitive and primitive not in ids:
            unjoined[name] = primitive
    assert unjoined == {}, (
        "these shapes write evidence rows no spec-primitives.md row can "
        f"match: {unjoined}")
