"""`P1.T42` -- attribute batch C's moved fuses: the `DYN` modes and `ODIV1L`.

Batch C (`p1-pll-sweep-c`, shape `fuzz/gw5ast138c/shapes/clocking_pll.py` with
`$FUZZ_PLL_AXIS=dyn,odiv1l`) sweeps the two things batches A and B could not:

    DYN     which of five DYN_* booleans is "TRUE", against an all-FALSE
            baseline (DYN_IDIV_SEL, DYN_FBDIV_SEL, DYN_MDIV_SEL,
            DYN_ODIV0_SEL, DYN_DPA_EN)
    ODIV1L  ODIV1_SEL 2,4,8,16,32,64 (base 8) with CLKOUT1 *loaded* -- the
            shape variant batch B's null result asked for (sweep-b-138c.md 3.1)

The procedure is `gen_sweep_b_138c.py`'s: the bits differing from a point's
**own axis baseline** inside the three tiles of `PLL_L[0]` are looked up in
`shortval[35]` and mapped back through `logicinfo['PLL']` and `pll_attrids`.

What differs is the expectation. `P1.T22` sighted two of the five modes
(`A_DYN_IDIV_SEL` 125, `A_DYN_ODIV0_SEL` 132); the other three are first
sightings, and the `.fse` attribute census leaves ids 124/127/128/131 unnamed
(`attrids-138c.tsv`), so an unnamed id moving under a named parameter is the
measurement this batch exists to make, not a discrepancy.  Such an id is
reported under `first_sighting` and never counted as `unexpected`.

Usage:
    python gen_sweep_c_138c.py <rows.jsonl> [<out.json>]
"""
import importlib.resources as ir
import json
import sys
from pathlib import Path

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

BATCH_ID = "p1-pll-sweep-c"

#: `PLL_L[0]`, `sites-138c.json` pll_idx 0: row 27, columns 1..3.
SITE = "PLL_L[0]"
SITE_TILES = [(27, 1), (27, 2), (27, 3)]

#: The baseline (`none`) enables no mode and is expected to move nothing.
#: `P1.T22`'s two sighted `DYN` attributes (`attrmap-138c.md` §4), keyed by
#: the shape's mode tag.  A mode with `None` has never been sighted: the
#: attribute id it moves is this batch's measurement.
EXPECTED_MODES = {
    "none": (None, None),
    "idiv": ("A_DYN_IDIV_SEL", 125),
    "odiv0": ("A_DYN_ODIV0_SEL", 132),
    "fbdiv": (None, None),
    "mdiv": (None, None),
    "dpa": (None, None),
}

#: The `ODIV1L` axis's swept attribute -- named in `pll_attrids` but written
#: at no divider value while `CLKOUT1` was unloaded (batch B, six points).
EXPECTED_ODIV1L = ("A_ODIV1_SEL", 115)

#: The vendor recomputes these from `fref`/`fvco` (`attrmap-138c.md` §3), so a
#: point that moves the VCO moves them too.  No batch-C axis moves the VCO, so
#: a co-mover here would itself be a finding; they are listed to keep the
#: verdict comparable with batches A and B.
PUMP_CO_MOVERS = {16: "FLDCOUNT", 28: "KVCO",
                  111: "A_ICP_SEL", 112: "A_LPF_RES_SEL"}

#: `CLKOUT1_EN` is the `ODIV1L` axis's operating point, not its swept
#: parameter, so it is present in every point of that axis including its
#: baseline and can never appear as a *moved* bit inside the axis.
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


def expectation(axis, value):
    """`(name, attr_id)` this point is expected to move, `(None, None)` if new."""
    if axis.name == "ODIV1L":
        return EXPECTED_ODIV1L
    return EXPECTED_MODES[value]


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
        "task": "P1.T42",
        "device": "GW5AST-138C",
        "batch_id": BATCH_ID,
        "site": SITE,
        "site_tiles": [list(t) for t in SITE_TILES],
        "site_ttyps": ttyps,
        "expected_vs_t22": {
            "DYN": {tag: {"name": n, "attr_id": i}
                    for tag, (n, i) in EXPECTED_MODES.items()},
            "ODIV1L": {"name": EXPECTED_ODIV1L[0],
                       "attr_id": EXPECTED_ODIV1L[1]},
        },
        "runs": [],
    }

    fs_of = {}
    for idx, point in enumerate(order):
        row = by_run.get(f"{BATCH_ID}-clocking_pll-{idx:04d}")
        if row and row.get("vendor_fs"):
            fs_of[point] = Path(row["vendor_fs"][0]["path"])

    baselines = {}
    for axis in shape.selected_axes():
        base_point = axis.point_name(axis.baseline)
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
        want_name, want_id = expectation(axis, value)
        is_base = value == axis.baseline
        # An id `pll_attrids` has no name for: the vendor's own attribute
        # table leaves it blank, so a parameter that moves it is what names it.
        first_sighting = sorted(i for i in ids if i not in id2name)
        if is_base:
            verified = True
        elif want_id is not None:
            verified = want_id in ids and not (
                ids - {want_id} - set(PUMP_CO_MOVERS)
                - set(OPERATING_POINT_ATTRS) - set(first_sighting))
        else:
            # a first sighting: the claim is only that the mode moves fuses
            # and that they resolve to a single attribute of the site
            verified = len(ids) == 1
        unexpected = sorted(ids - ({want_id} if want_id else set())
                            - set(PUMP_CO_MOVERS) - set(OPERATING_POINT_ATTRS)
                            - set(first_sighting))
        if verified:
            ok += 1
        parms = axis.params(value)
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
            "first_sighting_attr_ids": first_sighting,
            "co_movers": sorted(PUMP_CO_MOVERS[i] for i in ids
                                if i in PUMP_CO_MOVERS),
            "unexpected_attr_ids": unexpected,
            "verified": verified,
        }
        if axis.name == "ODIV1L":
            entry["odiv1_mhz"] = round(axis.fvco(value) / int(value), 4)
        result["runs"].append(entry)
        print(f"{point:14s} {axis.param}={str(value):<14s} "
              f"moved={entry['moved_bits']:4d} tiles={entry['moved_tiles']} "
              f"ids={sorted(ids)} names={entry['names']} "
              f"new={first_sighting} verified={verified}")

    result["verified_count"] = ok
    result["run_count"] = len([r for r in result["runs"] if "axis" in r])
    print(f"\n{ok} of {result['run_count']} points attributed as expected")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
