#!/usr/bin/env python3
"""Decode the role every `AE350_SOC` tap wire plays in the vendor's routing.

A tap's direction cannot be read off the `.dat` table it came from, and a name
regex over the wire class is an assumption, not a measurement. The vendor's own
bitstream settles it: die row 0 carries no bels, so every wire there is either
the *destination* of a pip the vendor set -- the fabric drives it, so the block
reads it -- or the *source* of one -- the block drives it and the fabric reads
it. Nothing in row 0 can be both.

This tool decodes both banked runs with apicula's own unpacker, keeps only the
wire classes a tap can name, and writes the result as a small text fixture so
the direction test never needs the 34 MB bitstream. The no-block baseline is
decoded too: it holds no row-0 tile in the block's band at all, which is what
makes every band pip in the other run attributable to the block.

Usage::

    python3 tools/derive_ae350_pip_roles.py           # rewrite the fixture
    python3 tools/derive_ae350_pip_roles.py --check   # fail if it is stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import paths  # noqa: E402

DEVICE = "GW5AST-138C"

#: The banked vendor runs. `ae350-tilewires` drives or captures every one of the
#: block's 149 ports; `ae350-baseline` is the same vehicle with the block
#: removed.
DATASTORE = Path(os.environ.get(
    "FL_OTC_DATASTORE", "/Users/alex/fine-line-data/open-toolchain-gw5ast"))
RUNS = {"ae350": "ae350-tilewires", "baseline": "ae350-baseline"}

#: Wire classes an `AE350_SOC` tap can name. Everything else in a row-0 tile is
#: ordinary inter-tile routing and says nothing about the block.
TAP_WIRE = re.compile(r"(?:A|B|C|D|F|Q|OF|CE|CLK|LSR)\d+\Z")

#: Where the fixture lands: inside the apicula checkout, so its test suite
#: stays self-contained and upstreamable.
FIXTURE_RELPATH = Path("tests") / "data" / "ae350-pip-roles-138c.json"


def fixture_path() -> Path:
    root = paths.apicula_root()
    if root is None:
        raise SystemExit("apicula checkout not found; set $FL_APICULA")
    return Path(root) / FIXTURE_RELPATH


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode(fs_path: Path):
    """`{(row, col): ({destination wires}, {source wires})}` for die row 0."""
    from apycula import chipdb
    from apycula import gowin_unpack
    from apycula.bslib import read_bitstream

    root = Path(paths.apicula_root())
    db = chipdb.load_chipdb(str(root / "apycula" / f"{DEVICE}.msgpack.xz"))
    gowin_unpack._device = DEVICE
    gowin_unpack._pinout = db.pinout[DEVICE][gowin_unpack._packages[DEVICE]]

    bitmap = read_bitstream(str(fs_path))[0]
    tiles = chipdb.tile_bitmap(db, bitmap)
    roles = {}
    for (row, col), tile in sorted(tiles.items()):
        if row != 0:
            continue
        _bels, pips, clock_pips = gowin_unpack.parse_tile_(
            db, row, col, tile, tiles, noiostd=False)
        merged = dict(pips)
        merged.update(clock_pips)
        dest = {w for w in merged if TAP_WIRE.fullmatch(w)}
        src = {w for w in merged.values() if TAP_WIRE.fullmatch(w)}
        roles[(row, col)] = (dest, src)
    return roles


def build():
    payload = {
        "device": DEVICE,
        "primitive": "AE350_SOC",
        "record": ("per die-row-0 tile, the tap-class wires the vendor's "
                   "routing ends a pip on (dest) and starts a pip from (src); "
                   "row 0 carries no bels, so a wire in dest is driven by the "
                   "fabric and a wire in src is driven by whatever the tile "
                   "does not contain -- the hard block"),
        "decoded_with": "apycula.gowin_unpack.parse_tile_ over chipdb.tile_bitmap",
        "runs": {},
        "tiles": {},
    }
    for label, run in RUNS.items():
        fs_path = DATASTORE / run / "run" / "impl" / "pnr" / "run.fs"
        payload["runs"][label] = {"run": run, "sha256": sha256(fs_path)}
        for (row, col), (dest, src) in decode(fs_path).items():
            entry = payload["tiles"].setdefault(f"{row},{col}", {})
            entry[f"{label}_dest"] = sorted(dest)
            entry[f"{label}_src"] = sorted(src)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed fixture has drifted")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    out = args.out or fixture_path()
    payload = build()
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if args.check:
        if not out.is_file() or out.read_text() != text:
            print(f"STALE {out}", file=sys.stderr)
            return 1
        print(f"OK {out}")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out} ({len(payload['tiles'])} row-0 tiles, "
          f"{len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
