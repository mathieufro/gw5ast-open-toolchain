"""P1.T19 analyser: map each vendor PLL site name to a 138C chipdb tile group.

One vendor run per site (`fuzz/gw5ast138c/shapes/clocking_pll_trace.py`, one
hard `PLL` pinned by `INS_LOC "dut_pll" PLL_<side>[<n>]`). This script decodes
each run's `run.fs` into per-tile bitmaps and reports, for every one of
`P1.T17`'s twelve candidate three-tile groups, how many bits that group carries.

The discrimination is total, not statistical: with exactly one PLL in the
design, the constrained site's three tiles carry bits and the other eleven
groups are all-zero, so no baseline run and no cross-run subtraction is needed.

Usage:
    GOWINHOME=... PYTHONPATH=<apicula worktree> \\
        python evidence/plla/gen_trace_138c.py <batch-design-dir> [out.json]
"""
import json
import os
import sys
from pathlib import Path

from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap
import importlib.resources as ir

#: `P1.T17` anchors: `(row, col)` of the lowest-column tile of each three-tile
#: `shortval[35]` run, in the order the shape sweeps the site names.
ANCHORS = [
    (27, 1), (45, 0), (63, 0), (81, 1),
    (27, 177), (45, 178), (63, 178), (81, 177),
    (108, 28), (108, 32), (108, 146), (108, 150),
]

SITES = [
    "PLL_L[0]", "PLL_L[1]", "PLL_L[2]", "PLL_L[3]",
    "PLL_R[0]", "PLL_R[1]", "PLL_R[2]", "PLL_R[3]",
    "PLL_B[0]", "PLL_B[1]", "PLL_B[2]", "PLL_B[3]",
]


def group_bits(tiles, anchor):
    """Bits set in each of the three tiles of the group anchored at `anchor`."""
    row, col = anchor
    out = []
    for dc in range(3):
        tile = tiles.get((row, col + dc))
        out.append(int(sum(sum(r) for r in tile)) if tile is not None else None)
    return out


def main(argv):
    design_root = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None
    db = cdb.load_chipdb(str(ir.files('apycula') / 'GW5AST-138C.msgpack.xz'))

    runs = sorted(p for p in design_root.iterdir()
                  if (p / 'run/impl/pnr/run.fs').is_file())
    results = []
    for idx, run_dir in enumerate(runs):
        bitmap, _hdr, _ftr, _slots = read_bitstream(
            str(run_dir / 'run/impl/pnr/run.fs'))
        tiles = tile_bitmap(db, bitmap, empty=True)
        counts = {a: group_bits(tiles, a) for a in ANCHORS}
        hot = [a for a, c in counts.items() if any(c)]
        results.append({
            'run_dir': run_dir.name,
            'site': SITES[idx] if idx < len(SITES) else None,
            'hot_anchors': [list(a) for a in hot],
            'bits': {f'{a[0]},{a[1]}': counts[a] for a in ANCHORS},
        })
        print(f"{run_dir.name:52s} site={results[-1]['site']:10s} "
              f"hot={[tuple(a) for a in hot]} "
              f"bits={[counts[a] for a in hot]}")

    unique = all(len(r['hot_anchors']) == 1 for r in results)
    print(f"\nruns={len(results)} single_hot_group_every_run={unique} "
          f"distinct_anchors={len({tuple(r['hot_anchors'][0]) for r in results if r['hot_anchors']})}")
    if out_path:
        out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')
        print(f"wrote {out_path}")
    return 0 if unique else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
