#!/usr/bin/env python3
"""Render the per-sweep-point verdict table of a slug's `runs.jsonl`.

Used to build `summary.md` for `clkdiv` and `clkdiv2` (`P1.T14`/`P1.T15`) so
the table in the prose is generated from the rows, never retyped.
"""
import argparse
import json
import sys


def point(row):
    sweep = row.get("sweep") or {}
    if "DIV_MODE" in sweep:
        label = "DIV_MODE=" + str(sweep["DIV_MODE"])
        # The baseline is the same design at the same default: only the shape
        # tells the two rows apart, so the table has to say which is which.
        if str(row.get("shape", "")).endswith("_baseline"):
            label += " (baseline run)"
        return label
    if "lane" in sweep:
        return "lane %s (%s), RESETN=%s" % (sweep["lane"], sweep["input_path"],
                                            sweep["resetn"])
    return "placement=" + str(sweep.get("placement", "?"))


def residual_note(row):
    unexplained = row.get("unexplained_bits") or []
    if not unexplained:
        return "0"
    return "; ".join("%s:%s" % (e.get("category"), e.get("bits"))
                     for e in unexplained)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("rows")
    args = ap.parse_args(argv)
    rows = [json.loads(l) for l in open(args.rows) if l.strip()]
    print("| sweep point | level | verdict | cells | attrs | conns | "
          "unexplained residual | decode c1/c2 |")
    print("|---|---|---|---|---|---|---|---|")
    for row in rows:
        dc = row.get("diff_count") or {}
        dk = row.get("decode_check") or {}
        print("| `%s` | %s | **%s** | %s | %s | %s | %s | %s/%s |" % (
            point(row), row.get("level"), row.get("verdict"),
            dc.get("cells"), dc.get("attrs"), dc.get("conns"),
            residual_note(row), dk.get("c1"), dk.get("c2")))
    print()
    print("pips (whole-device statistic, never a verdict term, D32): "
          + ", ".join(str((row.get("diff_count") or {}).get("pips"))
                      for row in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
