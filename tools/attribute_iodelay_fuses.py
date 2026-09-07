#!/usr/bin/env python3
"""Which fuses an `IODELAY`'s `C_STATIC_DLY` moves on the GW5AST-138C (`P3.T21`).

The sweep's vendor bitstreams are the measurement; this reads them back and
says, per sweep point, which bits of the scoped IO tile are set and which
IOLOGIC attribute the shipped table resolves them to.  The baseline is the
sweep's own baseline point, never an empty design, so a moved bit is the
attribute's and not the design's.

    python -m tools.attribute_iodelay_fuses --rows evidence/iodelay/runs.jsonl \
        --tile 52,108 --half A
"""
import argparse
import json
import sys


def tile_bits(db, bitmap, row, col):
    """`{(bit_row, bit_col)}` set in one tile of a decoded bitstream."""
    from apycula import chipdb as _chipdb
    tiles = _chipdb.tile_bitmap(db, bitmap)
    tile = tiles.get((row, col))
    if tile is None:
        return set(), None
    bits = {(r, c) for r, line in enumerate(tile)
            for c, bit in enumerate(line) if bit}
    return bits, tile


def decoded_attrs(db, tile, row, col, half):
    from apycula import attrids, gowin_unpack as gu
    tiledata = db[row, col]
    table = db.shortval[tiledata.ttyp].get(f'IOLOGIC{half}')
    if table is None:
        return {}
    vals = gu.parse_attrvals(tile, db.rev_logicinfo('IOLOGIC'), table,
                             attrids.iologic_attrids, "IOLOGIC")
    return {k: (v, attrids.iologic_num2val.get(v)) for k, v in vals.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="attribute_iodelay_fuses")
    parser.add_argument("--rows", required=True)
    parser.add_argument("--tile", required=True, help="<x>,<y> of the scoped IO cell")
    parser.add_argument("--half", default="A", choices=("A", "B"))
    parser.add_argument("--baseline", default=None,
                        help="sweep value of the baseline point (default: the first row)")
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args(argv)

    from apycula.bslib import read_bitstream
    from fuzz.gw5ast138c.harness import equiv

    x, y = (int(v) for v in args.tile.split(","))
    db = equiv.load_db(equiv.DEVICE)

    rows = [json.loads(l) for l in open(args.rows, encoding="utf-8") if l.strip()]
    out = []
    for r in rows:
        entries = r.get("vendor_fs") or []
        if not entries:
            continue
        bitmap, _h, _f, _s = read_bitstream(entries[0]["path"])
        bits, tile = tile_bits(db, bitmap, y, x)
        out.append({
            "run_id": r["run_id"],
            "point": list(r["sweep"].values())[0],
            "bits": sorted(bits),
            "attrs": decoded_attrs(db, tile, y, x, args.half) if tile is not None else {},
        })

    if not out:
        raise SystemExit("no row carried a vendor bitstream")
    base = out[0]
    if args.baseline is not None:
        base = next(o for o in out if o["point"] == args.baseline)
    base_bits = set(map(tuple, base["bits"]))

    print(f"baseline: {base['point']} ({len(base_bits)} bits set in tile {x},{y})")
    print(f"{'point':<24} {'+bits':<28} {'-bits':<28} attrs that differ")
    for o in out:
        bits = set(map(tuple, o["bits"]))
        added = sorted(bits - base_bits)
        removed = sorted(base_bits - bits)
        diff_attrs = {k: v for k, v in o["attrs"].items()
                      if base["attrs"].get(k) != v}
        print(f"{o['point']:<24} {str(added):<28} {str(removed):<28} {diff_attrs}")
        o["added"], o["removed"] = added, removed

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"tile": [x, y], "half": args.half,
                       "baseline": base["point"], "points": out}, fh, indent=1)
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
