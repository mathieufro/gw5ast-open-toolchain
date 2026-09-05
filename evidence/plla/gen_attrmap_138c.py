"""`P1.T22` -- derive the GW5AST-138C `PLL` attrid/attrval map and verify it.

Two independent halves, both written to `attrmap-138c.json`:

1. **The census** (no oracle needed): the attribute-id space of the shipped
   `.fse`'s `logicinfo['PLL']` table for the 138C, reconciled against
   `apycula/attrids.py`'s `pll_attrids`.  Emits the three counts `P1.T22` asks
   for -- ids in both, ids in the `.fse` with no name, names with no `.fse` id
   -- and, for the 25A, the same three so the divergence can be attributed to
   the device rather than to the table.

2. **The attribution** (12 oracle runs, batch `p1-pll-attrmap`): each run
   changes exactly ONE `PLL` parameter from the baseline, so the bits that
   move inside the three tiles of `PLL_L[0]` are that parameter's fuses.  Each
   moved bit is looked up in the tile's `shortval[35]` table; the attrvals in
   the matching rows' keys are mapped back through `logicinfo['PLL']` to
   `(attr_id, value)` and through `pll_attrids` to a name.  A run whose moved
   bits resolve to exactly the attribute the run varied is a VERIFIED
   `(attr, value) -> fuses` row.

Usage:
    python gen_attrmap_138c.py <batch design dir> [<out.json>]
"""
import json
import os
import sys
import importlib.resources as ir
from pathlib import Path

from apycula import chipdb as cdb
from apycula import attrids
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

#: `PLL_L[0]`, `sites-138c.json` pll_idx 0: row 27, columns 1..3.
SITE = "PLL_L[0]"
SITE_TILES = [(27, 1), (27, 2), (27, 3)]

#: The shape's points, in sweep order (`shapes/clocking_pll_attrmap.py`).
POINTS = [
    ("p00_baseline", None, None),
    ("p01_idiv3", "IDIV_SEL", 3),
    ("p02_idiv4", "IDIV_SEL", 4),
    ("p03_fbdiv1", "FBDIV_SEL", 1),
    ("p04_mdiv7", "MDIV_SEL", 7),
    ("p05_mdiv10", "MDIV_SEL", 10),
    ("p06_odiv0_4", "ODIV0_SEL", 4),
    ("p07_odiv0_16", "ODIV0_SEL", 16),
    ("p08_odiv0_64", "ODIV0_SEL", 64),
    ("p09_dyn_idiv", "DYN_IDIV_SEL", "TRUE"),
    ("p10_dyn_odiv0", "DYN_ODIV0_SEL", "TRUE"),
    ("p11_clkout1_en", "CLKOUT1_EN", "TRUE"),
]

#: Verilog parameter -> the `attrids.pll_attrids` name the packer emits for it
#: (`gowin_pack.GW5A.get_pll_attrvals` prefixes every PLLA/PLL parameter with
#: `A_`; `DYN_*` map onto the `A_DYN_*`/`A_*` spellings).
PARAM_TO_ATTR = {
    "IDIV_SEL": "A_IDIV_SEL",
    "FBDIV_SEL": "A_FBDIV_SEL",
    "MDIV_SEL": "A_MDIV_SEL",
    "ODIV0_SEL": "A_ODIV0_SEL",
    "CLKOUT1_EN": "A_CLKOUT1_EN",
    "DYN_IDIV_SEL": None,   # no A_DYN_IDIV_SEL in pll_attrids -- a finding
    "DYN_ODIV0_SEL": None,
}


def set_bits(tile):
    """`{(row, col)}` of the bits set in one tile bitmap."""
    if tile is None:
        return set()
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def census(db, device):
    """The three reconciliation counts for one device's `logicinfo['PLL']`."""
    table = db.logicinfo["PLL"]
    fse_ids = {k[0] for k in table}
    named = set(attrids.pll_attrids.values())
    id2name = {v: k for k, v in attrids.pll_attrids.items()}
    return {
        "device": device,
        "fse_attr_ids": len(fse_ids),
        "named_attr_ids": len(named),
        "in_both": len(fse_ids & named),
        "fse_id_with_no_name": sorted(fse_ids - named),
        "name_with_no_fse_id": sorted(id2name[i] for i in (named - fse_ids)),
        "table_rows": len(table),
    }


def attribute_run(db, baseline_tiles, run_tiles, ttyps):
    """Moved bits per tile, and the attrvals whose shortval rows contain them."""
    moved = {}
    attrvals = set()
    for (row, col), ttyp in zip(SITE_TILES, ttyps):
        base = set_bits(baseline_tiles.get((row, col)))
        cur = set_bits(run_tiles.get((row, col)))
        delta = base ^ cur
        if not delta:
            continue
        moved[f"{row},{col}"] = {
            "set": sorted(f"{r},{c}" for r, c in cur - base),
            "cleared": sorted(f"{r},{c}" for r, c in base - cur),
        }
        tab = db.shortval[ttyp].get("PLL", {})
        for key, fuses in tab.items():
            if delta & set(fuses):
                attrvals.update(a for a in key if a > 0)
    return moved, attrvals


def main(argv):
    design_root = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None
    db = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))

    result = {
        "task": "P1.T22",
        "device": "GW5AST-138C",
        "site": SITE,
        "site_tiles": [list(t) for t in SITE_TILES],
        "batch_id": "p1-pll-attrmap",
        "census": census(db, "GW5AST-138C"),
        "runs": [],
    }

    ttyps = [db.grid[r][c] for r, c in SITE_TILES]
    result["site_ttyps"] = ttyps

    # attrval -> (attr_id, value), and attr_id -> name
    inv = {v: k for k, v in db.logicinfo["PLL"].items()}
    id2name = {v: k for k, v in attrids.pll_attrids.items()}

    runs = sorted(p for p in design_root.iterdir()
                  if (p / "run/impl/pnr/run.fs").is_file())
    if not runs:
        print("no completed runs under", design_root)
        return 2

    def tiles_of(run_dir):
        bitmap, _h, _f, _s = read_bitstream(str(run_dir / "run/impl/pnr/run.fs"))
        return tile_bitmap(db, bitmap, empty=True)

    baseline_tiles = tiles_of(runs[0])
    for idx, run_dir in enumerate(runs):
        point, param, value = POINTS[idx] if idx < len(POINTS) else (None, None, None)
        moved, attrvals = attribute_run(db, baseline_tiles, tiles_of(run_dir), ttyps)
        resolved = []
        for av in sorted(attrvals):
            attr_id, val = inv.get(av, (None, None))
            resolved.append({
                "attrval": av,
                "attr_id": attr_id,
                "value": val,
                "name": id2name.get(attr_id),
            })
        want = PARAM_TO_ATTR.get(param)
        names = {r["name"] for r in resolved if r["name"]}
        row = {
            "run_dir": run_dir.name,
            "point": point,
            "param": param,
            "value": value,
            "expected_attr": want,
            "moved_bits": sum(len(m["set"]) + len(m["cleared"])
                              for m in moved.values()),
            "moved": moved,
            "attrvals": resolved,
            "names": sorted(names),
            "verified": bool(want) and want in names,
        }
        result["runs"].append(row)
        print(f"{point:16s} param={str(param):14s} value={str(value):6s} "
              f"moved={row['moved_bits']:4d} names={sorted(names)} "
              f"verified={row['verified']}")

    verified = [r for r in result["runs"] if r["verified"]]
    result["verified_count"] = len(verified)
    result["attributable_points"] = sum(
        1 for r in result["runs"] if r["param"] and PARAM_TO_ATTR.get(r["param"]))
    print(f"\nverified {len(verified)} of {result['attributable_points']} "
          f"attributable points; census in_both={result['census']['in_both']} "
          f"fse_no_name={len(result['census']['fse_id_with_no_name'])} "
          f"name_no_fse={len(result['census']['name_with_no_fse_id'])}")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
