#!/usr/bin/env python3
"""`P3.T04` -- which GW5AST-138C tile types must be excluded from IOLOGIC.

`fse_iologic` creates an `IOLOGICA`/`IOLOGICB` bel wherever the tile's
`shortval` carries key 21 or 22. On this die 47 tile types do, but only some of
them sit under a pin: the rest would be bels a design can ask for and never
reach. `GW5A-25A` states its own exclusion set as a literal `{48, 51, 263, 392,
399}`; this tool derives the 138C one from the device data instead of copying a
shape.

Two independent criteria are computed and must agree, because a single
criterion is an assumption:

1. **IOB co-residency.** After `chipdb.fill_GW5A_io_bels` consolidates each
   differential pair into one "main" cell, a tile type either carries `IOBA`/
   `IOBB` or it does not. IOLOGIC in a tile with no IOB has no buffer to drive.
2. **Bonded pins.** The pinout of each package this die ships in maps `IO<side>
   <n><A|B>` names onto edge cells. A tile type under no pin of *any* package
   cannot be reached from a `.cst` at all.

Where the two disagree the tool exits non-zero and prints the disagreement --
that is a finding about the device model, not a set to ship.

Usage::

    python tools/derive_iologic_ttyps_138c.py            # print the TSV
    python tools/derive_iologic_ttyps_138c.py -o <path>  # write it
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402

DEVICE = "GW5AST-138C"

#: Every package this die ships in; a pin in any of them makes the tile real.
PACKAGES = ("PBGA484A", "PBGA676A", "FCPBGA676A")

#: `IO<side><index><pin>` -- the vendor's edge-pin naming.
PIN_RE = re.compile(r"IO([TBRL])(\d+)([A-Z])$")

#: Header of `evidence/oddr-iddr/ttyp-adjudication.tsv`.
TSV_HEADER = ("ttyp", "verdict", "gw_sh_log_path", "iologic_cells",
              "iob_bels", "bonded_pins", "example_cell")


def load_db():
    from apycula.gowin_pack import ChipDB
    return ChipDB(DEVICE).db


def edge_lists(db):
    grid = db.grid
    return {"T": grid[0], "B": grid[-1],
            "L": [row[0] for row in grid], "R": [row[-1] for row in grid]}


def bonded_pins_by_ttyp(db):
    """`{ttyp: {pin name}}` over every package -- criterion 2."""
    edges = edge_lists(db)
    out = collections.defaultdict(set)
    for package in PACKAGES:
        pinout = db.pinout.get(DEVICE, {}).get(package, {})
        for _, (name, _cfgs) in pinout.items():
            match = PIN_RE.match(name)
            if not match:
                continue
            side, index, _ab = match.groups()
            out[edges[side][int(index) - 1]].add(name)
    return out


def iologic_ttyps(db):
    """`{ttyp: (cell count, first cell)}` for every tile type carrying IOLOGIC."""
    found = {}
    for row, cols in enumerate(db.grid):
        for col, ttyp in enumerate(cols):
            if any(b.startswith("IOLOGIC") for b in db.tiles[ttyp].bels):
                count, first = found.get(ttyp, (0, (row, col)))
                found[ttyp] = (count + 1, first)
    return found


def adjudicate(db):
    """`(rows, exclusion set)` -- one row per candidate tile type."""
    pins = bonded_pins_by_ttyp(db)
    rows, excluded, disagreements = [], set(), []
    for ttyp, (cells, first) in sorted(iologic_ttyps(db).items()):
        iob = sorted(b for b in db.tiles[ttyp].bels if b.startswith("IOB"))
        bonded = len(pins.get(ttyp, ()))
        if bool(iob) != bool(bonded):
            disagreements.append((ttyp, iob, bonded))
        verdict = "accept" if iob and bonded else "reject"
        if verdict == "reject":
            excluded.add(ttyp)
        rows.append((str(ttyp), verdict, "-", str(cells),
                     ",".join(iob) or "none", str(bonded), str(first)))
    return rows, excluded, disagreements


def render(rows):
    return "\n".join(["\t".join(TSV_HEADER)] + ["\t".join(r) for r in rows]) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", default=None,
                        help="write the TSV here instead of stdout")
    args = parser.parse_args(argv)

    apicula = paths.apicula_root()
    if apicula:
        sys.path.insert(0, apicula)
    rows, excluded, disagreements = adjudicate(load_db())

    text = render(rows)
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)

    print(f"IOLOGIC-TTYP candidates={len(rows)} accept={len(rows) - len(excluded)} "
          f"reject={len(excluded)}", file=sys.stderr)
    print("exclusion set: {" + ", ".join(str(t) for t in sorted(excluded)) + "}",
          file=sys.stderr)
    for ttyp, iob, bonded in disagreements:
        print(f"DISAGREEMENT ttyp={ttyp} iob={iob} bonded_pins={bonded}",
              file=sys.stderr)
    return 1 if disagreements else 0


if __name__ == "__main__":
    sys.exit(main())
