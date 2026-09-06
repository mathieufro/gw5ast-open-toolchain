"""P1.T08d -- decode the GW5AST-138C central clock mux (.fse table 38) out of a
bitstream.

The 138C's HCLK blocks reach the global clock spines through a *central clock
mux* that lives in cells (54,88) and (54,93) (fse ttyp 80 and 85) plus their
neighbours.  Those cells carry `.fse` wire table 38 (`CLOCK_MUX`), which
`fse_clock_pips_138` reads but whose two interesting source bands it discards
(`srcid in range(105,129)` "unknown wires" and `srcid in range(164,237)`
"longwires").

This module answers, for one vendor or open `.fs`: which table-38 rows are lit,
i.e. which clock-network source wire the vendor selected onto which SPINE.  It
is read-only and adds no oracle run of its own.

Usage (from $FL_WT/apicula-wt/<wt>, PYTHONPATH=.):
    python probe_clkmux.py --fs a.fs [--fs b.fs ...] [--json out.json]
"""
import argparse, json, os, pickle, sys

TABLE = 38
DEVICE = "GW5AST-138C"


def load_fse(device=DEVICE, cache=None):
    if cache and os.path.isfile(cache):
        return pickle.load(open(cache, "rb"))
    from apycula import fse_parser
    gw = os.environ["GOWINHOME"]
    with open(f"{gw}/IDE/share/device/{device}/{device}.fse", "rb") as f:
        fse = fse_parser.read_fse(f, device)
    if cache:
        pickle.dump(fse, open(cache, "wb"))
    return fse


def mux_cells(fse):
    """Every (row, col, ttyp) whose .fse tile carries wire table 38."""
    grid = fse["header"]["grid"][61]
    out = []
    for r, row in enumerate(grid):
        for c, t in enumerate(row):
            d = fse.get(t)
            if isinstance(d, dict) and TABLE in d.get("wire", {}):
                out.append((r, c, t))
    return out


def table38_rows(fse, ttyp, device=DEVICE):
    """[(src, dest, frozenset((row,col) fuse bits))] for one ttyp."""
    from apycula import fse_parser
    rows = []
    for srcid, destid, *fuses in fse[ttyp]["wire"][TABLE]:
        fs = [f for f in fuses if f != -1]
        bits = frozenset(fse_parser.fuse_lookup(fse, ttyp, f, device) for f in fs)
        if srcid < 0:
            srcid, bits = -srcid, frozenset()
        rows.append((srcid, destid, bits))
    return rows


def lit_rows(fse, tiles, cells, device=DEVICE):
    """For each mux cell, the table-38 rows whose fuses are ALL set.

    Returns {(row, col): {destid: [(srcid, nbits)]}} keeping only the rows with
    at least one fuse (a fuseless row is a default, never 'lit')."""
    res = {}
    for (r, c, ttyp) in cells:
        entry = tiles.get((c, r))
        if entry is None:
            continue
        _t, bm = entry
        set_bits = {(i, j) for i, rr in enumerate(bm) for j, v in enumerate(rr) if v}
        per = {}
        for srcid, destid, bits in table38_rows(fse, ttyp, device):
            if bits and bits <= set_bits:
                per.setdefault(destid, []).append((srcid, len(bits)))
        if per:
            res[(r, c)] = per
    return res


#: The six HCLK block cells (apicula grid row, col) -- chipdb._gw5a_hclk_locs.
HCLK_LOCS = {0: (27, 0), 1: (27, 181), 2: (81, 0),
             3: (81, 181), 4: (108, 64), 5: (108, 117)}
HCLK_TABLE = 48
#: Block output lane i is HCLK_MUX_BETA0i == table-48 dest 34 + i, fed by
#: L2HCLK0i == src 30 + i (the lane's CLKDIV output).
BETA_DEST = {34: 0, 35: 1, 36: 2, 37: 3}
L2HCLK_SRC = {30: 0, 31: 1, 32: 2, 33: 3}


def lit_hclk_lanes(fse, tiles, device=DEVICE):
    """{block: [lane, ...]} -- lanes whose BETA <= L2HCLK pip is lit."""
    from apycula import fse_parser
    grid = fse["header"]["grid"][61]
    out = {}
    for blk, (r, c) in sorted(HCLK_LOCS.items()):
        entry = tiles.get((c, r))
        if entry is None:
            continue
        _t, bm = entry
        ttyp = grid[r][c]
        set_bits = {(i, j) for i, rr in enumerate(bm) for j, v in enumerate(rr) if v}
        lanes = []
        for srcid, destid, *fuses in fse[ttyp]["wire"][HCLK_TABLE]:
            if srcid < 0 or destid not in BETA_DEST or srcid not in L2HCLK_SRC:
                continue
            if BETA_DEST[destid] != L2HCLK_SRC[srcid]:
                continue
            fs = [f for f in fuses if f != -1]
            bits = {fse_parser.fuse_lookup(fse, ttyp, f, device) for f in fs}
            if bits and bits <= set_bits:
                lanes.append(BETA_DEST[destid])
        if lanes:
            out[blk] = sorted(lanes)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fs", action="append", required=True)
    ap.add_argument("--fse-cache", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--hclk", action="store_true",
                    help="also decode the six HCLK block cells' table 48")
    ap.add_argument("--maximal", action="store_true",
                    help="per dest keep only the src with the most fuses")
    args = ap.parse_args(argv)

    from fuzz.gw5ast138c.harness import attribute
    from fuzz.gw5ast138c.harness.equiv import load_db
    fse = load_fse(cache=args.fse_cache)
    cells = mux_cells(fse)
    db = load_db(DEVICE)
    out = {}
    for path in args.fs:
        tiles = attribute.load_tile_bitmaps(path, db=db)
        res = lit_rows(fse, tiles, cells)
        name = os.path.basename(path)
        out[name] = {}
        for (r, c), per in sorted(res.items()):
            d = {}
            for destid, srcs in sorted(per.items()):
                srcs = sorted(srcs, key=lambda s: (-s[1], s[0]))
                d[destid] = [srcs[0]] if args.maximal else srcs
            out[name][f"{r},{c}"] = d
            print(f"{name} cell ({r},{c}): " +
                  " ".join(f"dest{k}<={[s[0] for s in v]}" for k, v in sorted(d.items())))
        if args.hclk:
            lanes = lit_hclk_lanes(fse, tiles)
            out[name]["hclk_lanes"] = {str(k): v for k, v in lanes.items()}
            print(f"{name} HCLK lanes: {lanes}")
    if args.json:
        json.dump(out, open(args.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
