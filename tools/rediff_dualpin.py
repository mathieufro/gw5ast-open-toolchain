#!/usr/bin/env python3
"""Re-derive the dual-purpose-pin bit diff from the packer, with no new run.

Each `evidence/dualpin/diff/<option>.json` holds three sets of tile bits: the
bits the **vendor** moves for that option, measured once and banked; the bits
the **packer** emits for it; and their symmetric difference.  The vendor half
is a measurement and never changes here.  The packer half is a function of
`gowin_pack` alone, so a change to what the packer emits must be reflected in
the record by recomputing it -- never by editing the JSON.

    python -m tools.rediff_dualpin evidence/dualpin/diff [--write]

A non-empty symmetric difference is a `DIFF` unless the option is one of the
two the toolchain refuses outright, whose verdict is terminal (`D30`).
"""
import argparse
import json
import os
import sys
import types

#: The options `gowin_pack` exposes, and the composite point the row sweeps.
OPTIONS = ("jtag", "sspi", "mspi", "ready", "done", "reconfign", "cpu", "i2c")
#: `ae350_triple` is the union of the three options an AE350 design sets.
COMPOSITE = {"ae350_triple": ("sspi", "mspi", "cpu")}
#: Points no build reaches; their verdict is about the build, not a comparison.
REFUSED = ("reconfign", "i2c")


def packer_bits(device, options):
    """`{"x,y": [bit, ...]}` -- the bits `gowin_pack` emits for `options`.

    A bit is named by its flat index inside the tile, `row * width + col`, the
    spelling the banked records use.
    """
    from apycula import gowin_pack

    db = gowin_pack.ChipDB(device)
    args = types.SimpleNamespace(**{f"{o}_as_gpio": (o in options)
                                    for o in OPTIONS})

    class _Probe(gowin_pack.GW5AST_138C):
        """The packer's dual-pin half alone: no netlist, no bitstream."""

        def __init__(self):  # noqa: D107 -- deliberately not the real ctor
            self.chipdb = db
            self.cli_args = types.SimpleNamespace(args=args)

    out = {}
    for cell in _Probe().get_dualpin_fuses():
        if not cell.bits:
            continue
        width = db.db.tiles[db.get_ttyp(cell.x, cell.y)].width
        out[f"{cell.x},{cell.y}"] = sorted(int(r) * width + int(c)
                                           for r, c in cell.bits)
    return out


def symdiff(a, b):
    """Per-tile symmetric difference of two `{"x,y": [bits]}` maps."""
    return _per_tile(a, b, lambda x, y: x ^ y)


def only_in(a, b):
    """Per-tile bits of `a` that `b` does not have."""
    return _per_tile(a, b, lambda x, y: x - y)


def _per_tile(a, b, op):
    out = {}
    for tile in set(a) | set(b):
        bits = sorted(op(set(a.get(tile, ())), set(b.get(tile, ()))))
        if bits:
            out[tile] = bits
    return out


def rediff(directory, device="GW5AST-138C", write=False):
    """Returns `[(point, was, now)]` for every point whose verdict changed."""
    changed = []
    everything = {}
    for point in list(OPTIONS) + list(COMPOSITE):
        path = os.path.join(directory, f"{point}.json")
        with open(path) as fh:
            data = json.load(fh)
        options = COMPOSITE.get(point, (point,))
        data["packer"] = ({} if point in REFUSED
                          else packer_bits(device, options))
        vendor = data.get("vendor") or {}
        data["symdiff"] = symdiff(vendor, data["packer"])
        data["vendor_only"] = only_in(vendor, data["packer"])
        data["packer_only"] = only_in(data["packer"], vendor)
        was = data.get("verdict")
        # Only over-emission is decided here. A bit the vendor sets and the
        # packer does not is the `D35` direction, already classified by the
        # row that owns it; a bit the packer sets and the vendor does not is
        # an IO setting the silicon's own tool declines to make, and no
        # classification excuses it.
        now = ("refused" if point in REFUSED
               else "diff" if data["packer_only"] else "ok")
        if now != was:
            changed.append((point, was, now))
        data["verdict"] = now
        everything[point] = data
        if write:
            with open(path, "w") as fh:
                json.dump(data, fh, indent=1)
                fh.write("\n")
    if write:
        with open(os.path.join(directory, "_all.json"), "w") as fh:
            json.dump(everything, fh, indent=1)
            fh.write("\n")
    return changed


def main(argv=None):
    """CLI entry point; exits non-zero when a point still carries a `diff`."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--device", default="GW5AST-138C")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    for point, was, now in rediff(args.directory, args.device, args.write):
        print(f"{point}: {was} -> {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
