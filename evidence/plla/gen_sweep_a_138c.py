"""`P1.T23` -- attribute batch A's moved fuses and check them against `P1.T22`.

Batch A (`p1-pll-sweep-a`, shape `fuzz/gw5ast138c/shapes/clocking_pll.py`)
sweeps two axes of the GW5AST-138C `PLL` (`D96`), one parameter per run, each
axis with its own baseline:

    IDIV   FCLKIN 400, FBDIV 2, MDIV 14, ODIV0 8, IDIV_SEL  9..17 (base 13)
    FBDIV  FCLKIN 100, IDIV  4, MDIV  2, ODIV0 8, FBDIV_SEL 13..23 (base 18)

For each point the bits that differ from **its own axis baseline**, inside the
three tiles of `PLL_L[0]`, are that parameter's fuses.  Each moved bit is
looked up in its tile's `shortval[35]` table and the positive attrvals of the
matching rows are mapped back through `logicinfo['PLL']` to `(attr_id, value)`
and through `pll_attrids` to a name -- the identical procedure `P1.T22` used,
so the two results are directly comparable.

The `P1.T22` cross-check (`attrmap-138c.json`) is the point of this script: an
`IDIV_SEL` step must move `A_IDIV_SEL` (attr **109**) and an `FBDIV_SEL` step
must move `A_FBDIV_SEL` (attr **110**), both in tile `(27, 1)`, exactly as
`P1.T22` measured -- with the charge-pump co-movers `FLDCOUNT` (16) and
`A_ICP_SEL` (111) allowed, because the vendor recomputes them whenever the VCO
moves (`attrmap-138c.md` §3).  Anything else is a discrepancy, reported.

Usage:
    python gen_sweep_a_138c.py <batch design dir> <rows.jsonl> [<out.json>]
"""
import json
import sys
import importlib.resources as ir
from pathlib import Path

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

#: `PLL_L[0]`, `sites-138c.json` pll_idx 0: row 27, columns 1..3.
SITE = "PLL_L[0]"
SITE_TILES = [(27, 1), (27, 2), (27, 3)]

#: `P1.T22`, `attrmap-138c.md` §4: the attribute each swept parameter must
#: move, and the tile it must move it in.
EXPECTED = {
    "IDIV": ("A_IDIV_SEL", 109, (27, 1)),
    "FBDIV": ("A_FBDIV_SEL", 110, (27, 1)),
}

#: The vendor recomputes the charge-pump / loop-filter attributes from
#: `fref`/`fvco`, so a divider step that also moves these is the expected
#: shape, not a failure (`P1.T22` §3).  This is exactly the tuple
#: `GW5A.get_pll_attrvals` derives from `get_pll_pump` (`gowin_pack.py:5586`):
#: `fclkin_idx` -> `FLDCOUNT` (16) and `KVCO` (28), `icp` -> `A_ICP_SEL` (111),
#: `r_idx` -> `A_LPF_RES_SEL` (112).  `P1.T22`'s twelve points never crossed an
#: `r_idx` threshold, so `A_LPF_RES_SEL` is a `P1.T23` FIRST SIGHTING -- listed
#: here because it is a member of the pump triple by construction, not because
#: the sweep would otherwise disagree.
PUMP_CO_MOVERS = {16: "FLDCOUNT", 28: "KVCO",
                  111: "A_ICP_SEL", 112: "A_LPF_RES_SEL"}


def set_bits(tile):
    """`{(row, col)}` of the bits set in one tile bitmap."""
    if tile is None:
        return set()
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def attribute(db, base_tiles, run_tiles, ttyps):
    """Moved bits per tile, and the attrvals whose shortval rows contain them."""
    moved = {}
    attrvals = set()
    for (row, col), ttyp in zip(SITE_TILES, ttyps):
        base = set_bits(base_tiles.get((row, col)))
        cur = set_bits(run_tiles.get((row, col)))
        delta = base ^ cur
        if not delta:
            continue
        moved[f"{row},{col}"] = {
            "set": sorted(f"{r},{c}" for r, c in cur - base),
            "cleared": sorted(f"{r},{c}" for r, c in base - cur),
        }
        for key, fuses in db.shortval[ttyp].get("PLL", {}).items():
            if delta & set(fuses):
                attrvals.update(a for a in key if a > 0)
    return moved, attrvals


def tiles_of(db, fs_path):
    bitmap, _h, _f, _s = read_bitstream(str(fs_path))
    return tile_bitmap(db, bitmap, empty=True)


def main(argv):
    design_root = Path(argv[1])
    rows_path = Path(argv[2])
    out_path = Path(argv[3]) if len(argv) > 3 else None

    rows = [json.loads(l) for l in rows_path.read_text().splitlines() if l.strip()]
    by_run = {r["run_id"]: r for r in rows}

    db = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))
    ttyps = [db.grid[r][c] for r, c in SITE_TILES]
    inv = {v: k for k, v in db.logicinfo["PLL"].items()}
    id2name = {v: k for k, v in attrids.pll_attrids.items()}

    # The shape is the single source of the axis/value of each point; it is
    # imported from whatever apicula checkout $PYTHONPATH names (the branch
    # worktree that owns the shape), never from a guessed sibling path.
    from fuzz.gw5ast138c.shapes import clocking_pll as shape

    points = shape.points()
    order = list(points)

    result = {
        "task": "P1.T23",
        "device": "GW5AST-138C",
        "batch_id": "p1-pll-sweep-a",
        "site": SITE,
        "site_tiles": [list(t) for t in SITE_TILES],
        "site_ttyps": ttyps,
        "expected_vs_t22": {k: {"name": v[0], "attr_id": v[1],
                                "tile": list(v[2])} for k, v in EXPECTED.items()},
        "runs": [],
    }

    # Per-axis baseline bitmaps.
    baselines = {}
    fs_of = {}
    for idx, point in enumerate(order):
        run_id = f"p1-pll-sweep-a-clocking_pll-{idx:04d}"
        row = by_run.get(run_id)
        if not row or not row.get("vendor_fs"):
            continue
        fs_of[point] = Path(row["vendor_fs"][0]["path"])
    for axis in shape.selected_axes():
        base_point = f"{axis.name.lower()}_{axis.baseline:03d}"
        if base_point in fs_of:
            baselines[axis.name] = tiles_of(db, fs_of[base_point])

    ok = 0
    for idx, point in enumerate(order):
        axis, value = points[point]
        run_id = f"p1-pll-sweep-a-clocking_pll-{idx:04d}"
        if point not in fs_of:
            result["runs"].append({"point": point, "run_id": run_id,
                                   "status": "no vendor .fs"})
            continue
        moved, attrvals = attribute(db, baselines[axis.name],
                                    tiles_of(db, fs_of[point]), ttyps)
        resolved = []
        for av in sorted(attrvals):
            attr_id, val = inv.get(av, (None, None))
            resolved.append({"attrval": av, "attr_id": attr_id, "value": val,
                             "name": id2name.get(attr_id)})
        ids = {r["attr_id"] for r in resolved if r["attr_id"] is not None}
        want_name, want_id, want_tile = EXPECTED[axis.name]
        is_base = value == axis.baseline
        unexpected = sorted(ids - {want_id} - set(PUMP_CO_MOVERS))
        verified = is_base or (want_id in ids and not unexpected)
        if verified:
            ok += 1
        entry = {
            "run_id": run_id,
            "point": point,
            "axis": axis.name,
            "param": axis.param,
            "value": value,
            "baseline": is_base,
            "fvco_mhz": round(axis.fvco(value), 4),
            "fpfd_mhz": round(axis.fpfd(value), 4),
            "clkout0_mhz": round(axis.clkout0(value), 4),
            "expected_attr": want_name,
            "expected_attr_id": want_id,
            "moved_bits": sum(len(m["set"]) + len(m["cleared"])
                              for m in moved.values()),
            "moved_tiles": sorted(moved),
            "moved": moved,
            "attrvals": resolved,
            "attr_ids": sorted(ids),
            "names": sorted({r["name"] for r in resolved if r["name"]}),
            "co_movers": sorted(PUMP_CO_MOVERS[i] for i in ids
                                if i in PUMP_CO_MOVERS),
            "unexpected_attr_ids": unexpected,
            "verified_vs_t22": verified,
        }
        result["runs"].append(entry)
        print(f"{point:12s} {axis.param}={value:<3d} FVCO={entry['fvco_mhz']:8.2f} "
              f"moved={entry['moved_bits']:4d} tiles={entry['moved_tiles']} "
              f"names={entry['names']} vs_T22={verified}")

    result["verified_count"] = ok
    result["run_count"] = len([r for r in result["runs"] if "point" in r])
    print(f"\n{ok} of {result['run_count']} points agree with P1.T22's attrmap")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
