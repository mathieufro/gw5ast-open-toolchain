"""`P1.T14` -- attribute the GW5AST-138C `CLKDIV` `DIV_MODE` fuses.

The sweep changes exactly one parameter, so the bits that move inside the
HCLK block cell between two runs are that parameter's fuses.  Each moved bit
is looked up in the tile's `shortval['HCLK']` table; the attrvals in the
matching rows' keys are mapped back through `logicinfo['HCLK']` to
`(attr_id, value)` and through `attrids.hclk_attrids` / `hclk_attrvals` to a
name.  A run whose moved bits resolve to exactly `HCLKDIV<lane>_DIV = <the
DIV_MODE it swept>` is a VERIFIED `(attr, value) -> fuses` row -- the
attribution is *searched for*, never assumed from `gowin_pack`'s formula, so
agreement between the two is evidence rather than a tautology.

The reference point is the documented default `DIV_MODE = "2"`
(`gowin_pack.GW5A.get_default_clkdiv_divmode`), which is the sweep's own
baseline point, not an empty design (`spec-harness.md` §7).

Usage:
    python gen_divmode_fuses.py <batch design dir> [<out.json>]
"""
import json
import sys
import importlib.resources as ir
from pathlib import Path

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap
from apycula.gowin_pack import add_attr_val, get_shortval_fuses

#: HCLK block 5 of the 138C (`P1.T04`: `_gw5a_hclk_locs[...][5] == (108, 117)`),
#: the cell `shapes/clocking_clkdiv.py` pins both flows to.
SITE_TILE = (108, 117)

#: The `DIV_MODE` the whole sweep is differenced against.
DEFAULT_DIV_MODE = "2"

#: The HCLK lane `shapes/clocking_clkdiv.py` pins the CLKDIV to.
LANE = 0


def set_bits(tile):
    """`{(row, col)}` of the bits set in one tile bitmap."""
    if tile is None:
        return set()
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def tile_bits(fs_path, db):
    """The set bits of `SITE_TILE` in one `.fs`."""
    bitmap = read_bitstream(str(fs_path))[0]
    return set_bits(tile_bitmap(db, bitmap).get(SITE_TILE))


def resolve(db, ttyp, delta):
    """`(attr, value)` names whose `shortval['HCLK']` rows touch `delta`."""
    inv_val = {v: k for k, v in attrids.hclk_attrvals.items()}
    inv_attr = {v: k for k, v in attrids.hclk_attrids.items()}
    inv_logic = {v: k for k, v in db.logicinfo["HCLK"].items()}
    names, raw = set(), set()
    for key, fuses in db.shortval[ttyp].get("HCLK", {}).items():
        if not delta & set(map(tuple, fuses)):
            continue
        for attrval in key:
            if attrval <= 0:
                continue
            raw.add(attrval)
            pair = inv_logic.get(attrval)
            if pair is None:
                continue
            attr_id, value = pair
            names.add((inv_attr.get(attr_id, f"attr_id:{attr_id}"),
                       inv_val.get(value, str(value))))
    return sorted(names), sorted(raw)


def predicted(db, ttyp, lane, div_mode):
    """The fuses `gowin_pack.GW5A.get_CLKDIV_fuses` would emit for one mode.

    Kept independent of the measurement above: this is `apicula`'s claim, the
    other is the vendor's behaviour, and the row is only evidence because the
    two are computed from different sources and then compared.
    """
    av = set()
    add_attr_val(db, "HCLK", av,
                 attrids.hclk_attrids[f"HCLKDIV{lane}_DIV"],
                 attrids.hclk_attrvals[div_mode])
    return sorted(tuple(b) for b in get_shortval_fuses(db, ttyp, av, "HCLK"))


def divmode_of(run_dir):
    """The `DIV_MODE` a run's generated `top.v` carries."""
    for line in (run_dir / "top.v").read_text().splitlines():
        if "defparam" in line and "DIV_MODE" in line:
            return line.split("=", 1)[1].strip().strip(';').strip().strip('"')
    return None


def main(argv):
    design_root = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None
    db = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))
    ttyp = db.grid[SITE_TILE[0]][SITE_TILE[1]]

    runs = {}
    for run_dir in sorted(design_root.iterdir()):
        fs = run_dir / "run/impl/pnr/run.fs"
        if not fs.is_file():
            continue
        mode = divmode_of(run_dir)
        if mode is not None:
            runs[mode] = (run_dir, fs)

    if DEFAULT_DIV_MODE not in runs:
        print(f"no DIV_MODE={DEFAULT_DIV_MODE} run under {design_root}: the "
              f"sweep's own reference point is missing")
        return 2

    base = tile_bits(runs[DEFAULT_DIV_MODE][1], db)
    result = {"task": "P1.T14", "device": "GW5AST-138C",
              "site_tile": list(SITE_TILE), "site_ttyp": ttyp,
              "reference_div_mode": DEFAULT_DIV_MODE,
              "reference_tile_bits": len(base), "points": []}

    for mode in sorted(runs, key=float):
        run_dir, fs = runs[mode]
        cur = tile_bits(fs, db)
        delta = base ^ cur
        names, raw = resolve(db, ttyp, delta)
        want = predicted(db, ttyp, LANE, mode)
        want_ref = predicted(db, ttyp, LANE, DEFAULT_DIV_MODE)
        agrees = set(want) <= cur and set(delta) == (set(want) ^ set(want_ref))
        expected = [n for n in names
                    if n[0].startswith("HCLKDIV") and n[0].endswith("_DIV")
                    and n[1] == mode]
        result["points"].append({
            "div_mode": mode,
            "run": run_dir.name,
            "tile_bits": len(cur),
            "set": sorted(f"{r},{c}" for r, c in cur - base),
            "cleared": sorted(f"{r},{c}" for r, c in base - cur),
            "attributed": [list(n) for n in names],
            "attrvals": raw,
            "packer_predicted": [list(b) for b in want],
            "agrees_with_packer": agrees,
            "verified": bool(expected) or (mode == DEFAULT_DIV_MODE
                                           and not delta),
        })

    if out_path is not None:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
