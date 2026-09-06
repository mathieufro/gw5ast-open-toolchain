"""`P1.T43` -- decode the same `PLL` at each of the twelve sites.

Batch D (`p1-pll-sweep-d`, shape `fuzz/gw5ast138c/shapes/clocking_pll.py` with
`$FUZZ_PLL_AXIS=site`) builds one design -- `P1.T39`'s reference operating
point, `FCLKIN` 50 MHz, `IDIV` 1, `FBDIV` 1, `MDIV` 16, `ODIV0` 8 -- twelve
times, moving only the `INS_LOC`.

There is no per-point baseline to difference against here, because every point
is a different place: the measurement is *absolute*.  For each run the site's
three tiles are decoded through `shortval[35]` the way `gowin_unpack` decodes
them -- an entry is active when **every** fuse of its key is set -- and the
resulting `{attribute: value}` map is compared with `PLL_L[0]`'s.  Twelve
identical maps at twelve different tile coordinates is the claim "all twelve
sites are real and carry the same attribute encoding"; a site whose map
differs is a finding, recorded here and in the row's `notes`, never a silent
edit to `sites-138c.md` (`P1.T17`/`P1.T19` own that file).

Usage:
    python gen_sites_e1_138c.py <rows.jsonl> [<out.json>]
"""
import importlib.resources as ir
import json
import sys
from pathlib import Path

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

BATCH_ID = "p1-pll-sweep-d"

#: The reference site every other site's decode is compared against.
REFERENCE_SITE = "PLL_L[0]"


def set_bits(tile):
    if tile is None:
        return set()
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def decode(db, tiles, site_tiles, ttyps, inv, id2name):
    """`{attribute name: value}` active in one site's three tiles."""
    out = {}
    for (row, col), ttyp in zip(site_tiles, ttyps):
        bits = set_bits(tiles.get((row, col)))
        if not bits:
            continue
        for key, fuses in db.shortval[ttyp].get("PLL", {}).items():
            wanted = {tuple(f) for f in fuses}
            if not wanted or not wanted <= bits:
                continue
            for attrval in key:
                if attrval <= 0:
                    continue
                attr_id, value = inv.get(attrval, (None, None))
                if attr_id is None:
                    continue
                out[id2name.get(attr_id, f"attr{attr_id}")] = value
    return out


def main(argv):
    rows_path = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None

    rows = [json.loads(l) for l in rows_path.read_text().splitlines() if l.strip()]
    by_run = {r["run_id"]: r for r in rows}

    db = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))
    inv = {v: k for k, v in db.logicinfo["PLL"].items()}
    id2name = {v: k for k, v in attrids.pll_attrids.items()}

    from fuzz.gw5ast138c.shapes import clocking_pll as shape

    points = shape.points()
    order = list(points)

    result = {
        "task": "P1.T43",
        "device": "GW5AST-138C",
        "batch_id": BATCH_ID,
        "reference_site": REFERENCE_SITE,
        "operating_point": {k: v for k, v in
                            shape.AXIS_SITE.operating_point.items()},
        "sites": [],
    }

    decoded = {}
    for idx, point in enumerate(order):
        axis, site = points[point]
        run_id = f"{BATCH_ID}-clocking_pll-{idx:04d}"
        row = by_run.get(run_id, {})
        site_tiles = [(r, c) for c, r in shape.scope_tiles(site)]
        ttyps = [db.grid[r][c] for r, c in site_tiles]
        entry = {
            "run_id": run_id,
            "point": point,
            "site": site,
            "anchor": list(shape.SITES[site]),
            "tiles": [list(t) for t in site_tiles],
            "ttyps": ttyps,
            "verdict": row.get("verdict"),
            "level": row.get("level"),
            "diff_count": row.get("diff_count"),
            "decode_check": row.get("decode_check"),
            "open_fs": bool(row.get("open_fs")),
        }
        if row.get("vendor_fs"):
            tiles = tile_bitmap(
                db, read_bitstream(row["vendor_fs"][0]["path"])[0], empty=True)
            attrs = decode(db, tiles, site_tiles, ttyps, inv, id2name)
            entry["attrs"] = attrs
            entry["attr_count"] = len(attrs)
            decoded[site] = attrs
        else:
            entry["attrs"] = None
        result["sites"].append(entry)

    reference = decoded.get(REFERENCE_SITE)
    for entry in result["sites"]:
        attrs = entry["attrs"]
        if reference is None or attrs is None:
            entry["same_as_reference"] = None
            continue
        entry["same_as_reference"] = attrs == reference
        entry["attr_delta"] = {
            k: [reference.get(k), attrs.get(k)]
            for k in set(reference) | set(attrs) if reference.get(k) != attrs.get(k)}

    result["sites_decoded"] = len(decoded)
    result["sites_matching_reference"] = sum(
        1 for e in result["sites"] if e.get("same_as_reference"))
    result["e1_ok"] = sum(1 for e in result["sites"] if e["verdict"] == "ok")
    for entry in result["sites"]:
        print(f"{entry['site']:10s} anchor={tuple(entry['anchor'])} "
              f"ttyps={entry['ttyps']} attrs={entry['attr_count'] if entry['attrs'] else '-'} "
              f"same={entry.get('same_as_reference')} verdict={entry['verdict']}")
    print(f"\n{result['sites_matching_reference']}/{result['sites_decoded']} "
          f"sites decode identically; {result['e1_ok']} rows E1 ok")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
