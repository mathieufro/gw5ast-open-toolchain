#!/usr/bin/env python3
"""Re-derive a stored evidence row's verdict from the fields it already carries.

`spec-harness.md` §5.4 makes both halves of the decode check required, but
`equiv.evidence_fields` used to compute `verdict` from the set-level diff and
the raw residual alone, so a row could be published `verdict: ok` while its
own `decode_check` said `mismatch`.  This tool re-applies §5.2/§5.4 to rows
that are already on disk -- it re-reads nothing, re-runs nothing, and touches
only the `verdict` field (plus a one-line note saying it did).

    python -m tools.rederive_verdicts evidence/clkdiv/runs.jsonl [--write]
"""
import argparse
import json
import sys

#: Appended once to every row whose verdict this tool changed.
NOTE = ("verdict re-derived (spec-harness.md 5.4: decode_check and the "
        "symmetric residual are verdict terms)")


def rederive(row):
    """The §6 verdict this row's own fields imply, or its verdict unchanged.

    `aborted` and `refused` are terminal statements about the *build*, not
    about a comparison, so they are never re-derived into `diff`.
    """
    # `aborted` and `refused` are terminal, and a row with no verdict is not
    # an equivalence row at all. `diff` is terminal in the other direction:
    # this tool exists to catch a row published `ok` that its own fields
    # contradict, and it never argues a recorded difference away.
    if row.get("verdict") in (None, "aborted", "refused", "diff"):
        return row.get("verdict")
    diff_count = row.get("diff_count") or {}
    set_diffs = sum(int(diff_count.get(k, 0) or 0)
                    for k in ("cells", "attrs", "conns"))
    over_emitted = row.get("fuses_over_emitted") or []
    # `n/a` is what a row that is not an equivalence comparison records -- a
    # note or a measurement -- and the absence of a check is not its failure.
    decode = row.get("decode_check") or {}
    decode_failed = any(v not in ("ok", "n/a") for v in decode.values())
    # Only §5.1b's enumerated shape is re-derivable. An older writer's
    # `{tile: count}` summary says a residual exists but not whether it was
    # enumerated, which is exactly the distinction the verdict turns on.
    unexplained = row.get("unexplained_bits")
    if not isinstance(unexplained, list):
        unexplained = []
    if set_diffs or unexplained or over_emitted or decode_failed:
        return "diff"
    return "ok"


def unguarded(rows):
    """Run ids whose over-emission the row cannot answer for.

    A row written before the symmetric residual existed carries no
    `fuses_over_emitted` field, and nothing in it can be re-derived into one:
    the field is a measurement on two bitstreams, not a function of the other
    fields. Naming those rows is the honest alternative to letting their `ok`
    stand as if it had been checked.
    """
    return [row.get("run_id") for row in rows
            if "fuses_over_emitted" not in row
            and row.get("verdict") not in ("aborted", "refused")]


def rederive_file(path, write=False):
    """Returns the rows whose verdict changed, as `(run_id, was, now)`."""
    rows = [json.loads(line) for line in open(path) if line.strip()]
    for run_id in unguarded(rows):
        print(f"{run_id}: no fuses_over_emitted field; over-emission unchecked")
    changed = []
    for row in rows:
        now = rederive(row)
        if now == row.get("verdict"):
            continue
        changed.append((row.get("run_id"), row.get("verdict"), now))
        row["verdict"] = now
        notes = row.get("notes") or ""
        if NOTE not in notes:
            row["notes"] = f"{notes} | {NOTE}".strip(" |") if notes else NOTE
    if write and changed:
        with open(path, "w") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rows", nargs="+", help="runs.jsonl file(s)")
    parser.add_argument("--write", action="store_true",
                        help="rewrite the rows in place (default: report only)")
    args = parser.parse_args(argv)
    total = 0
    for path in args.rows:
        changed = rederive_file(path, write=args.write)
        total += len(changed)
        for run_id, was, now in changed:
            print(f"REDERIVED {path} {run_id} {was} -> {now}")
        print(f"SUMMARY {path} changed={len(changed)}")
    print(f"TOTAL changed={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
