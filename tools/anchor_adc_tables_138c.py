#!/usr/bin/env python3
"""Anchor the GW5AST-138C's ADC `.dat` port tables, or say why one cannot be.

The 138C has two ADC blocks and the vendor builds both (`P3.T28`/`P3.T29`, four
runs, `gw_sh` exit 0). What blocks a bel is the port map: the die's own
`AdcLRC*`/`AdcULC*` tables read at their declared bases give zeros and ASCII,
i.e. the base has drifted between IDE releases exactly as `Ae350SocIns`' and
`CibFabricNode`'s did. A bel built from a mis-based table is worse than no bel:
`nextpnr` binds it and then fails in the router on a wire that was never the
port's (`D30`).

This tool locates a table instead of addressing it, the way
`dat_parser.read_ae350_soc_ins` does, and then does something that plausibility
alone cannot: it **checks the candidate against the vendor's own ADC
bitstreams**. A record is only believed if the wire it names is one the vendor's
routing actually drives, in the cell the record names.

Three filters locate; one measurement decides.

1. every live record lies in a cell the bitstream diffs put the block in;
2. every live record names a wire of the right *role* -- a block input is a pip
   destination (`A`-`D`, `CLK`, `CE`, `LSR`, `SEL`), a block output a wire
   nothing else in the tile drives (`F`, `Q`, `OF`);
3. no wire is named twice: a second port cannot share a tap.

Usage::

    python3 tools/anchor_adc_tables_138c.py            # print the verdict
    python3 tools/anchor_adc_tables_138c.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

#: `(row, col)` of every tile the ADC bitstream diffs move, in `.dat`
#: coordinates -- the `.dat` names a cell one row and one column further on
#: than the bitstream tile grid does, which is what makes column 168 below the
#: same cell as the `VSENCTL` diff's tile (108, 167).
ADCLRC_DAT_CELLS = frozenset({(109, 168), (109, 169), (109, 180), (109, 181)})
ADCULC_DAT_CELLS = frozenset({(1, 1), (2, 1), (2, 2), (1, 2)})

#: Wire-name shapes, by the role a wire can play for a hard block.
INPUT_WIRE_RE = re.compile(r"(?:[A-D]\d|CLK\d|CE\d|LSR\d|SEL\d)")
OUTPUT_WIRE_RE = re.compile(r"(?:F|Q|OF)\d")

#: `(slots, record width)` of the two table shapes the ADC declares.
LRC_OUT_SLOTS = 0x12
LRC_IN_SLOTS = 0x28


def load_words(gowinhome, device="GW5AST-138C"):
    """The 5-series table block of the installed `.dat`, as u16 words."""
    from apycula import dat_parser

    dat = dat_parser.Datfile(
        pathlib.Path(gowinhome) / "IDE/share/device" / device / f"{device}.dat")
    return dat, dat._rs_words()


def windows(words, wirenames, slots, cells, wire_re, min_live):
    """Every window of `slots` records that passes the three filters."""
    found = []
    for base in range(0, len(words) - 3 * slots + 1):
        live, absent, ok = [], 0, True
        for k in range(slots):
            row, col, wire = words[base + 3 * k: base + 3 * k + 3]
            if (row, col, wire) == (0xffff, 0xffff, 0xffff):
                absent += 1
                continue
            name = wirenames.get(wire)
            if (row, col) in cells and name and wire_re.fullmatch(name):
                live.append((row, col, name))
            else:
                ok = False
                break
        if ok and len(live) >= min_live and len(set(live)) == len(live):
            found.append({"base": base, "live": live, "absent": absent})
    return found


def measured_wires(fs_paths, device="GW5AST-138C"):
    """`{(dat_row, dat_col): {wire, ...}}` the vendor's ADC routing drives.

    A tile whose type occurs elsewhere on the die is compared against a distant
    tile of the same type, so the background every tile carries is subtracted
    and only the ADC's own routing is left. A tile whose type is unique to the
    corner has no such twin and contributes nothing rather than everything.
    """
    from apycula import chipdb as C
    from apycula.bslib import read_bitstream
    from apycula.chipdb import load_chipdb
    from apycula.gowin_unpack import parse_tile_
    import importlib.resources

    with importlib.resources.path("apycula", f"{device}.msgpack.xz") as path:
        db = load_chipdb(path)

    tiles = sorted({(r - 1, c - 1) for r, c in ADCLRC_DAT_CELLS}
                   | {(r - 1, c - 1) for r, c in ADCULC_DAT_CELLS})
    out = {}
    for fs in fs_paths:
        bitmap, _h, _f, _s = read_bitstream(fs)
        bm = C.tile_bitmap(db, bitmap, empty=True)
        for row, col in tiles:
            if (row, col) not in bm:
                continue
            ttyp = db[row, col].ttyp
            twin = next(((r, c) for r in range(db.rows) for c in range(db.cols)
                         if db[r, c].ttyp == ttyp and abs(c - col) > 40
                         and (r, c) in bm), None)
            if twin is None:
                continue
            _b, pips, _cp = parse_tile_(db, row, col, bm[row, col], bm=bm)
            _b2, bg, _cp2 = parse_tile_(db, twin[0], twin[1], bm[twin], bm=bm)
            distinct = {dst for dst, src in pips.items() if bg.get(dst) != src}
            out.setdefault((row + 1, col + 1), set()).update(distinct)
    return out


def confirm(window, measured):
    """How many of a window's live records the vendor's routing confirms."""
    seen = [(r, c, w) for r, c, w in window["live"] if (r, c) in measured]
    hit = [rec for rec in seen if rec[2] in measured[(rec[0], rec[1])]]
    return len(hit), len(seen)


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

    from apycula.wirenames import wirenames_5ast138c as wirenames

    _dat, words = load_words(args.gowinhome)
    runs = sorted(glob.glob(args.adc_runs)) if args.adc_runs else []
    measured = measured_wires(runs) if runs else {}

    report = {"measured_cells": {f"{r},{c}": sorted(w)
                                 for (r, c), w in measured.items()},
              "candidates": []}
    for tag, slots, cells, wire_re, min_live in (
            ("AdcLRC 0x12 (input-role wires)", LRC_OUT_SLOTS,
             ADCLRC_DAT_CELLS, INPUT_WIRE_RE, 15),
            ("AdcLRC 0x28 (output-role wires)", LRC_IN_SLOTS,
             ADCLRC_DAT_CELLS, OUTPUT_WIRE_RE, 15),
            ("AdcULC 0x12 (input-role wires)", LRC_OUT_SLOTS,
             ADCULC_DAT_CELLS, INPUT_WIRE_RE, 12),
    ):
        for win in windows(words, wirenames, slots, cells, wire_re, min_live):
            hit, seen = confirm(win, measured)
            report["candidates"].append({
                "table": tag,
                "base_words": win["base"],
                "live": len(win["live"]),
                "absent": win["absent"],
                "confirmed": hit,
                "checkable": seen,
                "records": win["live"],
            })
    if args.json:
        json.dump(report, sys.stdout, indent=1, sort_keys=True)
        return 0
    for cand in sorted(report["candidates"],
                       key=lambda c: (-c["confirmed"], c["base_words"])):
        print("%-34s base 0x%x live=%2d absent=%d confirmed %d/%d"
              % (cand["table"], cand["base_words"], cand["live"],
                 cand["absent"], cand["confirmed"], cand["checkable"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
