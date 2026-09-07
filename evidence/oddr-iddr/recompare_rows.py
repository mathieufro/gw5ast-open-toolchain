"""`P3.T12` -- re-compare the batch's designs and publish the row.

The batch (`evidence/_runs/p3-oddr-iddr.log`) spends the oracle runs and
leaves, per sweep point, the vendor bitstream and the open flow's own beside
each other on disk.  The comparison over those two files is a pure function
of them, so once the packer and the decode are corrected the row is re-derived
here from the bitstreams already measured and **no further oracle run is
spent** -- the same separation `P3.T08` used to close the pin->HCLK row over
`P3.T07`'s designs.

    python $OTC/evidence/oddr-iddr/recompare_rows.py \
        --design-root $DATASTORE/p3t12 --batch-id p3-oddr-iddr --write

Without `--write` it prints the verdict each row would carry and changes
nothing.
"""
import argparse
import json
import os
import sys


def rows_of(path):
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]


def recompare(row, design_root, level="E1"):
    """The row as the corrected comparison sees it, artefacts unchanged."""
    from fuzz.gw5ast138c.harness import equiv, evidence, gen

    design_dir = os.path.join(design_root, row["run_id"])
    spec = gen.load_shape(row["shape"])
    result = equiv.compare(design_dir, spec, level=level)
    return evidence.adapt(row, **equiv.evidence_fields(result))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="recompare_rows")
    parser.add_argument("--design-root", required=True)
    parser.add_argument("--batch-id", default="p3-oddr-iddr")
    parser.add_argument("--slug", default="oddr-iddr")
    parser.add_argument("--level", default="E1", choices=("E0", "E1", "E2"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    from fuzz.gw5ast138c.harness import evidence

    root = evidence.evidence_root()
    batch_rows = os.path.join(root, "_runs", f"{args.batch_id}.rows.jsonl")
    out_path = os.path.join(root, args.slug, "runs.jsonl")

    rows = []
    for row in rows_of(batch_rows):
        if row.get("verdict") in ("aborted", "refused"):
            rows.append(row)
            print("%-32s %-8s (kept: build verdict)"
                  % (row["run_id"], row["verdict"]))
            continue
        fresh = recompare(row, args.design_root, level=args.level)
        rows.append(fresh)
        print("%-32s %-8s -> %-8s level=%s"
              % (row["run_id"], row["verdict"], fresh["verdict"],
                 fresh["level"]))

    if args.write:
        with open(out_path, "w") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        print("wrote %d rows to %s" % (len(rows), out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
