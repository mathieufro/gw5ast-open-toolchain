"""Merge a `clocking_pll` batch's rows into `evidence/plla/runs.jsonl`.

`P1.T23`, reused by `P1.T41`-`T43`.  The batch's human label is an argument
rather than a constant: batches B, C and D are not "batch A", and a row whose
note says otherwise misattributes its own measurement.

The batch runner records `sweep` as `{spec.sweep_axis: <point name>}`, i.e.
`{"pll_point": "idiv_009"}` -- the harness's generic shape.  The evidence
schema wants the sweep expressed in the terms the campaign is swept in, so
this rewrites it to the two-key form the shape itself defines:

    {"axis": "IDIV", "IDIV_SEL": 9}

which makes "differs from its axis baseline in exactly one key" a property of
the row rather than of a lookup table (`test_plla_sweep_batch_a_rows`).  The
`notes` field gains the point's operating point and the attribution verdict
from `sweep-a-138c.json`, so a reader never has to open two files to see what
a row measured.

Nothing else in the row is touched, and a run id already present in
`runs.jsonl` is skipped rather than duplicated -- the file is append-only.

Usage:
    python merge_sweep_rows.py <batch rows.jsonl> <runs.jsonl> \
        [<attribution.json>] [<label>]
"""
import json
import sys
from pathlib import Path

from fuzz.gw5ast138c.shapes import clocking_pll as shape


def main(argv):
    batch_rows = Path(argv[1])
    runs_path = Path(argv[2])
    attribution = json.loads(Path(argv[3]).read_text()) \
        if len(argv) > 3 and argv[3] != "-" else None
    label = argv[4] if len(argv) > 4 else "P1.T23 batch A"
    by_run = {r["run_id"]: r for r in (attribution or {}).get("runs", [])
              if "run_id" in r}

    points = shape.points()
    existing = set()
    if runs_path.is_file():
        for line in runs_path.read_text().splitlines():
            if line.strip():
                existing.add(json.loads(line)["run_id"])

    appended = 0
    out = []
    for line in batch_rows.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["run_id"] in existing:
            continue
        point = row["sweep"].get(shape.SPEC.sweep_axis)
        if point not in points:
            raise SystemExit(f"{row['run_id']}: unknown point {point!r}")
        axis, value = points[point]
        row["sweep"] = {"axis": axis.name, axis.param: value}
        attr = by_run.get(row["run_id"], {})
        note = (f"{label}, point {point}, site {axis.site_of(value)}: "
                f"{axis.param}={value}, FCLKIN={axis.params(value)['FCLKIN']} "
                f"Fpfd={axis.fpfd(value):.4f} FVCO={axis.fvco(value):.4f} "
                f"CLKOUT0={axis.clkout0(value):.4f} MHz"
                f"{' (axis baseline)' if value == axis.baseline else ''}.")
        if attr:
            # An attribute the vendor's own table leaves unnamed still has an
            # id, and the id is the measurement -- so the note carries both.
            resolved = attr["names"] or attr.get("attr_ids") or []
            note += (f" Moved {attr['moved_bits']} bits in tiles "
                     f"{attr['moved_tiles']} -> {resolved}; "
                     f"attributed as expected: "
                     f"{attr.get('verified_vs_t22', attr.get('verified'))}.")
        row["notes"] = f"{note} {row.get('notes', '')}".strip()
        out.append(row)
        appended += 1

    with runs_path.open("a") as fh:
        for row in out:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"appended {appended} rows to {runs_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
