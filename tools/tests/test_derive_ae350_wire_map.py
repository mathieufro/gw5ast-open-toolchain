"""Tests for `tools/derive_ae350_wire_map.py`.

The derivation exists so that the committed wire map is reproducible from the
vendor `.dat` rather than hand-maintained, and so that it stays an *independent*
reading of those tables from the one `apycula.chipdb` builds. One test per
property that has to hold for either of those to be true.
"""

import ast
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import derive_ae350_wire_map as derive  # noqa: E402
import paths  # noqa: E402

PORT_BITS = 911
BOUND_BITS = 884
#: The fabric grid the consumer builds from the `.fse`; every tap must land on
#: it, though the derivation bounds records by the `.dat`'s own larger grid.
FABRIC_GRID = (109, 182)


@pytest.fixture(scope="module")
def derived():
    """The artefact as derived here and now from the installed `.dat`."""
    sys.path.insert(0, paths.apicula_root())
    if not os.getenv("GOWINHOME"):
        pytest.skip("GOWINHOME is not set")
    if not derive.dat_path().is_file():
        pytest.skip(f"{derive.dat_path()} is absent")
    return derive.derive()


def test_the_committed_artefact_is_what_the_dat_says(derived):
    """The evidence file is the derivation's output, not a stale copy of it."""
    assert derive.render(derived) == derive.WIRE_MAP.read_text()


def test_the_derivation_is_deterministic(derived):
    """Two readings of one `.dat` produce one byte-identical artefact."""
    assert derive.render(derive.derive()) == derive.render(derived)


def test_the_input_map_is_the_fabric_driven_run_of_one_table(derived):
    """The direction rule closes: the run has exactly one record per input bit.

    This is what makes the map a map rather than a guess -- the number of
    records the wire classes select is not free to be anything else.
    """
    inputs = derived["bits"]["inputs"]
    assert len(inputs) == 416
    assert all(e["table"] == "Ae350SocOuts" for e in inputs)
    assert all(e["provenance"] != "UNBOUND" for e in inputs)


def test_the_output_map_is_read_from_both_tables_around_that_run(derived):
    """The output map's middle run comes from the other table, its ends do not."""
    outputs = derived["bits"]["outputs"]
    first, last = (derived["input_run"]["first_slot"],
                   derived["input_run"]["last_slot"])
    for entry in outputs:
        if entry["table"] is None:
            assert first <= entry["bit"] <= last, entry
        elif entry["bit"] < first or entry["bit"] > last:
            assert entry["table"] == "Ae350SocOuts", entry
        else:
            assert entry["table"] == "Ae350SocIns", entry


def test_every_bit_is_accounted_for_exactly_once(derived):
    """911 declared bits, 884 of them bound, and no bit named twice."""
    bits = derived["bits"]
    assert sum(len(v) for v in bits.values()) == PORT_BITS
    bound = [e for entries in bits.values() for e in entries
             if e["provenance"] != "UNBOUND"]
    assert len(bound) == BOUND_BITS == derived["summary"]["bound"]
    for direction, entries in bits.items():
        placed = [(e["row"], e["col"], e["wire"]) for e in entries
                  if e["provenance"] != "UNBOUND"]
        assert len(set(placed)) == len(placed), direction


def test_every_tap_lands_on_the_fabric_grid_the_consumer_builds(derived):
    """A tap outside the `.fse` grid would be a misread table, not a port."""
    rows, cols = FABRIC_GRID
    for entries in derived["bits"].values():
        for entry in entries:
            if entry["provenance"] == "UNBOUND":
                continue
            assert 0 <= entry["row"] < rows, entry
            assert 0 <= entry["col"] < cols, entry


def test_measured_provenance_comes_only_from_the_pip_cross_check(derived):
    """A bit is MEASURED exactly when the vendor bitstream names its tap."""
    taps, _doc = derive.read_pipdiff()
    for entries in derived["bits"].values():
        for entry in entries:
            if entry["provenance"] == "UNBOUND":
                continue
            seen = (entry["row"], entry["col"], entry["wire"]) in taps
            assert seen == (entry["provenance"] == "MEASURED"), entry


def test_the_derivation_never_reads_the_consumer_it_is_checked_against():
    """Importing `chipdb` here would make the reconciliation test tautological."""
    tree = ast.parse(Path(derive.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.update(f"{node.module}.{alias.name}"
                            for alias in node.names)
    assert not any("chipdb" in name for name in imported), imported
