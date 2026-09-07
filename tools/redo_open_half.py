#!/usr/bin/env python3
"""Re-run the **open half** of runs whose vendor bitstream is already on disk.

A vendor `gw_sh` invocation is the scarce resource -- the phase budget counts
oracle runs, not builds -- so a batch whose vendor step succeeded and whose
open flow then failed must not be re-run end to end.  The usual cause is a
toolchain mismatch (a `nextpnr-himbaechel` and a `chipdb-*.bin` from different
builds abort with `Assertion failure: ... idstring_idx_to_str`), and the fix is
to install the matching pair and redo `yosys` -> `nextpnr` -> `gowin_pack` over
the design directories that are still sitting there.

This spends **no** oracle run: it never calls `oracle.run_oracle`, and it keeps
the vendor fields of the row it repairs (`vendor_fs`, `sdf`, `tr`,
`oracle_log`, `ide_version`, `wall_clock_s.oracle`) exactly as the oracle
recorded them.  A row whose `vendor_fs` is missing from disk is refused rather
than silently rebuilt.

    python -m tools.redo_open_half --rows evidence/_runs/p3-oser-b.rows.jsonl \
        --shape io_ser --design-root $DATASTORE/p3t13b --write
"""
import argparse
import json
import os
import sys

#: Row fields the oracle owns.  They are carried across verbatim; everything
#: else is recomputed from the rebuilt open flow.
VENDOR_FIELDS = ("vendor_fs", "sdf", "tr", "sdf_condition", "oracle_log",
                 "ide_version", "part", "device", "edu_provisional")


def vendor_bitstream(row):
    """The vendor `.fs` this row measured, or `None` if it is not on disk."""
    entries = row.get("vendor_fs") or []
    if not entries:
        return None
    path = entries[0].get("path")
    return path if path and os.path.exists(path) else None


def redo(row, shape, design_root, level=None):
    """One repaired row: the vendor half kept, the open half rebuilt."""
    from fuzz.gw5ast138c.harness import equiv, evidence, gen, openflow

    spec = gen.load_shape(shape)
    sweep_value = list(row["sweep"].values())[0]
    design_dir = os.path.join(design_root, row["run_id"])
    if vendor_bitstream(row) is None:
        raise SystemExit(
            f"{row['run_id']}: no vendor bitstream on disk -- redoing the open "
            f"half of a run whose oracle output is gone would silently spend a "
            f"vendor run")

    kept = {k: row[k] for k in VENDOR_FIELDS if k in row}
    base = dict(row, verdict="aborted", level=level or row.get("level", "E1"))

    open_result = openflow.run_openflow(
        design_dir, top_module=spec.top_module,
        extra_gpio=gen.pack_flags_of(spec, sweep_value),
        vopts=gen.nextpnr_vopts_of(spec, sweep_value),
        base_gpio=() if gen.pack_flags_are_complete(spec)
        else openflow.DEFAULT_PACK_GPIO)
    open_logs = [step["log_path"] for step in open_result["steps"]
                 if step.get("log_path")]
    open_fragment = openflow.evidence_fields(
        open_result["provenance"], open_log=open_logs or None,
        open_fs=open_result["fs_path"],
        wall_clock_s=row.get("wall_clock_s") or {})
    if not open_result["ok"]:
        refusal = open_result.get("refused")
        if refusal:
            return evidence.adapt(base, open_fragment, kept,
                                  verdict="refused",
                                  notes=f"open flow refused: {refusal}")
        return evidence.adapt(
            base, open_fragment, kept,
            notes=f"open flow failed: {open_result['returncodes']}")

    equiv_result = equiv.compare(design_dir, spec, level=base["level"])
    return evidence.adapt(base, open_fragment, kept,
                          **equiv.evidence_fields(equiv_result))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="redo_open_half")
    parser.add_argument("--rows", required=True,
                        help="the batch's <batch_id>.rows.jsonl")
    parser.add_argument("--shape", required=True)
    parser.add_argument("--design-root", required=True)
    parser.add_argument("--level", default=None)
    parser.add_argument("--write", action="store_true",
                        help="rewrite --rows in place with the repaired rows")
    args = parser.parse_args(argv)

    rows = [json.loads(l) for l in open(args.rows, encoding="utf-8")
            if l.strip()]
    out = [redo(row, args.shape, args.design_root, args.level) for row in rows]
    for row in out:
        print("%-28s %s" % (row["run_id"], row["verdict"]))
    if args.write:
        with open(args.rows, "w", encoding="utf-8") as fh:
            for row in out:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        print("rewrote %s" % args.rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
