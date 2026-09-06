#!/usr/bin/env python3
"""Promote a harness batch's rows into a slug's `runs.jsonl` (P1.T14 / P1.T15).

`fuzz.gw5ast138c.harness` writes its rows to
`$OTC/evidence/_runs/<batch_id>.rows.jsonl`; the slug file is the reviewed
evidence.  This is the one step between them, and it does exactly three
things a batch cannot do for itself:

1. **Expands the `sweep` map.**  The batch records `{axis: value}` verbatim,
   so `clocking_clkdiv2` lands as `{"lane_resetn": [1, "pin"]}`.  A reader
   should not have to re-derive `chipdb.py:1748-1757`'s parity rule to learn
   which CLKDIV2 input path a row exercised, so the lane, the reset style and
   the resulting input path are written out as named keys.
2. **Justifies every `unexplained_bits` entry (`D35`).**  `equiv.residual()`
   names the category; `equiv.RESIDUAL_CATEGORIES` holds the one-line reason.
   A row may leave the list empty or enumerate it justified -- never
   enumerate it bare.
3. **Records artefact pruning honestly (`D99`).**  Vendor `run/` trees are
   ~70 MB each and the boot volume is near full, so everything except
   `run.fs`, `run.tr`, `run.vo` and `run.sdf` is deleted.  A row whose
   artefact this step removed says so in `notes` and has that path dropped
   from the artefact field, so no row ever points at something pruned.

Usage:

    python promote_rows.py --batch-rows <path>.rows.jsonl --slug clkdiv \
        [--design-dir <root>] [--prune] [--dry-run]
"""
import argparse
import json
import os
import shutil
import sys

#: Vendor artefacts worth keeping out of a `run/` tree.
KEEP = ("run.fs", "run.tr", "run.vo", "run.sdf")


def _harness():
    sys.path.insert(0, os.environ["PYTHONPATH"].split(os.pathsep)[0])
    from fuzz.gw5ast138c.harness import equiv, evidence
    return equiv, evidence


def expand_sweep(row):
    """`{axis: value}` -> named keys, per shape."""
    sweep = dict(row.get("sweep") or {})
    if "lane_resetn" in sweep:
        value = sweep.pop("lane_resetn")
        lane, resetn = (value if isinstance(value, (list, tuple))
                        else (0, str(value)))
        sweep["lane"] = int(lane)
        sweep["resetn"] = str(resetn)
        # chipdb.py:1748-1757: even lane -> HCLK_BUF_BO node, odd -> CLKDIV2_I pip
        sweep["input_path"] = "HCLK_BUF_BO" if int(lane) % 2 == 0 else "CLKDIV2_I"
    return sweep


def justify(unexplained, categories):
    """Every entry carries the category's own one-line reason (`D35`)."""
    out = []
    for entry in unexplained or []:
        item = dict(entry) if isinstance(entry, dict) else {"category": entry}
        name = item.get("category", "unknown")
        item.setdefault("justification", categories.get(
            name, f"category {name!r} has no RESIDUAL_CATEGORIES entry -- "
                  "unjustified, and the row says so rather than hiding it"))
        out.append(item)
    return out


def prune_run_tree(design_dir):
    """Delete everything in `<design_dir>/run` except the KEEP artefacts."""
    pnr = os.path.join(design_dir, "run", "impl", "pnr")
    removed = []
    if not os.path.isdir(pnr):
        return removed
    for name in sorted(os.listdir(pnr)):
        if name in KEEP:
            continue
        path = os.path.join(pnr, name)
        removed.append(path)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    for sub in ("gwsynthesis", "temp"):
        path = os.path.join(design_dir, "run", "impl", sub)
        if os.path.isdir(path):
            removed.append(path)
            shutil.rmtree(path)
    return removed


def drop_missing(row, fields=("vendor_fs", "open_fs", "sdf", "tr")):
    """Drop any artefact entry whose file is gone; say so in `notes` (D99)."""
    dropped = []
    for field in fields:
        kept = []
        for item in row.get(field) or []:
            path = item.get("path") if isinstance(item, dict) else item
            if path and not os.path.isfile(path):
                dropped.append(path)
                continue
            kept.append(item)
        row[field] = kept
    return dropped


def main(argv=None):
    ap = argparse.ArgumentParser(prog="promote_rows.py")
    ap.add_argument("--batch-rows", required=True, action="append")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--prune", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    equiv, evidence = _harness()
    written = 0
    for rows_path in args.batch_rows:
        for row in evidence.read_rows(rows_path):
            row = dict(row)
            row["sweep"] = expand_sweep(row)
            row["unexplained_bits"] = justify(row.get("unexplained_bits"),
                                              equiv.RESIDUAL_CATEGORIES)
            design_dir = None
            for item in (row.get("open_fs") or []):
                path = item.get("path") if isinstance(item, dict) else item
                if path:
                    design_dir = os.path.dirname(path)
            if args.prune and design_dir:
                removed = prune_run_tree(design_dir)
                if removed:
                    row["notes"] = (row.get("notes", "") +
                                    f" | artefact_pruned={len(removed)} vendor "
                                    f"run/ files under {design_dir}/run "
                                    f"(kept {', '.join(KEEP)}; D99)").strip(" |")
            dropped = drop_missing(row)
            if dropped:
                row["notes"] = (row.get("notes", "") +
                                " | artefact_pruned_paths=" +
                                json.dumps(dropped)).strip(" |")
            row = evidence.new_row(**{k: v for k, v in row.items()
                                      if k in evidence.REQUIRED_FIELDS})
            evidence.validate_row(row)
            if args.dry_run:
                print(json.dumps(row, sort_keys=True, default=str))
            else:
                evidence.append_row(row, args.slug)
            written += 1
    print(f"PROMOTED slug={args.slug} rows={written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
