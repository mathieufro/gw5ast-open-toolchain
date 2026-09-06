"""Read the ABSOLUTE value of a GW5AST-138C `PLL` attribute out of a `.fs`.

`P1.T41`.  `P1.T22`/`P1.T23` attributed fuses *differentially* -- which
attribute a moved bit belongs to -- which is the right instrument for a sweep
but cannot answer "what value did the vendor put here?".  Fitting the charge
pump needs the absolute value, so this module decodes one.

How the decode is exact, not a guess
------------------------------------
Every row of the 138C's `shortval[ttyp]['PLL']` table that mentions one of
these attributes has exactly **one** positive key (MEASURED: 63 rows for
`A_ICP_SEL`, 7 for `A_LPF_RES_SEL`, 15 for `FLDCOUNT`, 7 for `KVCO`, 127 each
for `A_MDIV_SEL`/`A_ODIV0_SEL`, and no row of any of them carries a second
positive or any negative key).  So an attribute owns a fixed *field* of bits --
the union of its values' fuse sets -- and a value is written by setting exactly
its own subset of that field.  The value present in a bitstream is therefore
the unique `v` whose fuse set equals `field & set_bits`; a decode that matches
zero values or more than one is reported as such and never guessed at.

Usage:
    python decode_pll_attrs_138c.py <run.fs> [<row> <col>]
"""
import importlib.resources as ir
import json
import sys

from apycula import attrids
from apycula import chipdb as cdb
from apycula.bslib import read_bitstream
from apycula.chipdb import tile_bitmap

#: `PLL_L[0]`, the site `P1.T22`/`P1.T23`/`P1.T41` measure at.
DEFAULT_TILE = (27, 1)

#: The attributes `GW5A.get_pll_attrvals` derives from `get_pll_pump` alone,
#: plus the loop-filter capacitor it writes as a constant.
PUMP_ATTRS = ("FLDCOUNT", "KVCO", "A_ICP_SEL", "A_LPF_RES_SEL", "A_LPF_CAP_SEL")

_DB = None


def db():
    """The packaged 138C chipdb, loaded once."""
    global _DB
    if _DB is None:
        _DB = cdb.load_chipdb(str(ir.files("apycula") / "GW5AST-138C.msgpack.xz"))
    return _DB


def fields(ttyp, attr_ids):
    """`{attr_id: {value: frozenset(fuses)}}` for one tile type."""
    table = db().shortval[ttyp]["PLL"]
    out = {a: {} for a in attr_ids}
    for (attr, value), attrval in db().logicinfo["PLL"].items():
        if attr not in out:
            continue
        fuses = set()
        for key, bits in table.items():
            if [k for k in key if k > 0] == [attrval]:
                fuses |= {tuple(b) for b in bits}
        out[attr][value] = frozenset(fuses)
    return out


def set_bits(tile):
    return {(r, c) for r, row in enumerate(tile) for c, v in enumerate(row) if v}


def decode(fs_path, tile=DEFAULT_TILE, names=PUMP_ATTRS):
    """`{name: value}` for one bitstream; `None` where the decode is not unique."""
    ids = {attrids.pll_attrids[n]: n for n in names}
    ttyp = db().grid[tile[0]][tile[1]]
    table = fields(ttyp, set(ids))
    bitmap, _h, _f, _s = read_bitstream(str(fs_path))
    bits = set_bits(tile_bitmap(db(), bitmap, empty=True)[tile])
    out = {}
    for attr_id, name in ids.items():
        values = table[attr_id]
        field = frozenset().union(*values.values()) if values else frozenset()
        observed = frozenset(bits & field)
        hits = sorted(v for v, f in values.items() if f == observed)
        out[name] = hits[0] if len(hits) == 1 else None
    return out


def main(argv):
    tile = (int(argv[2]), int(argv[3])) if len(argv) > 3 else DEFAULT_TILE
    print(json.dumps(decode(argv[1], tile), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
