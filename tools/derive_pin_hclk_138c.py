#!/usr/bin/env python3
"""Derive the GW5AST-138C package-pin -> bank -> HCLK-block table (`P3.T06`).

The artefact this writes, `evidence/iologic/pin-hclk-138c.json`, answers one
question for every I/O ball of the `GW5AST-LV138PG484AC1/I0`: *which HCLK
block can clock the IOLOGIC behind this pin, and how much of that answer is
device data rather than inference?* Every row carries its own derivation mark,
because the three columns do not have the same standing:

* **`DAT-DERIVED`** -- the ball's `IOB<n>{A,B}` site name, the bank it sits in
  and the `(row, col)` cell that site is, all read out of the shipped device
  files. The bank is read twice, from two independent vendor files -- the
  `.dat`'s `Bank` compatibility table (which is what `apycula.chipdb` builds
  `pin_bank` from) and the package pinout JSON `pindef` reads -- and the two
  must agree on every ball or this module raises.
* **`FSE-DERIVED`** -- whether the cell has an `IOLOGICA`/`IOLOGICB` at all,
  taken from the presence of `shortval` tables 21 and 22 in the cell's tile
  type, with the corner-tile exclusion `chipdb.fse_iologic` applies.
* **`ASSUMED`** -- the HCLK block and lane set. No shipped table relates an I/O
  cell to an HCLK block on this device: `chipdb.gw5_create_hclk_iol_pip`
  returns `False` for the 138C, and the 25A precedent it would be generalised
  from is a hand-written per-side rule, not device data. So the block here is
  the *nearest block on the same die edge* (`NEAREST_BLOCK_ON_SIDE`), which is
  a hypothesis for `P3.T07`'s reachability sweep to confirm or refute -- never
  evidence.

That split is also why `pin_to_hclk_entries` -- the list shaped like
`chipdb._gw5_pin_to_hclk`'s values, which the chipdb consumes directly -- is
**empty**. Its entries need a fabric wire name and an `hclknames` index per
pin, and neither is derivable from the device files; both come out of a vendor
run. Emitting a guessed wire there would put an unmeasured node in the routing
graph, so the table stays empty and the candidates sit beside it under
`clock_pin_candidates` until `P3.T07` measures them.

Usage::

    python3 tools/derive_pin_hclk_138c.py            # rewrite the artefact
    python3 tools/derive_pin_hclk_138c.py --check    # fail if it is stale
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402

#: The only device this pipeline targets (`LOOP-BRIEF` §6).
DEVICE = "GW5AST-138C"

#: The package the Tang Mega 138K SOM carries, and the only one measured.
PACKAGE = "PBGA484A"
PARTNUMBER = "GW5AST-LV138PG484AC1/I0"

#: The six HCLK blocks, MEASURED by `P1.T04`
#: (`evidence/hclk/topology-138c.md`): `(hclk_idx, row, col, side)`.
HCLK_BLOCKS = (
    (0, 27, 0, "left"),
    (1, 27, 181, "right"),
    (2, 81, 0, "left"),
    (3, 81, 181, "right"),
    (4, 108, 64, "bottom"),
    (5, 108, 117, "bottom"),
)

#: Lanes per block: four `CLKDIV`s, 24 in total, vendor-stated (`PA2017`) and
#: reproduced by `P1.T04`.
LANES_PER_BLOCK = (0, 1, 2, 3)

#: Banks carrying the DDR3 interface on this die (`shapes/__init__.DDR_BANKS`,
#: `D20c`/`D54`). A `LVCMOS*` setting on one of these is a thermal hazard, so
#: the table marks their pins rather than leaving a consumer to look it up.
DDR_BANKS = (6, 7)

#: Corner tiles `chipdb.fse_iologic` refuses an IOLOGIC on even though their
#: tile type carries `shortval` 21/22.
_NO_IOLOGIC_TTYPS = frozenset({48, 49, 50, 51})

#: `IO{side}{n}{A|B}` -- the site-name spelling `chipdb.pin_bank` is keyed by.
_SITE_RE = re.compile(r"^IO([TBLR])(\d+)([AB])$")

#: The rule that puts a pin on a block. Named in the artefact so a reader of
#: the JSON alone knows what the `ASSUMED` cells mean.
BLOCK_RULE = "NEAREST_BLOCK_ON_SIDE"

_OUT = os.path.join(paths.OTC_ROOT, "evidence", "iologic", "pin-hclk-138c.json")


class DerivationError(RuntimeError):
    """A vendor-data disagreement that must not be papered over."""


def _apycula():
    """Import `apycula` out of the apicula checkout, or say why it cannot."""
    root = paths.apicula_root()
    if root is None:
        raise DerivationError(
            "no apicula checkout carrying fuzz/gw5ast138c/harness/evidence.py; "
            "set $FL_APICULA")
    if root not in sys.path:
        sys.path.insert(0, root)
    if not os.environ.get("GOWINHOME"):
        raise DerivationError("GOWINHOME is not set; source $OTC/gate.env")
    from apycula import dat_parser, fse_parser, pindef  # noqa: E402
    return dat_parser, fse_parser, pindef


def site_cell(site, rows, cols):
    """`(row, col)` of an `IO{T,B,L,R}<n>{A,B}` site on a `rows` x `cols` die.

    The number in the name is the 1-based index `chipdb` reads the `.dat`
    `Bank` table with, so the cell index is one less; the other coordinate is
    the die edge the letter names. `IOT*` is included for completeness even
    though this device has none.
    """
    match = _SITE_RE.match(site)
    if match is None:
        raise DerivationError(f"site name {site!r} is not IO{{T,B,L,R}}<n>{{A,B}}")
    side, number, ab = match.group(1), int(match.group(2)), match.group(3)
    index = number - 1
    if side == "T":
        cell = (0, index)
    elif side == "B":
        cell = (rows - 1, index)
    elif side == "L":
        cell = (index, 0)
    else:
        cell = (index, cols - 1)
    if not (0 <= cell[0] < rows and 0 <= cell[1] < cols):
        raise DerivationError(f"site {site!r} resolves to {cell}, off a {rows}x{cols} die")
    return side, ab, cell


def nearest_block_on_side(side, cell):
    """The `hclk_idx` of the block nearest `cell` along its own die edge.

    Left- and right-edge pins are ranked by row, bottom-edge pins by column;
    a top-edge pin has no block on its edge at all and gets `None`. This is
    `BLOCK_RULE`, and it is a hypothesis -- see the module doc.
    """
    if side == "T":
        return None
    want = {"L": "left", "R": "right", "B": "bottom"}[side]
    axis = 1 if side == "B" else 0
    candidates = [(abs(cell[axis] - (col if side == "B" else row)), idx)
                  for idx, row, col, block_side in HCLK_BLOCKS if block_side == want]
    if not candidates:
        return None
    return min(candidates)[1]


def has_iologic(fse, ttyp, ab):
    """Whether the tile type carries the `IOLOGIC{ab}` this pin would use.

    Mirrors `chipdb.fse_iologic`: `shortval` 21 is the `A` half and 22 the `B`
    half, and the four corner tiles never get one whatever their tables say.
    """
    if ttyp in _NO_IOLOGIC_TTYPS:
        return False
    shortval = fse[ttyp].get("shortval", {})
    return (21 if ab == "A" else 22) in shortval


def derive():
    """Build the whole table from the shipped device files."""
    dat_parser, fse_parser, pindef = _apycula()
    from pathlib import Path

    gowinhome = os.environ["GOWINHOME"]
    share = f"{gowinhome}/IDE/share/device/{DEVICE}/{DEVICE}"
    dat = dat_parser.Datfile(Path(f"{share}.dat"))
    with open(f"{share}.fse", "rb") as handle:
        fse = fse_parser.read_fse(handle, DEVICE)

    grid = fse["header"]["grid"][61]
    rows, cols = len(grid), len(grid[0])

    # `pindef` indexes its files by (device, package) only after all_packages
    # has populated the index, so ask for the packages first.
    packages = pindef.all_packages(DEVICE)
    if PARTNUMBER not in packages:
        raise DerivationError(
            f"{PARTNUMBER} is not a {DEVICE} partnumber of this install; "
            f"known: {sorted(packages)}")
    package_pins = pindef.get_package(DEVICE, PACKAGE, pindef.VeryTrue)

    bank_table = dat.compat_dict["Bank"]
    pins = []
    for pin in sorted(package_pins, key=lambda p: str(p["NAME"])):
        site = str(pin["NAME"])
        side, ab, (row, col) = site_cell(site, rows, cols)
        dat_bank = bank_table[side + ab][int(_SITE_RE.match(site).group(2))]
        json_bank = int(pin["BANK"])
        if dat_bank != json_bank:
            raise DerivationError(
                f"{site} ({pin['INDEX']}): .dat Bank says {dat_bank}, "
                f"{PACKAGE}.json says {json_bank}")
        block = nearest_block_on_side(side, (row, col))
        pins.append({
            "ball": str(pin["INDEX"]),
            "site": site,
            "side": side,
            "half": ab,
            "bank": json_bank,
            "row": row,
            "col": col,
            "iologic": has_iologic(fse, grid[row][col], ab),
            "hclk_block": block,
            "hclk_lanes": list(LANES_PER_BLOCK) if block is not None else [],
            "cfg": str(pin.get("CFG", "")),
            "diff": str(pin.get("DIFF", "")),
            "true_lvds": bool(pin.get("TRUELVDS", False)),
            "dqs": str(pin.get("DQS", "")),
            "ddr_bank": json_bank in DDR_BANKS,
            "derived": {
                "bank": "DAT-DERIVED",
                "cell": "DAT-DERIVED",
                "iologic": "FSE-DERIVED",
                "hclk_block": "ASSUMED",
                "hclk_lanes": "ASSUMED",
            },
        })

    clock_candidates = [p["site"] for p in pins
                        if re.search(r"\b(S|M)?GCLK", p["cfg"] or "")]
    return {
        "device": DEVICE,
        "package": PACKAGE,
        "partnumber": PARTNUMBER,
        "grid": {"rows": rows, "cols": cols},
        "generated_by": "tools/derive_pin_hclk_138c.py",
        "sources": {
            "bank": f"IDE/share/device/{DEVICE}/{DEVICE}.dat compat_dict['Bank']",
            "bank_crosscheck": f"IDE/data/device/{DEVICE}/{PACKAGE}.json PIN_DATA[*].BANK",
            "cell": f"IDE/data/device/{DEVICE}/{PACKAGE}.json PIN_DATA[*].NAME + grid dims",
            "iologic": f"IDE/share/device/{DEVICE}/{DEVICE}.fse shortval 21/22",
            "hclk_blocks": "evidence/hclk/topology-138c.md (P1.T04, MEASURED)",
            "hclk_block_of_pin": f"{BLOCK_RULE} (ASSUMED, to be settled by P3.T07)",
        },
        "block_rule": BLOCK_RULE,
        "hclk_blocks": [{"hclk_idx": i, "row": r, "col": c, "side": s}
                        for i, r, c, s in HCLK_BLOCKS],
        "ddr_banks": list(DDR_BANKS),
        # Shaped like the values of `chipdb._gw5_pin_to_hclk`. Empty on
        # purpose: an entry needs a measured fabric wire and `hclknames` index
        # (see the module doc), and P3.T07 is the task that measures them.
        "pin_to_hclk_entries": [],
        "clock_pin_candidates": clock_candidates,
        "corroboration": corroboration(pins),
        "pins": pins,
    }


def corroboration(pins):
    """Two independent checks on `BLOCK_RULE`, computed and recorded.

    Neither makes the block assignment MEASURED -- only a vendor run does that
    (`P3.T07`) -- but both would have failed loudly on a wrong rule, and a
    reader of the JSON alone should see them:

    1. **bank -> block is a function.** If the rule split a bank across two
       blocks, a bank's pins could not share one `BANK_VCCIO`-scoped clock
       plan; the vendor lays banks out along an edge, so a correct rule keeps
       each bank whole.
    2. **the dedicated clock balls bracket their block's cell.** The `SGCLK`/
       `MGCLK` config roles in the pinout are the balls the silicon routes
       straight at a clock resource, and they are placed by the die layout,
       not by this rule -- so the distance from each of them to the block the
       rule assigns is an outside opinion on the rule.
    """
    blocks = {i: (r, c) for i, r, c, _ in HCLK_BLOCKS}
    bank_to_block = {}
    split_banks = []
    for pin in pins:
        seen = bank_to_block.setdefault(pin["bank"], pin["hclk_block"])
        if seen != pin["hclk_block"] and pin["bank"] not in split_banks:
            split_banks.append(pin["bank"])
    distances = []
    for pin in pins:
        if not re.search(r"\b(S|M)?GCLK", pin["cfg"] or ""):
            continue
        row, col = blocks[pin["hclk_block"]]
        axis = abs(pin["col"] - col) if pin["side"] == "B" else abs(pin["row"] - row)
        distances.append(axis)
    return {
        "bank_to_block": {str(bank): block for bank, block in sorted(bank_to_block.items())},
        "banks_split_across_blocks": split_banks,
        "clock_ball_max_cells_from_its_block": max(distances) if distances else None,
        "clock_ball_count": len(distances),
    }


def render(table):
    return json.dumps(table, indent=1, sort_keys=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed artefact is not what this "
                             "run derives")
    parser.add_argument("--out", default=_OUT, help="artefact path")
    args = parser.parse_args(argv)

    text = render(derive())
    if args.check:
        if not os.path.isfile(args.out):
            print(f"FAIL {args.out} does not exist", file=sys.stderr)
            return 1
        with open(args.out) as handle:
            if handle.read() != text:
                print(f"FAIL {args.out} is stale", file=sys.stderr)
                return 1
        print(f"ok {args.out} is current")
        return 0
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as handle:
        handle.write(text)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
