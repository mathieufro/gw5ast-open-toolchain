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
NOTE = "verdict re-derived (spec-harness.md 5.4: decode_check is a verdict term)"


def rederive(row):
    """The §6 verdict this row's own fields imply, or its verdict unchanged.

    `aborted` and `refused` are terminal statements about the *build*, not
    about a comparison, so they are never re-derived into `diff`.
    """
    if row.get("verdict") in ("aborted", "refused"):
        return row.get("verdict")
    diff_count = row.get("diff_count") or {}
    set_diffs = sum(int(diff_count.get(k, 0) or 0)
                    for k in ("cells", "attrs", "conns"))
    unexplained = row.get("unexplained_bits") or []
    decode = row.get("decode_check") or {}
    decode_failed = any(v != "ok" for v in decode.values())
    if set_diffs or unexplained or decode_failed:
        return "diff"
    return "ok"


def rederive_file(path, write=False):
    """Returns the rows whose verdict changed, as `(run_id, was, now)`."""
    rows = [json.loads(line) for line in open(path) if line.strip()]
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
