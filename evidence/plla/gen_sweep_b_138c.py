"""`P1.T41` -- attribute batch B's moved fuses and check them against `P1.T22`.

Batch B (`p1-pll-sweep-b`, shape `fuzz/gw5ast138c/shapes/clocking_pll.py` with
`$FUZZ_PLL_AXIS=odiv0,odiv1,mdiv`) sweeps the three divider axes batch A did
not, one parameter per run, each axis with its own baseline:

    ODIV0  FCLKIN 100, IDIV 4, FBDIV 18, MDIV  2, ODIV0_SEL 1,2,3,4,8,16,64 (base 8)
    ODIV1  as ODIV0 + CLKOUT1_EN TRUE,             ODIV1_SEL 2,4,8,16,32,64 (base 8)
    MDIV   FCLKIN 100, IDIV 4, FBDIV  1,           MDIV_SEL 26..52          (base 36)

The procedure is `gen_sweep_a_138c.py`'s, unchanged: the bits that differ from
a point's **own axis baseline** inside the three tiles of `PLL_L[0]` are looked
up in `shortval[35]` and mapped back through `logicinfo['PLL']` and
`pll_attrids`.  What differs is the expectation table -- `P1.T22` measured
`A_ODIV0_SEL` (114) and `A_MDIV_SEL` (113) at three and two divider values
respectively, and the `ODIV1` axis turns out to write **no** fuse at all
(`NO_FUSE_AXES`).

Usage:
    python gen_sweep_b_138c.py <rows.jsonl> [<out.json>]
"""
import importlib.resources as ir
import json
import sys
from pathlib import Path

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

BATCH_ID = "p1-pll-sweep-b"

#: `PLL_L[0]`, `sites-138c.json` pll_idx 0: row 27, columns 1..3.
SITE = "PLL_L[0]"
SITE_TILES = [(27, 1), (27, 2), (27, 3)]

#: The attribute each swept parameter must move, and the tile it must move it
#: in.  `A_ODIV0_SEL`/`A_MDIV_SEL` are `P1.T22`'s (`attrmap-138c.md` §4);
#: `A_ODIV1_SEL` is this batch's first sighting and its id comes from the
#: `.fse` census (`attrids-138c.tsv`), not from a previous run.
EXPECTED = {
    "ODIV0": ("A_ODIV0_SEL", 114, (27, 1)),
    "ODIV1": (None, None, None),
    "MDIV": ("A_MDIV_SEL", 113, (27, 1)),
}

#: An axis whose expectation is "no fuse moves", with the reason.  MEASURED
#: here: with `CLKOUT1_EN "TRUE"` the vendor does write `A_CLKOUT1_EN` (154,
#: value 50) but writes **no** `A_ODIV1_SEL` (115) at any of the six divider
#: values -- the shape leaves `CLKOUT1` unconnected, so the output has no load
#: and the vendor programs the enable without the divider.  The axis therefore
#: measures a real property of the vendor flow, and a point that moved a bit
#: would be the surprise.  Loading `CLKOUT1` needs a second flop in the RTL,
#: which is `P1.T23`'s shape to change, not this task's.
NO_FUSE_AXES = {
    "ODIV1": "CLKOUT1 is unconnected in the shape, so the vendor writes "
             "A_CLKOUT1_EN but no A_ODIV1_SEL at any divider value",
}

#: The vendor recomputes these from `fref`/`fvco`, so an axis that moves the
#: VCO moves them too (`attrmap-138c.md` §3, `sweep-a-138c.md` §3).
PUMP_CO_MOVERS = {16: "FLDCOUNT", 28: "KVCO",
                  111: "A_ICP_SEL", 112: "A_LPF_RES_SEL"}

#: `CLKOUT1_EN` is the `ODIV1` axis's operating point, not its swept
#: parameter, so its attribute is present in every `ODIV1` row -- including the
#: axis baseline, which is why it can never appear as a *moved* bit inside the
#: axis.  Listed so a stray sighting is not mistaken for a discrepancy.
OPERATING_POINT_ATTRS = {154: "A_CLKOUT1_EN"}


def set_bits(tile):
    if tile is None:
        return set()
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def attribute(db, base_tiles, run_tiles, ttyps):
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
            if delta & {tuple(f) for f in fuses}:
                attrvals.update(a for a in key if a > 0)
    return moved, attrvals


def tiles_of(db, fs_path):
    bitmap, _h, _f, _s = read_bitstream(str(fs_path))
    return tile_bitmap(db, bitmap, empty=True)


def main(argv):
    rows_path = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None

    rows = [json.loads(l) for l in rows_path.read_text().splitlines() if l.strip()]
    by_run = {r["run_id"]: r for r in rows}

    db = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))
    ttyps = [db.grid[r][c] for r, c in SITE_TILES]
    inv = {v: k for k, v in db.logicinfo["PLL"].items()}
    id2name = {v: k for k, v in attrids.pll_attrids.items()}

    from fuzz.gw5ast138c.shapes import clocking_pll as shape

    points = shape.points()
    order = list(points)

    result = {
        "task": "P1.T41",
        "device": "GW5AST-138C",
        "batch_id": BATCH_ID,
        "site": SITE,
        "site_tiles": [list(t) for t in SITE_TILES],
        "site_ttyps": ttyps,
        "expected_vs_t22": {
            k: ({"name": v[0], "attr_id": v[1], "tile": list(v[2])}
                if v[0] is not None
                else {"name": None, "attr_id": None, "tile": None,
                      "why_no_fuse": NO_FUSE_AXES[k]})
            for k, v in EXPECTED.items()},
        "runs": [],
    }

    fs_of = {}
    for idx, point in enumerate(order):
        row = by_run.get(f"{BATCH_ID}-clocking_pll-{idx:04d}")
        if row and row.get("vendor_fs"):
            fs_of[point] = Path(row["vendor_fs"][0]["path"])

    baselines = {}
    for axis in shape.selected_axes():
        base_point = f"{axis.name.lower()}_{axis.baseline:03d}"
        if base_point in fs_of:
            baselines[axis.name] = tiles_of(db, fs_of[base_point])

    ok = 0
    for idx, point in enumerate(order):
        axis, value = points[point]
        run_id = f"{BATCH_ID}-clocking_pll-{idx:04d}"
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
        want_name, want_id, _want_tile = EXPECTED[axis.name]
        is_base = value == axis.baseline
        unexpected = sorted(ids - {want_id} - set(PUMP_CO_MOVERS)
                            - set(OPERATING_POINT_ATTRS))
        if axis.name in NO_FUSE_AXES:
            verified = not ids
            want_name = f"(no fuse: {NO_FUSE_AXES[axis.name]})"
        else:
            verified = is_base or (want_id in ids and not unexpected)
        if verified:
            ok += 1
        parms = axis.params(value)
        divider = int(parms[axis.param]) if axis.name.startswith("ODIV") \
            else int(parms["ODIV0_SEL"])
        entry = {
            "run_id": run_id,
            "point": point,
            "axis": axis.name,
            "param": axis.param,
            "value": value,
            "baseline": is_base,
            "fvco_mhz": round(axis.fvco(value), 4),
            "fpfd_mhz": round(axis.fpfd(value), 4),
            "clkout_mhz": round(axis.fvco(value) / divider, 4),
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
              f"names={entry['names']} verified={verified}")

    result["verified_count"] = ok
    result["run_count"] = len([r for r in result["runs"] if "axis" in r])
    print(f"\n{ok} of {result['run_count']} points attributed as expected")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
