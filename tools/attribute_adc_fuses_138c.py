#!/usr/bin/env python3
"""What an `ADCLRC`'s parameters and ports actually move on the GW5AST-138C.

This die's `.fse` declares no `ADC` `logicinfo`/`shortval` pair, so the bits an
ADC design moves land in tables the parser could only name by index --
`unknown_136`, `unknown_137`, `unknown_138`.  The question a sweep answers is
not "which bits move" (a diff gives that) but **what owns each moved bit**, and
there are only three possible owners: a pip, a shortval entry, or nothing yet
attributed.  Classifying them is what separates a parameter that needs a fuse
from a port that is simply routed.

The sweep behind this tool builds every value of `VSENCTL` (eight) and every
value of `DIV_CTL` (four).  Completeness is not thoroughness for its own sake:
a shortval entry is `code -> bits`, so a code is identified by the bits it
moves, and a parameter is decoded only once every one of its values has been
built.

    python -m tools.attribute_adc_fuses_138c --rows $OTC/evidence/adc/runs.jsonl
"""
import argparse
import json
import sys

#: Sweep point -> `(parameter, value)`.  The baseline carries the value every
#: other point is diffed against, so it names both axes' zero.
POINTS = {
    "adclrc-temp": (("VSENCTL", 1), ("DIV_CTL", 0)),
    "adclrc-vsen0": (("VSENCTL", 0),),
    "adclrc-vdd09": (("VSENCTL", 2),),
    "adclrc-vsen3": (("VSENCTL", 3),),
    "adclrc-vsen4": (("VSENCTL", 4),),
    "adclrc-vsen5": (("VSENCTL", 5),),
    "adclrc-vsen6": (("VSENCTL", 6),),
    "adclrc-vsen7": (("VSENCTL", 7),),
    "adclrc-divctl1": (("DIV_CTL", 1),),
    "adclrc-divctl2": (("DIV_CTL", 2),),
    "adclrc-divctl3": (("DIV_CTL", 3),),
}

BASELINE = "adclrc-temp"

#: The three cells the `P3.T29` diffs put the block's configuration in.
DEFAULT_TILES = ((108, 167), (108, 180), (108, 181))


def tile_bits(db, bitmap, row, col):
    """`{(bit_row, bit_col)}` set in one tile of a decoded bitstream."""
    from apycula import chipdb as _chipdb
    tile = _chipdb.tile_bitmap(db, bitmap).get((row, col))
    if tile is None:
        return set()
    return {(r, c) for r, line in enumerate(tile)
            for c, bit in enumerate(line) if bit}


def read_points(rows_path, points=POINTS):
    """`{sweep point: vendor .fs path}` for every point this tool knows."""
    out = {}
    for line in open(rows_path, encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        point = (row.get("sweep") or {}).get("POINT")
        entries = row.get("vendor_fs") or []
        if point in points and entries:
            out[point] = entries[0]["path"]
    return out


def measure(db, paths, tiles):
    """`{point: {tile: bits}}` -- the raw per-tile bit sets."""
    from apycula.bslib import read_bitstream
    out = {}
    for point, path in sorted(paths.items()):
        bitmap, *_ = read_bitstream(path)
        out[point] = {t: tile_bits(db, bitmap, *t) for t in tiles}
    return out


def pip_bits(db, row, col):
    """Every bit any pip of one cell can claim."""
    tiledata = db[row, col]
    claimed = set()
    for table in (tiledata.pips, getattr(tiledata, "clock_pips", {})):
        for srcs in table.values():
            for fuses in srcs.values():
                claimed.update(map(tuple, fuses))
    return claimed


def shortval_entries(db, row, col):
    """`{(table, key): bits}` for the cell's unattributed tables."""
    ttyp = db[row, col].ttyp
    return {(name, key): set(map(tuple, fuses))
            for name, table in db.shortval.get(ttyp, {}).items()
            if name.startswith("unknown_")
            for key, fuses in table.items() if fuses}


def classify(db, measured, baseline=BASELINE):
    """One record per (point, tile) naming what owns the bits that moved."""
    base = measured[baseline]
    out = []
    for point, tiles in sorted(measured.items()):
        if point == baseline:
            continue
        for tile, bits in sorted(tiles.items()):
            moved = bits ^ base[tile]
            if not moved:
                continue
            pips = pip_bits(db, *tile)
            candidates = {k: v for k, v in shortval_entries(db, *tile).items()
                          if v <= bits and v & moved}
            # One value's fuses can be a proper subset of another's -- the two
            # low bits of `DIV_CTL` give 1 ⊂ 2 ⊃ 3 -- so an entry that only
            # explains part of what moved is not the entry that was written.
            entries = {k: v for k, v in candidates.items()
                       if not any(v < other for other in candidates.values())}
            owned = set(pips)
            for fuses in entries.values():
                owned |= fuses
            out.append({
                "point": point,
                "tile": tile,
                "moved": len(moved),
                "routing": len(moved & pips),
                "entries": sorted(entries),
                "unattributed": sorted(moved - owned),
            })
    return out


def div_ctl_codes(records, points=POINTS):
    """`{DIV_CTL value: (table, key)}` for every value one entry explains."""
    axis = {value: point for point, pairs in points.items()
            for parm, value in pairs if parm == "DIV_CTL"}
    out = {}
    for record in records:
        for value, point in axis.items():
            if record["point"] != point or len(record["entries"]) != 2:
                continue
            if record["unattributed"] or record["routing"]:
                continue
            out[value] = record["entries"]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="attribute_adc_fuses_138c")
    parser.add_argument("--rows", required=True)
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args(argv)

    from fuzz.gw5ast138c.harness import equiv

    db = equiv.load_db(equiv.DEVICE)
    paths = read_points(args.rows)
    missing = sorted(set(POINTS) - set(paths))
    if missing:
        print(f"INCOMPLETE-AXIS: no vendor bitstream for {missing}")
        return 1

    records = classify(db, measure(db, paths, DEFAULT_TILES))
    for record in records:
        print("%-16s %-11s moved=%-4d routing=%-4d entries=%s%s"
              % (record["point"], record["tile"], record["moved"],
                 record["routing"], record["entries"] or "-",
                 "" if not record["unattributed"]
                 else f" UNATTRIBUTED={record['unattributed']}"))
    codes = div_ctl_codes(records)
    for value, entries in sorted(codes.items()):
        print(f"DIV_CTL={value} -> {entries}")
    print(f"ADC-ATTRIBUTION DIV_CTL {len(codes)}/3 non-default values resolved")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"records": [dict(r, tile=list(r["tile"]),
                                        entries=[list(e) for e in r["entries"]])
                                   for r in records],
                       "div_ctl": {str(v): [list(e) for e in entries]
                                   for v, entries in codes.items()}},
                      fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
