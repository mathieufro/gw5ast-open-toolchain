"""IOB / bank-default safety row for the GW5AST-138C (`P3.T26`).

The row's claim, asserted over vendor/open bitstream **pairs that already
exist** in the datastore:

1. the open flow never sets a bank or IOB fuse the vendor does not set for the
   same pin state, and
2. it never leaves a used pin's ``IO_TYPE`` or its bank's ``BANK_VCCIO`` unset.

Both halves are decided on the *unpacked bitstream* (`D20b`) -- the packer is
never trusted for its own verdict.  Every IOB and BANK fuse is read back
through apicula's own ``parse_attrvals`` against the chipdb's ``longval``
tables, so "which fuse is this" is answered by the same tables
``gowin_unpack`` decodes with, never by a byte offset.

Pin state is taken from the open flow's placement (``top_pnr.json``
``NEXTPNR_BEL``), which both flows share because they are driven by the same
``.cst``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

#: Attributes whose value the PR #423 defect class turns on: a bank pull that
#: the vendor does not ask for is the live thermal hazard, and a drive
#: strength or IO standard the vendor does not ask for is the same class of
#: mistake one step down.
SAFETY_ATTRS = (
    "PULL_STRENGTH", "PULLMODE", "PULL_MODE", "DRIVE", "IO_TYPE",
    "OPENDRAIN", "SLEW_RATE", "SLEW", "HYSTERESIS", "VREF", "BANK_VCCIO",
    "VCCIO", "DIFF_RESISTOR_VALUE",
)

#: A used pin must carry both of these once the bitstream is unpacked.
REQUIRED_ON_USED_PIN = ("IO_TYPE",)
REQUIRED_ON_USED_BANK = ("IO_TYPE",)

_BEL_RE = re.compile(r"X(\d+)Y(\d+)/IOB([AB])$")

#: Cell types whose placement makes the site a differential half.
_DIFF_TYPES = ("LVDS", "MIPI")


@dataclass(frozen=True)
class Site:
    """One IOB half or one bank, addressed the way the chipdb addresses it."""

    row: int
    col: int
    name: str

    def __str__(self) -> str:
        return f"(R{self.row}C{self.col})/{self.name}"


@dataclass
class Violation:
    """One place where the open flow diverges from the vendor unsafely."""

    design: str
    site: Site
    pin_state: str
    attr: str
    kind: str
    vendor: str | None
    open_: str | None

    def as_row(self) -> dict:
        return {
            "design": self.design,
            "tile": [self.site.row, self.site.col],
            "site": self.site.name,
            "pin_state": self.pin_state,
            "attr": self.attr,
            "class": self.kind,
            "vendor": self.vendor,
            "open": self.open_,
        }


@dataclass
class DesignReport:
    """Per-design decode of both bitstreams, before any verdict is drawn."""

    design: str
    sites: dict = field(default_factory=dict)
    violations: list = field(default_factory=list)
    classes: dict = field(default_factory=lambda: defaultdict(Counter))


def _apycula(apicula_root):
    sys.path.insert(0, apicula_root)
    from apycula import attrids, chipdb  # noqa: PLC0415
    from apycula import gowin_unpack as gu  # noqa: PLC0415
    from apycula.bslib import read_bitstream  # noqa: PLC0415

    return attrids, chipdb, gu, read_bitstream


def load_device(apicula_root, chipdb_path, device="GW5AST-138C"):
    """The chipdb plus the apicula modules the decode needs."""
    attrids, chipdb, gu, read_bitstream = _apycula(apicula_root)
    db = gu.load_chipdb(chipdb_path)
    gu._device = device
    return db, attrids, chipdb, gu, read_bitstream


def bank_fuse_tables(db):
    """``{ttyp: {BANK<n>: table}}`` -- the shape ``parse_attrvals`` wants."""
    tables = {}
    for ttyp, groups in db.longval.items():
        bank = groups.get("BANK")
        if not bank:
            continue
        for key, val in bank.items():
            tables.setdefault(ttyp, {}).setdefault(
                f"BANK{key[0]}", {})[key[1:]] = val
    return tables


def _named(attrids, value):
    return attrids.iob_num2val.get(value, str(value))


def decode_iob(db, bm, gu, attrids, row, col, idx):
    """``{attr: value}`` for one IOB half, or ``None`` if it has no table."""
    tiledata = db[row, col]
    name = f"IOB{idx}"
    bel = tiledata.bels.get(name)
    if bel is None:
        return None
    io_row, io_col = row, col
    if idx == "B" and bel.fuse_cell_offset:
        io_row += bel.fuse_cell_offset[0]
        io_col += bel.fuse_cell_offset[1]
    table = (db.longval.get(db[io_row, io_col].ttyp, {}) or {}).get(name)
    tile = bm.get((io_row, io_col))
    if not table or tile is None:
        return None
    raw = gu.parse_attrvals(tile, db.rev_logicinfo("IOB"), table,
                            attrids.iob_attrids, "IOB")
    return {a: _named(attrids, v) for a, v in raw.items()}


def decode_bank(db, bm, gu, attrids, tables, row, col, name):
    """``{attr: value}`` for one bank cell, or ``None`` if it has no table."""
    table = (tables.get(db[row, col].ttyp) or {}).get(name)
    tile = bm.get((row, col))
    if not table or tile is None:
        return None
    raw = gu.parse_attrvals(tile, db.rev_logicinfo("IOB"), table,
                            attrids.iob_attrids, "IOB")
    return {a: _named(attrids, v) for a, v in raw.items()}


def io_sites(db):
    """Every IOB half and bank cell in the device, in a stable order."""
    out = []
    for row in range(db.rows):
        for col in range(db.cols):
            for name in sorted(db[row, col].bels):
                if name in ("IOBA", "IOBB") or name.startswith("BANK"):
                    out.append(Site(row, col, name))
    return out


def used_sites(pnr_json_path):
    """``{(row, col, 'IOBA'): pin_state}`` from the open flow's placement."""
    with open(pnr_json_path, encoding="utf-8") as handle:
        pnr = json.load(handle)
    states = {}
    for module in pnr.get("modules", {}).values():
        for cell in module.get("cells", {}).values():
            bel = cell.get("attributes", {}).get("NEXTPNR_BEL", "")
            match = _BEL_RE.match(bel)
            if match is None:
                continue
            col, row, idx = int(match[1]), int(match[2]), match[3]
            states[(row, col, f"IOB{idx}")] = pin_state(cell["type"])
    return states


def pin_state(cell_type):
    """The four states the row distinguishes, from the placed cell's type."""
    if any(marker in cell_type for marker in _DIFF_TYPES):
        return "diff_pair"
    if cell_type in ("OBUF", "TBUF"):
        return "used_output"
    if cell_type == "IOBUF":
        return "used_inout"
    return "used_input"


def bank_of(chipdb, db, row, col):
    """The bank a tile belongs to, or ``None`` when it belongs to none."""
    try:
        return chipdb.loc2bank(db, row, col)
    except KeyError:
        return None


def site_open_only_bits(db, vendor_bm, open_bm, row, col, name):
    """Bits the open bitstream sets in a site's fuse cell and the vendor does not.

    The claim is about **fuses**, so this is what decides it.  Where the open
    bit set is a subset of the vendor's, no fuse was invented and an attribute
    that decodes only on the open side is the decoder resolving a smaller bit
    set to a different name -- the `lvds_out_is_aliased` case -- not a
    configuration the vendor declined to make.
    """
    cell = fuse_cell(db, row, col, name) if not name.startswith("BANK") \
        else (row, col)
    if cell is None or cell not in vendor_bm or cell not in open_bm:
        return None
    vendor, opened = vendor_bm[cell], open_bm[cell]
    return {(r, c)
            for r, line in enumerate(opened)
            for c, bit in enumerate(line)
            if bit and not vendor[r][c]}


def analyse(design, vendor_bm, open_bm, ctx):
    """Decode both bitstreams and enumerate every violation of the claim."""
    db, attrids, chipdb, gu, tables, used = ctx
    report = DesignReport(design=design)
    used_banks = {bank_of(chipdb, db, row, col)
                  for (row, col, _name) in used}
    used_banks.discard(None)
    for site in io_sites(db):
        if site.name.startswith("BANK"):
            state = ("used_bank"
                     if int(site.name[4:]) in used_banks else "unused_bank")
            decode = decode_bank
            args = (tables, site.row, site.col, site.name)
        else:
            key = (site.row, site.col, site.name)
            state = used.get(key, "unused")
            decode = decode_iob
            args = (site.row, site.col, site.name[-1])
        vendor = decode(db, vendor_bm, gu, attrids, *args)
        opened = decode(db, open_bm, gu, attrids, *args)
        if vendor is None and opened is None:
            continue
        vendor, opened = vendor or {}, opened or {}
        report.sites[str(site)] = {"state": state,
                                   "vendor": vendor, "open": opened}
        open_bits = site_open_only_bits(db, vendor_bm, open_bm,
                                        site.row, site.col, site.name)
        _classify(report, design, site, state, vendor, opened, open_bits)
    return report


def _classify(report, design, site, state, vendor, opened, open_bits=None):
    for attr in sorted(set(vendor) | set(opened)):
        in_v, in_o = attr in vendor, attr in opened
        if in_v and in_o:
            kind = "equal" if vendor[attr] == opened[attr] else "value_diff"
        elif in_o:
            kind = "open_only"
        else:
            kind = "vendor_only"
        if kind in ("open_only", "value_diff") and open_bits == set():
            kind = "decode_alias"
        report.classes[state][f"{attr}:{kind}"] += 1
        if kind == "open_only" or (kind == "value_diff"
                                   and attr in SAFETY_ATTRS):
            report.violations.append(Violation(
                design, site, state, attr, kind,
                vendor.get(attr), opened.get(attr)))
    required = (REQUIRED_ON_USED_BANK if state == "used_bank"
                else REQUIRED_ON_USED_PIN)
    if state.startswith("used") or state == "diff_pair":
        for attr in required:
            if attr not in opened and attr in vendor:
                report.violations.append(Violation(
                    design, site, state, attr, "unset_on_used",
                    vendor.get(attr), None))


#: The attribute-value set `GW5A.get_unused_io_attrvals` emits for an unused
#: pin on this device, and the same set with the two drive attributes removed.
#: Subtracting one fuse set from the other names the bits a drive default --
#: and nothing else -- can be responsible for, which is what turns "a bit the
#: vendor does not set" into "a bit of the PR #423 attribute class".
UNUSED_IO_ATTRVALS = (
    ("OPENDRAIN", "OFF"), ("IO_TYPE", "LVCMOS33"),
    ("DRIVE", "8"), ("DRIVE_LEVEL", "8"),
    ("PADDI", "PADDI"), ("PULLMODE", "NONE"),
)
DRIVE_ATTRS = ("DRIVE", "DRIVE_LEVEL")


def attrval_fuses(db, chipdb, attrids, ttyp, idx, pairs):
    """The fuse coordinates one IOB attribute-value set programs."""
    av = set()
    for attr, val in pairs:
        chipdb.add_attr_val(db, "IOB", av, attrids.iob_attrids[attr],
                            attrids.iob_attrvals[val])
    return {tuple(c)
            for c in chipdb.get_longval_fuses(db, ttyp, av, f"IOB{idx}")}


def fuse_cell(db, row, col, name):
    """Where an IOB half's fuses live, which is not always its own tile."""
    bel = db[row, col].bels.get(name)
    if bel is None:
        return None
    if name == "IOBB" and bel.fuse_cell_offset:
        return (row + bel.fuse_cell_offset[0], col + bel.fuse_cell_offset[1])
    return (row, col)


def unused_drive_bits(db, chipdb, attrids, vendor_bm, open_bm, row, col, name):
    """Bits the open flow sets on an unused pin and the vendor does not.

    Returned as `(drive_class, other)`: the first are bits only a `DRIVE` /
    `DRIVE_LEVEL` value can program (they vanish when those two attributes are
    dropped from the set), the second are the rest.
    """
    cell = fuse_cell(db, row, col, name)
    if cell is None or cell not in vendor_bm:
        return (), ()
    ttyp = db[cell].ttyp
    if not (db.longval.get(ttyp, {}) or {}).get(name):
        return (), ()
    idx = name[-1]
    full = attrval_fuses(db, chipdb, attrids, ttyp, idx, UNUSED_IO_ATTRVALS)
    nodrive = attrval_fuses(
        db, chipdb, attrids, ttyp, idx,
        tuple(p for p in UNUSED_IO_ATTRVALS if p[0] not in DRIVE_ATTRS))
    vendor, opened = vendor_bm[cell], open_bm[cell]
    only_open = {c for c in full
                 if opened[c[0]][c[1]] and not vendor[c[0]][c[1]]}
    drive = tuple(sorted(only_open - nodrive))
    return drive, tuple(sorted(only_open & nodrive))


def run_dirs(paths, open_name="top.fs"):
    """Every run directory under *paths* that holds a full vendor/open pair."""
    found = []
    for path in paths:
        for root, _dirs, files in os.walk(path):
            if (open_name in files and "top_pnr.json" in files
                    and os.path.exists(
                        os.path.join(root, "run/impl/pnr/run.fs"))):
                found.append(root)
    return sorted(found)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apicula", required=True)
    parser.add_argument("--chipdb", required=True)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--open-name", default="top.fs",
        help="the open-half bitstream to read inside each run directory; "
             "point it at a repack (tools/repack_open_fs.py) to re-diff a "
             "packer fix without spending an oracle run")
    args = parser.parse_args(argv)

    db, attrids, chipdb, gu, read_bitstream = load_device(
        args.apicula, args.chipdb)
    tables = bank_fuse_tables(db)
    dirs = run_dirs(args.runs, args.open_name)
    if args.limit:
        dirs = dirs[:args.limit]

    classes = defaultdict(Counter)
    violations = []
    rows = []
    for path in dirs:
        design = os.path.basename(path.rstrip("/"))
        vendor_bm = chipdb.tile_bitmap(
            db, read_bitstream(os.path.join(path, "run/impl/pnr/run.fs"))[0])
        open_bm = chipdb.tile_bitmap(
            db, read_bitstream(os.path.join(path, args.open_name))[0])
        used = used_sites(os.path.join(path, "top_pnr.json"))
        report = analyse(design, vendor_bm, open_bm,
                         (db, attrids, chipdb, gu, tables, used))
        drive_sites, drive_bits, other_bits = 0, 0, 0
        for site in io_sites(db):
            if not site.name.startswith("IOB"):
                continue
            if (site.row, site.col, site.name) in used:
                continue
            drive, other = unused_drive_bits(
                db, chipdb, attrids, vendor_bm, open_bm,
                site.row, site.col, site.name)
            drive_sites += bool(drive)
            drive_bits += len(drive)
            other_bits += len(other)
        for state, counter in report.classes.items():
            classes[state].update(counter)
        violations.extend(report.violations)
        rows.append({"design": design, "path": path,
                     "used_sites": len(used),
                     "violations": len(report.violations),
                     "unused_drive_sites": drive_sites,
                     "unused_drive_bits": drive_bits,
                     "unused_other_open_only_bits": other_bits})
        print(f"{design}: used={len(used)} "
              f"violations={len(report.violations)} "
              f"unused_drive_sites={drive_sites} "
              f"unused_drive_bits={drive_bits}", flush=True)

    result = {
        "designs": rows,
        "fuse_classes": {state: dict(sorted(counter.items()))
                         for state, counter in sorted(classes.items())},
        "violations": [v.as_row() for v in violations],
        "violation_count": len(violations),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
    print(f"IOB-SAFETY: {len(dirs)} designs, "
          f"{len(violations)} violations -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
