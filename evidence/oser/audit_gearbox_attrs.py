"""`P3.T13`/`P3.T14` -- the OSER/IDES attribute audit against the vendor.

What this measures, and with which instrument
---------------------------------------------
The question is *which IOLOGIC attributes the vendor sets* for each width of
the output-serialiser and input-deserialiser families on the GW5AST-138C, and
which of them `gowin_pack` emits.  The instrument is the same one `P3.T11`
built for the DDR pair and is imported from it rather than copied: the vendor
bitstream, decoded through apicula's own `IOLOGIC` shortval table, with the
fuse set each side writes computed through `gowin_pack`'s own
`add_attr_val` -> `get_shortval_fuses` path.  The verdict term is the fuse
set, not the attribute list: an attribute at its zero code moves no bit and
is not a gap.

**No oracle run is spent here.**  The sweep batches (`p3-oser`, `p3-ides`)
already leave one vendor bitstream per point on disk, and decoding a file is
a pure function of it -- the same separation `P3.T08` used over `P3.T07`'s
designs and `P3.T12` used over its own.

Usage (from the apicula worktree, `PYTHONPATH=.`)::

    python $OTC/evidence/oser/audit_gearbox_attrs.py \\
        --slug oser --design-root $DATASTORE/p3t13 --batch-id p3-oser --write
"""
import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_T11 = os.path.join(os.path.dirname(_HERE), "oddr-iddr",
                    "audit_oddr_iddr_attrs.py")


def _t11():
    """`P3.T11`'s audit module -- the instrument of record, imported."""
    spec = importlib.util.spec_from_file_location("p3t11_audit", _T11)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Which shape and which of its `POINTS` fields name the primitive, per slug.
SLUGS = {
    "oser": {"shape": "io_ser", "design_root_default": "p3t13",
             "batch_id": "p3-oser"},
    "ides": {"shape": "io_des", "design_root_default": "p3t14",
             "batch_id": "p3-ides"},
}


def primitive_of(shape_module, point):
    width = shape_module.POINTS[point][0]
    return shape_module.PRIMITIVE_OF_WIDTH[width]


def decode_iologic(fs_path, tile_xy):
    """`{half: {attr: value}}` for one IOLOGIC tile of one bitstream.

    The tile is addressed directly, by the shape's own scope, rather than
    found by asking `gowin_unpack` which cells it recovered: a mode the
    decoder cannot *name* still has its attributes in the tile, and this row
    has to be able to say so (MEASURED, `P3.T13`: an `OVIDEO`'s `OUTMODE`
    fuses come back as value id 74 and no IOLOGIC cell is recovered at all).
    Pure function of the file -- no oracle run is spent.
    """
    from apycula import attrids, bslib, chipdb
    from apycula.gowin_unpack import parse_attrvals

    db = _t11().audit_db()
    x, y = tile_xy
    row, col = y, x
    bitmap = bslib.read_bitstream(fs_path)[0]
    tile = chipdb.tile_bitmap(db, bitmap)[(row, col)]
    ttyp = db.grid[row][col]
    out = {}
    for half in "AB":
        table = db.shortval[ttyp].get(f"IOLOGIC{half}")
        if table is None:
            continue
        raw = parse_attrvals(tile, db.rev_logicinfo("IOLOGIC"), table,
                             attrids.iologic_attrids, "IOLOGIC")
        if raw:
            out[half] = {attr: attrids.iologic_num2val.get(val, str(val))
                         for attr, val in sorted(raw.items())}
    return out


def audit(slug, design_root, batch_id):
    """One record per sweep point: the vendor's decoded IOLOGIC attributes
    beside the open flow's, at the shape's own scope tile.

    Both sides are read from the bitstream each flow actually produced, so
    what the record compares is what shipped -- not a re-invocation of the
    packer with parameters this script chose.  That distinction matters: the
    packer's `FCLKSEL*`, `TXCLK_POL` and `HWL` all depend on the placed cell's
    own parameters and on the HCLK lane `nextpnr` routed to, none of which a
    stub call can know.
    """
    import importlib
    from fuzz.gw5ast138c.harness import evidence

    cfg = SLUGS[slug]
    shape_module = importlib.import_module(
        "fuzz.gw5ast138c.shapes.%s" % cfg["shape"])
    tile_xy = shape_module.SCOPE_TILES[0]
    rows_path = os.path.join(evidence.evidence_root(), "_runs",
                             "%s.rows.jsonl" % batch_id)
    batch_rows = [json.loads(l) for l in open(rows_path) if l.strip()]

    out = []
    for row in batch_rows:
        point = row["sweep"]["POINT"]
        primitive = primitive_of(shape_module, point)
        fs = row.get("vendor_fs")
        vendor_fs = (fs[0]["path"] if isinstance(fs, list) and fs
                     else os.path.join(design_root, row["run_id"], "run",
                                       "impl", "pnr", "run.fs"))
        open_fs = os.path.join(design_root, row["run_id"], "top.fs")
        missing = [p for p in (vendor_fs, open_fs) if not os.path.exists(p)]
        if missing:
            out.append({"point": point, "primitive": primitive,
                        "error": "no bitstream at %s" % ", ".join(missing)})
            continue
        vendor = decode_iologic(vendor_fs, tile_xy)
        opened = decode_iologic(open_fs, tile_xy)
        halves = sorted(set(vendor) | set(opened))
        gap = []
        for half in halves:
            v, o = vendor.get(half, {}), opened.get(half, {})
            for attr in sorted(set(v) | set(o)):
                if v.get(attr) == o.get(attr):
                    continue
                gap.append({"half": half, "attr": attr,
                            "vendor_val": v.get(attr, "-"),
                            "open_val": o.get(attr, "-"),
                            "direction": ("value_differs" if attr in v and attr in o
                                          else "vendor_only" if attr in v
                                          else "open_only")})
        out.append({
            "point": point,
            "primitive": primitive,
            "tile": list(tile_xy),
            "vendor_attrs": vendor,
            "open_attrs": opened,
            "gap": gap,
        })
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="audit_gearbox_attrs")
    parser.add_argument("--slug", required=True, choices=sorted(SLUGS))
    parser.add_argument("--design-root", required=True)
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    batch_id = args.batch_id or SLUGS[args.slug]["batch_id"]
    records = audit(args.slug, args.design_root, batch_id)

    for rec in records:
        if "error" in rec:
            print("%-20s %-8s ERROR %s"
                  % (rec["point"], rec["primitive"], rec["error"]))
            continue
        print("%-20s %-8s tile=%s %s"
              % (rec["point"], rec["primitive"], tuple(rec["tile"]),
                 "IDENTICAL" if not rec["gap"] else
                 "DIFFER on %d attribute(s)" % len(rec["gap"])))
        for half in sorted(rec["vendor_attrs"]):
            print("    vendor %s: %s" % (half, rec["vendor_attrs"][half]))
        for half in sorted(rec["open_attrs"]):
            print("    open   %s: %s" % (half, rec["open_attrs"][half]))
        for g in rec["gap"]:
            print("    %-18s half=%s vendor=%-12s open=%-12s %s"
                  % (g["attr"], g["half"], g["vendor_val"], g["open_val"],
                     g["direction"]))

    if args.write:
        from fuzz.gw5ast138c.harness import evidence
        root = os.path.join(evidence.evidence_root(), args.slug)
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "attr-audit.json"), "w") as fh:
            json.dump(records, fh, indent=1, sort_keys=True)
        header = ["primitive", "point", "half", "attr", "vendor_val",
                  "open_val", "direction"]
        with open(os.path.join(root, "attr-gap.tsv"), "w") as fh:
            fh.write("\t".join(header) + "\n")
            for rec in records:
                for g in rec.get("gap", []):
                    line = dict(g, primitive=rec["primitive"],
                                point=rec["point"])
                    fh.write("\t".join(str(line[k]) for k in header) + "\n")
        print("wrote attr-audit.json and attr-gap.tsv under %s" % root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
