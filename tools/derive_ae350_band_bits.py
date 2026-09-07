#!/usr/bin/env python3
"""Which bits of `ttyp` 224/228 an AE350 design sets that apicula does not model.

The AE350's "configuration fuse set" was measured by keeping, of the bits that
differ between an AE350 design and the same design without the block, those in
tile types 224 and 228 that belong to no pip and to no bel `modes`/`flags`
table -- 77 bits over 9 tiles.  That filter omits the tile types' `shortval`
tables, and those tile types are ordinary CLS logic tiles: `LUT`, `CLS0`-`CLS3`
live exactly in tile-bitmap rows 10-11, where all 77 bits are.

This tool computes both filters side by side over any set of bitstreams, so the
claim "the block sets a configuration fuse" can be checked rather than quoted.

    python -m tools.derive_ae350_band_bits <name>=<path.fs> [...]
"""
import argparse
import json
import sys

#: The two tile types the block's port columns pass through.
BAND_TTYPS = (224, 228)


def band_tiles(db):
    """`[(row, col)]` of every tile of a band type."""
    return [(r, c) for r, row in enumerate(db.grid)
            for c, ttyp in enumerate(row) if ttyp in BAND_TTYPS]


def _fuse_coords(table, into):
    """Collect every `(row, col)` fuse coordinate of a nested chipdb table."""
    if isinstance(table, dict):
        for value in table.values():
            _fuse_coords(value, into)
    elif isinstance(table, (set, frozenset, list, tuple)):
        for item in table:
            if (isinstance(item, (tuple, list)) and len(item) == 2
                    and all(isinstance(v, int) for v in item)):
                into.add(tuple(item))
            else:
                _fuse_coords(item, into)


def routing_and_bel_coords(db, ttyp):
    """The bits the original filter subtracted: pips and bel mode/flag fuses."""
    tile = db.tiles[ttyp]
    coords = set()
    _fuse_coords(getattr(tile, 'pips', None) or {}, coords)
    _fuse_coords(getattr(tile, 'clock_pips', None) or {}, coords)
    for bel in (getattr(tile, 'bels', None) or {}).values():
        _fuse_coords(getattr(bel, 'modes', None) or {}, coords)
        _fuse_coords(getattr(bel, 'flags', None) or {}, coords)
    return coords


def modelled_coords(db, ttyp):
    """Every bit of the tile type some chipdb table owns, `shortval` included."""
    coords = routing_and_bel_coords(db, ttyp)
    for table in ('shortval', 'longval', 'longfuses'):
        _fuse_coords((getattr(db, table, {}) or {}).get(ttyp, {}), coords)
    return coords


def set_bits(db, path, owned_by):
    """`{(row, col): {(i, j)}}` -- set bits of the band no table in `owned_by` owns."""
    from apycula import bslib, chipdb

    tiles = chipdb.tile_bitmap(db, bslib.read_bitstream(path)[0], empty=True)
    owned = {ttyp: owned_by(db, ttyp) for ttyp in BAND_TTYPS}
    out = {}
    for row, col in band_tiles(db):
        tile = tiles.get((row, col))
        if tile is None:
            continue
        skip = owned[db.grid[row][col]]
        bits = {(i, j) for i, line in enumerate(tile)
                for j, value in enumerate(line) if value and (i, j) not in skip}
        if bits:
            out[(row, col)] = bits
    return out


def report(db, named_paths):
    """`{name: {filter: {"bits": n, "tiles": {"x,y": [[i, j], ...]}}}}`."""
    out = {}
    for name, path in named_paths:
        entry = {}
        for label, owned_by in (('routing_and_bels', routing_and_bel_coords),
                                ('every_modelled_table', modelled_coords)):
            bits = set_bits(db, path, owned_by)
            entry[label] = {
                'bits': sum(len(v) for v in bits.values()),
                'tiles': {f'{col},{row}': sorted(map(list, coords))
                          for (row, col), coords in sorted(bits.items())},
            }
        out[name] = entry
    return out


def main(argv=None):
    """CLI entry point; prints the two filters' counts as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bitstreams', nargs='+', metavar='NAME=PATH')
    parser.add_argument('--device', default='GW5AST-138C')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    import apycula
    import os
    from apycula import chipdb

    db = chipdb.load_chipdb(os.path.join(os.path.dirname(apycula.__file__),
                                         f'{args.device}.msgpack.xz'))
    named = [tuple(spec.split('=', 1)) for spec in args.bitstreams]
    result = report(db, named)
    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        for name, entry in result.items():
            print(f"{name}: routing_and_bels={entry['routing_and_bels']['bits']} "
                  f"every_modelled_table={entry['every_modelled_table']['bits']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
