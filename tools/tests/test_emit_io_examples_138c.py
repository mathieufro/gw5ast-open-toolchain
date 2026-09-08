"""The examples are generated from the shapes, so they cannot drift from them.

`DONE-STD` clause (d) wants a buildable example per closed primitive.  Writing
those designs a second time by hand would make the example and the evidence
row two different things that only look alike; these guards pin that they are
one thing.
"""
import os

import pytest

from tools import emit_io_examples_138c as emit


def test_every_example_names_a_shape_that_exists():
    """A target whose shape is gone would fail only at build time."""
    gen = pytest.importorskip("fuzz.gw5ast138c.harness.gen")
    for name, shape, point in emit.EXAMPLES:
        spec = gen.load_shape(shape)
        assert point in spec.sweep_values, (name, shape, point)


def test_example_names_are_unique():
    names = [name for name, _, _ in emit.EXAMPLES]
    assert len(names) == len(set(names))


def test_emitted_files_match_the_shape_render(tmp_path):
    """The written `.v` is the shape's own render, byte for byte."""
    gen = pytest.importorskip("fuzz.gw5ast138c.harness.gen")
    written = emit.emit(str(tmp_path), examples=emit.EXAMPLES[:1])
    name, shape, point = emit.EXAMPLES[0]
    assert written == [name]
    spec = gen.load_shape(shape)
    with open(tmp_path / f"{name}.v", encoding="utf-8") as fh:
        assert fh.read() == gen.render_verilog(spec, point)
    with open(tmp_path / f"{name}-tangmega138k.cst", encoding="utf-8") as fh:
        assert fh.read() == gen.render_cst(spec, point, with_ins_loc=True)


def test_makefile_targets_are_board_suffixed():
    assert all(t.endswith("-tangmega138k.fs")
               for t in emit.makefile_targets())
