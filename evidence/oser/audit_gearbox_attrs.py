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


def packed_parms(primitive):
    """The `parms` `nextpnr`'s `pack_iologic.cc` puts on the packed cell.

    `pack_iologic.cc:134-205` sets `OUTMODE` per output primitive and
    `:283-347` `INMODE` per input one; the audit calls the handler with the
    same parameters the packer would, so what is compared is the handler and
    not a netlist this script invented.
    """
    return {
        "OSER4": {"OUTMODE": "ODDRX2"},
        "OSER8": {"OUTMODE": "ODDRX4"},
        "OSER10": {"OUTMODE": "ODDRX5"},
        "OVIDEO": {"OUTMODE": "VIDEOTX"},
        "IDES4": {"INMODE": "IDDRX2"},
        "IDES8": {"INMODE": "IDDRX4"},
        "IDES10": {"INMODE": "IDDRX5"},
    }[primitive]


def apicula_attrvals(primitive, fclk="UNKNOWN"):
    """`{attr: val}` `GW5AST_138C` emits for `primitive`, today."""
    from apycula import gowin_pack

    parms = packed_parms(primitive)

    class _Cell:
        typ = primitive
        parms = None
        attrs = {}

    _Cell.parms = dict(parms)
    bel = gowin_pack.IologicBelDesc(0, 0, "0", _Cell(), fclk,
                                    parms.get("OUTMODE"), parms.get("INMODE"))
    device = object.__new__(gowin_pack.GW5AST_138C)
    attr_vals = device.common_iologic_handler(bel)
    if "OUTMODE" in parms:
        attr_vals += device.get_out_iologic_attrs(bel)
    else:
        attr_vals += device.get_in_iologic_attrs(bel)
    return {av.attr: str(av.val) for av in attr_vals}


def audit(slug, design_root, batch_id):
    """One record per sweep point: vendor attrs, apicula attrs, both fuse sets."""
    t11 = _t11()
    import importlib
    from fuzz.gw5ast138c.harness import evidence

    cfg = SLUGS[slug]
    shape_module = importlib.import_module(
        "fuzz.gw5ast138c.shapes.%s" % cfg["shape"])
    rows_path = os.path.join(evidence.evidence_root(), "_runs",
                             "%s.rows.jsonl" % batch_id)
    batch_rows = [json.loads(l) for l in open(rows_path) if l.strip()]

    out = []
    for row in batch_rows:
        point = row["sweep"]["POINT"]
        primitive = primitive_of(shape_module, point)
        fs = row.get("vendor_fs")
        if isinstance(fs, list) and fs:
            fs_path = fs[0]["path"]
        else:
            fs_path = os.path.join(design_root, row["run_id"], "run", "impl",
                                   "pnr", "run.fs")
        if not os.path.exists(fs_path):
            out.append({"point": point, "primitive": primitive,
                        "error": "no vendor bitstream at %s" % fs_path})
            continue
        cells = t11.vendor_attrvals(fs_path)
        if not cells:
            out.append({"point": point, "primitive": primitive,
                        "error": "no IOLOGIC bel realised in this bitstream"})
            continue
        cell = cells[0]
        apicula = apicula_attrvals(primitive)
        db = t11.audit_db()
        out.append({
            "point": point,
            "primitive": primitive,
            "tile": cell["tile"],
            "ttyp": cell["ttyp"],
            "idx": cell["idx"],
            "vendor_attrs": cell["attrs"],
            "apicula_attrs": apicula,
            "vendor_fuses": sorted(tuple(b) for b in cell["vendor_bits"]),
            "apicula_fuses": sorted(
                t11.fuse_bits(db, cell["ttyp"], cell["idx"], apicula)),
            "gap": t11.gap_rows(primitive, cell, apicula),
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
        same = rec["vendor_fuses"] == rec["apicula_fuses"]
        print("%-20s %-8s tile=%s%s %s vendor=%d apicula=%d %s"
              % (rec["point"], rec["primitive"], tuple(rec["tile"]),
                 rec["idx"], "ttyp%d" % rec["ttyp"],
                 len(rec["vendor_fuses"]), len(rec["apicula_fuses"]),
                 "IDENTICAL" if same else "DIFFER"))
        if not same:
            only_v = [b for b in rec["vendor_fuses"]
                      if b not in rec["apicula_fuses"]]
            only_a = [b for b in rec["apicula_fuses"]
                      if b not in rec["vendor_fuses"]]
            print("    vendor_only=%s apicula_only=%s" % (only_v, only_a))
            for g in rec["gap"]:
                if g["direction"] != "agree":
                    print("    %-18s vendor=%-12s apicula=%-12s %s (%d bits)"
                          % (g["attr"], g["vendor_val"], g["apicula_val"],
                             g["direction"], g["bits"]))

    if args.write:
        from fuzz.gw5ast138c.harness import evidence
        root = os.path.join(evidence.evidence_root(), args.slug)
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "attr-audit.json"), "w") as fh:
            json.dump(records, fh, indent=1, sort_keys=True)
        gaps = [g for rec in records for g in rec.get("gap", [])]
        header = ["bits", "primitive", "attr", "vendor_val", "apicula_val",
                  "direction", "attrid", "tile", "ttyp", "idx", "disposition",
                  "justification"]
        with open(os.path.join(root, "attr-gap.tsv"), "w") as fh:
            fh.write("\t".join(header) + "\n")
            for g in gaps:
                fh.write("\t".join(str(g[k]) for k in header) + "\n")
        print("wrote attr-audit.json and attr-gap.tsv under %s" % root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
