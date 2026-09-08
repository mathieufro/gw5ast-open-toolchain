#!/usr/bin/env python3
"""Report the GW5AST-138C's anchored ADC port tables, and check them.

`P3.T28`/`P3.T28a` could not anchor these tables, and `P3.T28a`'s search was
wrong in a way worth stating: it looked for the block's *inputs* among the
`A`-`D`/`CLK` wires and its *outputs* among `F`/`Q`/`OF`, which is the
direction backwards. The chipdb's own hard-block portmaps settle it -- `BSRAM`
reads `AD*` off `C0`-`C7` and drives `DO*` onto `F0`-`F5`/`Q0`-`Q5`, `ALU`
reads `I0` off `A0` and drives `SUM` onto `F0` -- so a block *input* is an
`A`-`D`/`CLK`/`CE`/`LSR` wire and a block *output* an `F`/`Q`/`OF` wire.

With the direction right, `apycula.dat_parser.Datfile.locate_adc_tables`
locates both blocks by the ADC's own port-group geometry, which fixes the
phase as well as the region, and this tool holds the result against the vendor
ADC bitstreams already on disk: the cell an output table names must be a cell
the vendor's routing shows the block driving, and only in the run that
instantiates that block.

Usage::

    python3 tools/anchor_adc_tables_138c.py --adc-runs '<dir>/*/run/impl/pnr/run.fs'
    python3 tools/anchor_adc_tables_138c.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

#: The wires an ADC's `ADCVALUE[13:0]` occupies in the cell its output table
#: names -- one cell, fourteen wires, in this order.
VALUE_WIRES = tuple(["F%d" % i for i in range(6)]
                    + ["OF%d" % i for i in range(8)])


def locate(gowinhome, device="GW5AST-138C"):
    """Both ADC port tables, located by `apycula`'s own anchor."""
    from apycula import dat_parser
    from apycula.wirenames import wirenames_5ast138c

    path = (pathlib.Path(gowinhome) / "IDE/share/device" / device
            / f"{device}.dat")
    return dat_parser.Datfile(path).locate_adc_tables(wirenames_5ast138c)


def driven_wires(fs_path, cells, device="GW5AST-138C"):
    """`{(row, col): {wire, ...}}` a bitstream shows driven in `cells`.

    Only wires that appear as a pip *source* count: a hard block's output is
    the one thing in a corner cell that a design with no logic there can drive.
    """
    import importlib.resources

    from apycula import chipdb as C
    from apycula.bslib import read_bitstream
    from apycula.chipdb import load_chipdb
    from apycula.gowin_unpack import parse_tile_

    with importlib.resources.path("apycula", f"{device}.msgpack.xz") as path:
        db = load_chipdb(path)
    bitmap, _hdr, _ftr, _syn = read_bitstream(fs_path)
    bm = C.tile_bitmap(db, bitmap, empty=True)
    out = {}
    for row, col in cells:
        if (row, col) not in bm:
            continue
        _bels, pips, _clk = parse_tile_(db, row, col, bm[row, col], bm=bm)
        out[(row, col)] = set(pips.values())
    return out


#: Directory names the vendor's own tree adds below a run's own directory.
_RUN_TREE = ("run", "impl", "pnr")


def run_id(fs_path):
    """The run's own directory name, above the vendor's `run/impl/pnr`."""
    parts = pathlib.Path(fs_path).parent.parts
    while parts and parts[-1] in _RUN_TREE:
        parts = parts[:-1]
    return parts[-1] if parts else fs_path


def confirm(blocks, runs):
    """For each block, how many of its `ADCVALUE` wires each run drives."""
    report = []
    for block in blocks:
        value = [block["outputs"][f"ADCVALUE{i}"] for i in range(14)]
        cell = (value[0][0] - 1, value[0][1] - 1)
        wires = {wire for _row, _col, wire in value}
        row = {"ins_base": block["ins_base"], "outs_base": block["outs_base"],
               "clk": list(block["inputs"]["CLK"]), "value_cell": list(cell),
               "runs": {}}
        for path in runs:
            driven = driven_wires(path, [cell]).get(cell, set())
            row["runs"][run_id(path)] = len(wires & driven)
        report.append(row)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="anchor_adc_tables_138c")
    parser.add_argument("--gowinhome", default=os.environ.get("GOWINHOME"))
    parser.add_argument("--adc-runs", default=None,
                        help="glob of vendor ADC run.fs files")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.gowinhome:
        raise SystemExit("no GOWINHOME: the .dat this anchors is the IDE's")

    import glob

    blocks = locate(args.gowinhome)
    runs = sorted(glob.glob(args.adc_runs)) if args.adc_runs else []
    report = confirm(blocks, runs)
    if args.json:
        json.dump(report, sys.stdout, indent=1, sort_keys=True)
        return 0
    for row in report:
        print("Ins 0x%05x  Outs 0x%05x  CLK %s  ADCVALUE cell %s"
              % (row["ins_base"], row["outs_base"], tuple(row["clk"]),
                 tuple(row["value_cell"])))
        for name, hit in sorted(row["runs"].items()):
            print("    %-28s %2d/14 ADCVALUE wires driven" % (name, hit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
