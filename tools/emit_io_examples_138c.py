#!/usr/bin/env python3
"""Write the phase's IO/IOLOGIC examples from the shapes that measured them.

`DONE-STD` clause (d) asks each closed primitive for a `tangmega138k` example
that builds through the open flow.  The design that proves a row is the one
the row was measured on, so the examples are *generated from the shape files*
rather than written a second time by hand: the `.v` and `.cst` a target builds
are byte-identical to the ones the vendor comparison used, and a shape that
changes moves its example with it.

    python -m tools.emit_io_examples_138c --out $FL/apicula/examples/gw5a
"""
import argparse
import os
import sys

#: `(example base name, shape module, sweep point)`.  One entry per primitive
#: that closed at `E1`; a row that closed `refused` carries its error-text
#: unit test instead of an example.
EXAMPLES = (
    ("oddr-io", "io_basic", "oddr-default"),
    ("iddr-io", "io_basic", "iddr-default"),
    ("oser4-io", "io_ser", "oser4-default"),
    ("oser8-io", "io_ser", "oser8-default"),
    ("oser10-io", "io_ser", "oser10-default"),
    ("ovideo-io", "io_ser", "ovideo-default"),
    ("ides4-io", "io_des", "ides4-reset-pad"),
    ("ides8-io", "io_des", "ides8-reset-pad"),
    ("ides10-io", "io_des", "ides10-reset-pad"),
    ("oser16-io", "io_ser16", "oser16-default"),
    ("ides16-io", "io_des16_balls", "ides16-balls"),
    ("tlvds-ibuf-io", "diff_io", "tlvds-ibuf"),
    ("tlvds-obuf-io", "diff_io", "tlvds-obuf"),
    ("tlvds-tbuf-io", "diff_io", "tlvds-tbuf"),
    ("tlvds-iobuf-io", "diff_io_iobuf", "tlvds-iobuf"),
    ("iodelay-static-io", "iodelay_a_iddr", "c-static-dly-128"),
    ("adclrc-io", "adc_osc", "adclrc-temp"),
)

BOARD = "tangmega138k"


def emit(out_dir, examples=EXAMPLES):
    """Write `<name>.v` and `<name>-tangmega138k.cst`; return the names."""
    from fuzz.gw5ast138c.harness import gen

    written = []
    for name, shape, point in examples:
        spec = gen.load_shape(shape)
        verilog = gen.render_verilog(spec, point)
        cst = gen.render_cst(spec, point, with_ins_loc=True)
        with open(os.path.join(out_dir, f"{name}.v"), "w",
                  encoding="utf-8") as fh:
            fh.write(verilog)
        with open(os.path.join(out_dir, f"{name}-{BOARD}.cst"), "w",
                  encoding="utf-8") as fh:
            fh.write(cst)
        written.append(name)
    return written


def makefile_targets(names=None):
    """The `tangmega138k:` prerequisites these examples add."""
    names = names or [n for n, _, _ in EXAMPLES]
    return [f"{n}-{BOARD}.fs" for n in names]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="emit_io_examples_138c")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    for name in emit(args.out):
        print(f"wrote {name}.v {name}-{BOARD}.cst")
    return 0


if __name__ == "__main__":
    sys.exit(main())
