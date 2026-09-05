"""P1.T25 -- reduce the trace results to the DHCEN `CE` wire table.

Reads the `trace-result*.json` files `probe_dhce.py` wrote and emits
`ce-wires-138c.json` / `ce-wires-138c.md`: one `(side, idx, row, col, wire)`
row per DHCE site.

Identification rule, stated once so the artefact is auditable:

* Only the `tie_resetn` runs are used. With `CLKDIV.RESETN` driven from a pin
  there are three IO-driven nets ending inside the HCLK block cells (the
  enables, the resets and the `CALIB` constant) and all three have exactly one
  end per instance, so no structural rule can separate them. Tying `RESETN`
  off leaves two.
* The remaining two are separated by the **control run** (`0` DHCE, `24`
  CLKDIV, `trace-result-control.json`): the end-wire set that still appears
  when there is no DHCE in the design at all is the `CLKDIV` `CALIB` net. The
  other one is the enable net. It is an error if that leaves anything but one
  candidate.
* `idx` is the vendor's **allocation order** inside a block, read off the
  incremental sweep (`n`, `n+1`, ... each adding exactly one site). It is a
  hypothesis for `HCLK_IN{idx}`, not a measurement of the multiplexer number;
  `P1.T26` must treat it as such. Blocks whose four sites were never observed
  arriving one at a time carry `order_measured: false` and are ordered by the
  canonical order the measured blocks agree on.
"""
import argparse
import glob
import json
import os

HCLK_CELLS = [(27, 0), (27, 181), (81, 0), (81, 181), (108, 64), (108, 117)]
GRID_ROWS, GRID_COLS = 109, 182
CAPACITY = 24


def side_of(row, col):
    if col == 0:
        return "L"
    if col == GRID_COLS - 1:
        return "R"
    if row == GRID_ROWS - 1:
        return "B"
    return "T"


def _bare(wire):
    """`R82C1_C2` -> `C2`; the wire name as the chipdb tables spell it."""
    return wire.split("_", 1)[1] if "_" in wire else wire


def load_traces(paths):
    out = {}
    for path in paths:
        doc = json.load(open(path, encoding="utf-8"))
        for key, trace in doc.get("traces", {}).items():
            out.setdefault(int(key), []).append((path, trace))
    return out


def calib_wires(control_path):
    doc = json.load(open(control_path, encoding="utf-8"))
    trace = doc["traces"]["0"]
    for cand in trace["candidates"]:
        if len(cand["ends"]) == CAPACITY:
            return {_bare(e[2]) for e in cand["ends"]}
    raise SystemExit("control run has no 24-end candidate")


def enable_ends(trace, n, calib):
    hits = []
    for cand in trace["candidates"]:
        if len(cand["ends"]) != n:
            continue
        names = {_bare(e[2]) for e in cand["ends"]}
        if names & calib:
            continue
        hits.append(cand)
    if len(hits) != 1:
        return None
    return {(e[0], e[1], _bare(e[2])) for e in hits[0]["ends"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--control", default=None)
    args = ap.parse_args()

    control = args.control or os.path.join(args.dir, "trace-result-control.json")
    calib = calib_wires(control)

    paths = sorted(p for p in glob.glob(os.path.join(args.dir, "trace-result*.json"))
                   if "control" not in p and p.endswith(("tieresetn.json",
                                                         "1620.json",
                                                         "1719.json")))
    traces = load_traces(paths)

    sets = {}
    for n in sorted(traces):
        for _path, trace in traces[n]:
            ends = enable_ends(trace, n, calib)
            if ends is not None:
                sets[n] = ends
                break

    ns = sorted(sets)
    full = sets[max(ns)]
    assert len(full) == CAPACITY, f"largest point has {len(full)} sites"

    # first appearance of each site along the incremental sweep
    first_seen, prev_n, seen = {}, None, set()
    for n in ns:
        added = sets[n] - seen
        step = n - (prev_n or 0)
        for site in added:
            # resolvable only when the step added exactly as many sites as it
            # advanced the instance count
            first_seen[site] = (n, len(added) == step)
        seen |= sets[n]
        prev_n = n

    per_block = {}
    for site in full:
        per_block.setdefault((site[0], site[1]), []).append(site)

    # canonical order, learned from the blocks whose order was measured
    canonical = []
    for block, sites in per_block.items():
        ordered = sorted(sites, key=lambda s: first_seen.get(s, (999, False))[0])
        if all(first_seen.get(s, (0, False))[1] for s in sites) and \
                len({first_seen[s][0] for s in sites}) == len(sites):
            names = [s[2] for s in ordered]
            if names not in canonical:
                canonical.append(names)

    entries = []
    for block in sorted(per_block):
        sites = per_block[block]
        measured = (all(first_seen.get(s, (0, False))[1] for s in sites) and
                    len({first_seen[s][0] for s in sites}) == len(sites))
        if measured:
            ordered = sorted(sites, key=lambda s: first_seen[s][0])
        else:
            order = next((c for c in canonical
                          if set(c) == {s[2] for s in sites}), None)
            if order is None:
                ordered = sorted(sites, key=lambda s: s[2])
            else:
                ordered = sorted(sites, key=lambda s: order.index(s[2]))
        for idx, site in enumerate(ordered):
            entries.append({
                "side": side_of(site[0], site[1]),
                "idx": idx,
                "row": site[0],
                "col": site[1],
                "wire": site[2],
                "order_measured": bool(measured),
                "first_seen_n": first_seen.get(site, (None, False))[0],
            })

    doc = {
        "device": "GW5AST-138C",
        "part": "GW5AST-LV138PG484AC1/I0, device_version C",
        "primitive": "DHCE",
        "apicula_name": "DHCEN",
        "enable_port": "CEN",
        "capacity": CAPACITY,
        "hclk_cells": [list(c) for c in HCLK_CELLS],
        "sweep_points_used": ns,
        "calib_wires": sorted(calib),
        "entries": sorted(entries, key=lambda e: (e["row"], e["col"], e["idx"])),
    }
    out_json = os.path.join(args.dir, "ce-wires-138c.json")
    json.dump(doc, open(out_json, "w", encoding="utf-8"), indent=1)
    print("wrote", out_json, len(entries), "entries")

    by_side = {}
    for e in doc["entries"]:
        by_side.setdefault(e["side"], []).append(e)
    print(json.dumps({s: [(e["row"], e["col"], e["wire"]) for e in v]
                      for s, v in by_side.items()}, indent=1))


if __name__ == "__main__":
    main()
