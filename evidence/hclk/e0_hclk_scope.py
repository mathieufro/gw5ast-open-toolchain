"""P1.T08d -- E0/E1 for a CLKDIV design, scoped to the HCLK block tiles and the
central clock mux (spine) cells.

Scope: the six HCLK block cells (chipdb._gw5a_hclk_locs) plus the two clock-mux
cells (54,88) and (54,93) that carry .fse table 38.  Tiles are (x, y) = (col,
row), which is how equiv.Cell addresses them.

    python e0_hclk_scope.py --vendor <run.fs> --open <top.fs>
"""
import argparse, os, sys, types

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import equiv  # noqa: E402
from apycula import chipdb as _chipdb       # noqa: E402

MUX_CELLS = [(88, 54), (93, 54)]


def scope():
    tiles = [(c, r) for r, c in _chipdb._gw5a_hclk_locs['GW5AST-138C'].values()]
    return types.SimpleNamespace(tiles=tiles + MUX_CELLS,
                                 include_bel_attrs=True, include_port_nets=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendor", required=True)
    ap.add_argument("--open", dest="open_", required=True)
    a = ap.parse_args()
    db = equiv.load_db()
    sc = scope()
    v = equiv.unpack_netlist(a.vendor, db=db)
    o = equiv.unpack_netlist(a.open_, db=db)
    for tag, nl in (("vendor", v), ("open", o)):
        cells = sorted((c for c in nl.cells if equiv.in_scope(c, sc)),
                       key=lambda c: (c.y, c.x, c.z))
        print(f"{tag} in-scope cells: {[(c.x, c.y, c.z, c.type) for c in cells]}")
    r = equiv.compare_e0(v, o, scope=sc)
    dc = r.diff_count
    print(f"DIFF_COUNT cells={dc['cells']} attrs={dc['attrs']} "
          f"conns={dc['conns']} pips={dc['pips']}")
    print(f"FIRST_DIFF {r.first_diff}")
    print(f"PER_TILE {r.per_tile}")

    # Scoped raw residual: fuse bits that moved inside the scope tiles.  The
    # E0 sets can match while bits still differ (D35 sec 5.1b), so this is
    # reported, never inferred from the sets.
    from fuzz.gw5ast138c.harness import attribute
    tv = attribute.load_tile_bitmaps(a.vendor, db=db)
    to = attribute.load_tile_bitmaps(a.open_, db=db)
    keep = set(sc.tiles)
    tv = {k: val for k, val in tv.items() if k in keep}
    to = {k: val for k, val in to.items() if k in keep}
    deltas = attribute.diff_tile_bitmaps(tv, to)
    per = {}
    for d in deltas:
        per[(d.tile_x, d.tile_y)] = per.get((d.tile_x, d.tile_y), 0) + 1
    print(f"RESIDUAL_UNEXPLAINED bits={len(deltas)} tiles={dict(sorted(per.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
