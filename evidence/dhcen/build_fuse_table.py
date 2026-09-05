"""P1.T26 -- reduce the `p1-dhce-fuse` batch to the DHCE gate-fuse table.

Deterministic: re-derives the committed `fuse-138c.json` from the four vendor
`.fs` of batch `p1-dhce-fuse`, so the attribution is auditable without
re-running the oracle.

Method.  The sweep holds `n_div = 4` and `tie_resetn` constant and varies
`n_dhce = 0, 1, 2, 3`, so the only difference between adjacent points is one
more DHCE in the first-filled HCLK block, `(108, 64)`.  For each step the
block tile's moved fuses are computed, and intersected with the *gate fuses*
of the block's four HCLK input multiplexers -- the fuse each multiplexer's
three sources have in common, which `chipdb.gw5a_dhce_gate_fuses` computes
from the chipdb alone.  The result per step is exactly one bit, and it is the
bit of the multiplexer whose index is the DHCE's allocation index.

The remaining moved bits per step are the enable net's own routing into the
tile, and are reported as the residual rather than swept under the rug.

    PYTHONPATH=<apicula worktree> python build_fuse_table.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.getcwd())
from apycula import chipdb as _chipdb                              # noqa: E402
from fuzz.gw5ast138c.harness.attribute import load_tile_bitmaps    # noqa: E402
from fuzz.gw5ast138c.harness.equiv import load_db                  # noqa: E402

DEVICE = 'GW5AST-138C'
FS_DIR = os.environ.get(
    'DHCE_FS_DIR',
    '/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/dhcen/fuse/fs')
BLOCK = (108, 64)            # (row, col) -- the first-filled HCLK block
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'fuse-138c.json')


def _pip_dests(db, block, bits):
    """Which ordinary tile pips the residual bits belong to.

    The residual of a DHCE step is the enable net's own routing into the block
    cell -- CIB pips whose destination is the `CEN` wire of that site (and the
    hops feeding it).  Naming the destinations makes that checkable rather than
    asserted.
    """
    want = set(bits)
    dests = set()
    for dest, srcs in db[block[0], block[1]].pips.items():
        for fuses in srcs.values():
            if set(fuses) & want:
                dests.add(dest)
    return dests


def _pip_bits(db, block, bits):
    want = set(bits)
    seen = set()
    for srcs in db[block[0], block[1]].pips.values():
        for fuses in srcs.values():
            seen |= set(fuses) & want
    return seen


def main():
    db = load_db(DEVICE)
    tb = {n: load_tile_bitmaps(f'{FS_DIR}/fz{n:02d}_div4.fs', db=db)
          for n in range(4)}
    key = (BLOCK[1], BLOCK[0])                    # load_tile_bitmaps keys (x, y)

    sites = db.extra_func[BLOCK]['dhcen']
    muxes = [s['pip'][1] for s in sites]
    gate = {m: sorted(_chipdb.gw5a_dhce_gate_fuses(db.hclk_pips[BLOCK], m))
            for m in muxes}
    gate_bits = {tuple(b) for bits in gate.values() for b in bits}

    steps = []
    for n in range(1, 4):
        a = np.asarray(tb[n - 1][key][1])
        b = np.asarray(tb[n][key][1])
        moved = {(int(r), int(c)) for r, c in np.argwhere(a != b)}
        on_gate = sorted(moved & gate_bits)
        residual = sorted(moved - gate_bits)
        predicted = [tuple(x) for x in gate[muxes[n - 1]]]
        steps.append({
            'n_dhce': n, 'site_idx': n - 1, 'mux': muxes[n - 1],
            'moved_in_block': sorted(moved),
            'gate_bits_moved': on_gate,
            'model_predicts': predicted,
            'agrees': on_gate == predicted,
            'residual_bits': residual,
            'residual_count': len(residual),
            'residual_pip_dests': sorted(_pip_dests(db, BLOCK, residual)),
            'residual_unattributed': sorted(
                set(residual) - _pip_bits(db, BLOCK, residual)),
        })

    other = {}
    for n in range(1, 4):
        tiles = []
        for k in sorted(set(tb[n - 1]) | set(tb[n])):
            if k == key:
                continue
            a = np.asarray(tb[n - 1].get(k, (None, np.zeros((0, 0))))[1])
            b = np.asarray(tb[n].get(k, (None, np.zeros((0, 0))))[1])
            if a.shape != b.shape or a.size == 0:
                continue
            d = int((a != b).sum())
            if d:
                tiles.append([k[0], k[1], d])
        other[str(n)] = tiles

    out = {
        'device': DEVICE, 'task': 'P1.T26', 'batch': 'p1-dhce-fuse',
        'block': list(BLOCK), 'muxes': muxes,
        'gate_fuses': {m: [list(b) for b in bits] for m, bits in gate.items()},
        'steps': steps,
        'other_tiles_moved': other,
        'site3_measured': False,
    }
    with open(OUT, 'w') as fh:
        json.dump(out, fh, indent=1)
    for s in steps:
        print(f"n={s['n_dhce']} idx={s['site_idx']} mux={s['mux']} "
              f"DIFF_COUNT={0 if s['agrees'] else 1} "
              f"gate_moved={s['gate_bits_moved']} predicted={s['model_predicts']} "
              f"RESIDUAL={s['residual_count']} "
              f"unattributed={len(s['residual_unattributed'])} "
              f"pip_dests={s['residual_pip_dests']}")
    print('other tiles moved per step:', other)
    return 0


if __name__ == '__main__':
    sys.exit(main())
