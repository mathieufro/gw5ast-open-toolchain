#!/usr/bin/env python3
"""Derive the `AE350_SOC` fabric wire map of the GW5AST-138C.

The map says, for every one of the block's 911 port bits, which fabric wire
`(row, col, wire)` the hard block reaches it on, or that this device data binds
no wire to it. It is derived from three inputs and nothing else:

* the vendor `.dat`'s `Ae350SocIns` and `Ae350SocOuts` tables, decoded by
  `apycula.dat_parser` (the input table is *located* from the block's geometry,
  not addressed at a fixed base) and named by `apycula.wirenames`;
* `evidence/ae350/port-inventory.json` -- the 149 ports in `primitive.xml`
  declaration order with their widths and directions, which fixes bit order;
* `evidence/ae350/wire-map-pipdiff-138c.json` -- the taps the vendor bitstream
  of run `p2t26-tilewires` was seen to use, which is what makes a bit MEASURED
  rather than DAT-DERIVED.

The direction rule is the load-bearing part, and it is not the table names.
Die row 0 is a row of routing tiles with no bels, so a tap's direction is the
wire's role in the routing graph: `F`, `Q` and `OF` end no pip, so only the
block can drive them and they are its outputs; `A`-`D`, `CE`, `CLK` and `LSR`
are pip destinations and dead ends unless the block reads them, so they are its
inputs. `Ae350SocOuts` therefore holds the whole input map in one run, with the
head and tail of the output map either side of it, and `Ae350SocIns` holds the
output map's middle run.

This is deliberately a second implementation of that rule: `apycula.chipdb`
builds the same map for the router, and
`tools/tests/test_ae350_chipdb_reconciliation.py` holds the two against each
other bit for bit. Importing the chipdb builder here would make that test say
nothing, so this module imports only the `.dat` decoder and the wire names.

Usage::

    python3 tools/derive_ae350_wire_map.py            # rewrite the artefact
    python3 tools/derive_ae350_wire_map.py --check    # fail if it is stale
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

#: The only device that carries the block.
DEVICE = "GW5AST-138C"
PRIMITIVE = "AE350_SOC"

#: Die columns of the block's footprint, from the presence diff of the two
#: banked runs named in `RUNS`.
FOOTPRINT_COLS = (145, 181)

#: The vendor runs the measured half of the map rests on.
RUNS = ("p2t26-tilewires", "p2t26-baseline")

#: Wire classes only the block drives: a bit whose record names one of these is
#: an output of the block.
BLOCK_DRIVEN_WIRE = re.compile(r"(?:Q|F|OF)\d+")

#: The six clock inputs. `TEST_CLK` is not among them: the block ties it
#: internally, so it never reaches the clock network.
CLOCK_PORTS = frozenset(
    {"CORE_CLK", "DDR_CLK", "AHB_CLK", "APB_CLK", "RTC_CLK", "DBG_TCK"})

#: The two asynchronous reset inputs -- the only ports that can sit on a tile's
#: `LSR` line, which is what fixes them within the head of the input map.
RESET_PORTS = frozenset({"POR_N", "HW_RSTN"})

#: An absent field of a `gw5aStuff` record: these tables are unsigned, so the
#: `-1` of the legacy triples reads back as `0xffff`.
DAT_ABSENT = 0xFFFF

_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = _ROOT / "evidence" / "ae350"
PORT_INVENTORY = EVIDENCE / "port-inventory.json"
PIPDIFF = EVIDENCE / "wire-map-pipdiff-138c.json"
WIRE_MAP = EVIDENCE / "wire-map-138c.json"


def dat_path() -> Path:
    """The shipped `.dat` of the device, under the installed IDE."""
    home = os.environ.get("GOWINHOME")
    if not home:
        raise SystemExit("GOWINHOME is not set")
    return Path(home) / "IDE" / "share" / "device" / DEVICE / f"{DEVICE}.dat"


def port_bits(ports):
    """Yield `(port, index)` per bit of `ports`, in declaration order.

    A single-bit port keeps its name and has no index; a bus of width *w*
    becomes `NAME0` .. `NAME{w-1}`, LSB first.
    """
    for name, width in ports:
        if width == 1:
            yield name, None
        else:
            for index in range(width):
                yield f"{name}{index}", index


def read_ports(inventory=PORT_INVENTORY):
    """`(inputs, outputs)` as `(name, width)` tuples in declaration order."""
    ports = json.loads(Path(inventory).read_text())["ports"]
    def of(direction):
        return [(p["name"], p["width"]) for p in ports
                if p["direction"] == direction]
    return of("input"), of("output")


def read_tables(path=None):
    """`(ins_table, outs_table, ide_version, grid)` from the vendor `.dat`."""
    from apycula import dat_parser
    from apycula import wirenames as wnames

    wnames.select_wires(DEVICE)
    dat = dat_parser.Datfile(Path(path) if path else dat_path())
    stuff = getattr(dat, "gw5aStuff", None) or {}
    grid = (dat.grid.num_rows, dat.grid.num_cols)
    return (stuff.get("Ae350SocIns") or [], stuff.get("Ae350SocOuts") or [],
            dat.ide_version, grid)


def wire_name(index):
    """The name of a wire index, or `None` when this device has no such wire."""
    from apycula import wirenames as wnames
    return wnames.wirenames.get(index)


def tap(record, grid):
    """`((row, col, wire_name, wire_index), None)`, else `(None, reason)`.

    A record binds a bit when it is present, lands on a cell of the die grid,
    and names a wire this device's wire table knows. Every other outcome is a
    bit the device data does not map, and the reason is kept so that the gap is
    auditable rather than silent.
    """
    if record is None or len(record) < 3:
        return None, "no-record"
    row, col, wire = record[0], record[1], record[2]
    if DAT_ABSENT in (row, col, wire) or -1 in (row, col, wire):
        return None, "unbound"
    if not (0 <= row - 1 < grid[0] and 0 <= col - 1 < grid[1]):
        return None, "off-grid"
    name = wire_name(wire)
    if name is None:
        return None, "unknown-wire-index"
    return (row - 1, col - 1, name, wire), None


def drives_the_block(record, grid):
    """True when a usable record names a wire the *fabric* drives.

    Those are the block's inputs; `F`/`Q`/`OF` are the wires only the block
    drives, and so are its outputs.
    """
    placed, _reason = tap(record, grid)
    return placed is not None and not BLOCK_DRIVEN_WIRE.fullmatch(placed[2])


def wire_class(record):
    """The letter class of a record's wire -- `A`, `CE`, `CLK`, `LSR`, ..."""
    return re.match(r"[A-Z]+", wire_name(record[2])).group()


def input_records(outs_table, in_ports, grid):
    """One record per input bit, in bit order.

    Every fabric-driven record of `Ae350SocOuts` is an input tap, and there are
    exactly as many of them as the block has input bits. Within the two classes
    that name a dedicated tile line the slot order and the port order disagree,
    so the class decides: an `LSR` tap can only be a reset input and a `CLK` tap
    only a clock input.
    """
    picked = [(slot, rec) for slot, rec in enumerate(outs_table)
              if drives_the_block(rec, grid)]
    ports = [name for name, _index in port_bits(in_ports)]
    if len(picked) != len(ports):
        raise SystemExit(
            f"{len(picked)} fabric-driven records for {len(ports)} input bits")
    dedicated = [i for i, port in enumerate(ports)
                 if port in CLOCK_PORTS or port in RESET_PORTS]
    pool = {"LSR": [], "CLK": []}
    for i in dedicated:
        pool.setdefault(wire_class(picked[i][1]), []).append(picked[i])
    if len(pool["LSR"]) != len(RESET_PORTS) or len(pool["CLK"]) != len(CLOCK_PORTS):
        raise SystemExit("the head of the input map is not resolvable by class")
    for i in dedicated:
        want = "LSR" if ports[i] in RESET_PORTS else "CLK"
        picked[i] = pool[want].pop(0)
    return picked


def output_records(ins_table, outs_table, first_in, last_in, bits):
    """One record per output bit, in bit order.

    The output map is stored in two runs either side of the input map: bits
    below the first input slot and above the last one come from `Ae350SocOuts`
    at their own index, the run between them from `Ae350SocIns` at its start.
    `Ae350SocIns` is shorter than that gap, so the bits past its end are the
    ones this device data does not map.
    """
    out = []
    for bit in range(bits):
        if bit >= len(outs_table):
            out.append((None, None, None))
        elif bit < first_in:
            out.append(("Ae350SocOuts", bit, outs_table[bit]))
        elif bit - first_in < len(ins_table):
            out.append(("Ae350SocIns", bit - first_in, ins_table[bit - first_in]))
        elif bit <= last_in:
            out.append((None, None, None))
        else:
            out.append(("Ae350SocOuts", bit, outs_table[bit]))
    return out


def read_pipdiff(path=PIPDIFF):
    """The `(row, col, wire)` taps the vendor bitstream was seen to use."""
    doc = json.loads(Path(path).read_text())
    return {tuple(t) for t in doc["taps"]}, doc


def _entry(bit, port, index, table, slot, record, grid, measured):
    placed, reason = tap(record, grid)
    if placed is None:
        return {"bit": bit, "col": None, "index": index, "port": port,
                "provenance": "UNBOUND", "row": None, "slot": slot,
                "table": table, "unmapped_reason": reason, "wire": None,
                "wire_idx": None}
    row, col, name, wire_idx = placed
    return {"bit": bit, "col": col, "index": index, "port": port,
            "provenance": "MEASURED" if (row, col, name) in measured
                          else "DAT-DERIVED",
            "row": row, "slot": slot, "table": table, "unmapped_reason": None,
            "wire": name, "wire_idx": wire_idx}


def _summary(entries, table_facts):
    low, high = FOOTPRINT_COLS
    bound = [e for e in entries if e["provenance"] != "UNBOUND"]
    inside = [e for e in bound if low <= e["col"] <= high]
    summary = {
        "bits": len(entries),
        "bound": len(bound),
        "unbound": len(entries) - len(bound),
        "measured": sum(1 for e in bound if e["provenance"] == "MEASURED"),
        "dat_derived": sum(1 for e in bound if e["provenance"] == "DAT-DERIVED"),
        "in_footprint": len(inside),
        "out_of_footprint": len(bound) - len(inside),
        "cols": dict(sorted(Counter(str(e["col"]) for e in bound).items(),
                            key=lambda kv: int(kv[0]))),
        "wire_classes": dict(sorted(Counter(
            re.match(r"[A-Z]+", e["wire"]).group() for e in bound).items())),
        "tables": dict(sorted(Counter(
            e["table"] for e in bound).items())),
        "unmapped_reasons": dict(sorted(Counter(
            e["unmapped_reason"] for e in entries
            if e["provenance"] == "UNBOUND").items())),
        "out_of_footprint_taps": [
            {"bit": e["bit"], "col": e["col"], "port": e["port"],
             "row": e["row"], "wire": e["wire"]}
            for e in bound if not low <= e["col"] <= high],
    }
    summary.update(table_facts)
    return summary


def derive(dat=None, inventory=PORT_INVENTORY, pipdiff=PIPDIFF):
    """The whole artefact, as the dict that is written to the JSON file."""
    ins_table, outs_table, ide_version, grid = read_tables(dat)
    in_ports, out_ports = read_ports(inventory)
    measured, pipdoc = read_pipdiff(pipdiff)

    in_bits = list(port_bits(in_ports))
    out_bits = list(port_bits(out_ports))

    picked = input_records(outs_table, in_ports, grid)
    inputs = [_entry(bit, port, index, "Ae350SocOuts", slot, record, grid,
                     measured)
              for bit, ((port, index), (slot, record))
              in enumerate(zip(in_bits, picked))]

    driven = [slot for slot, rec in enumerate(outs_table)
              if drives_the_block(rec, grid)]
    first_in, last_in = (driven[0], driven[-1]) if driven else (0, -1)
    outputs = [_entry(bit, port, index, table, slot, record, grid, measured)
               for bit, ((port, index), (table, slot, record))
               in enumerate(zip(out_bits, output_records(
                   ins_table, outs_table, first_in, last_in, len(out_bits))))]

    def live(table):
        return sum(1 for rec in table if tap(rec, grid)[0] is not None)

    bits = {"inputs": inputs, "outputs": outputs}
    return {
        "bits": bits,
        "device": DEVICE,
        "direction_rule": (
            "die row 0 holds routing tiles with no bels, so a tap's direction "
            "is the wire's: F/Q/OF end no pip and only the block drives them, "
            "so they are its outputs; A-D, CE, CLK and LSR are pip "
            "destinations and dead ends unless the block reads them, so they "
            "are its inputs -- neither table is one direction"),
        "footprint_cols": list(FOOTPRINT_COLS),
        "ide": f"Gowin IDE Standard {ide_version}",
        "input_run": {"first_slot": first_in, "last_slot": last_in},
        "mapping_rule": (
            "bit i of a direction is the i'th record of that direction's map, "
            "counting ports in primitive.xml declaration order and each bus "
            "LSB first; the input map is the fabric-driven run of "
            "Ae350SocOuts, the output map is Ae350SocOuts outside that run "
            "with Ae350SocIns filling it; a 0xffff/0xffff/0xffff record and a "
            "bit past the end of Ae350SocIns inside the run are unbound"),
        "measured_by": pipdoc["source"],
        "primitive": PRIMITIVE,
        "record": ("(row, col, wire) with row and col 0-based die coordinates "
                   "and wire a name from wirenames_5a25a"),
        "runs": list(RUNS),
        "source": ("dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts'], decoded by "
                   "apycula dat_parser.read_packed_grid16; the input table is "
                   "located by dat_parser.read_ae350_soc_ins, not addressed at "
                   "a fixed base"),
        "summary": {
            "bound": sum(1 for e in inputs + outputs
                         if e["provenance"] != "UNBOUND"),
            "bits": len(inputs) + len(outputs),
            "inputs": _summary(inputs, {
                "slots": len(outs_table), "live_slots": live(outs_table),
                "table": "Ae350SocOuts"}),
            "outputs": _summary(outputs, {
                "slots": {"Ae350SocIns": len(ins_table),
                          "Ae350SocOuts": len(outs_table)},
                "live_slots": {"Ae350SocIns": live(ins_table),
                               "Ae350SocOuts": live(outs_table)},
                "table": "Ae350SocOuts head and tail, Ae350SocIns between"}),
        },
    }


def render(doc):
    """The artefact's exact on-disk text: sorted keys, one trailing newline."""
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dat", help="the device .dat; default under GOWINHOME")
    parser.add_argument("--out", default=str(WIRE_MAP),
                        help="artefact to write; default the committed one")
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit 1 if the artefact is stale")
    args = parser.parse_args(argv)

    text = render(derive(args.dat))
    out = Path(args.out)
    if args.check:
        if not out.is_file() or out.read_text() != text:
            print(f"{out} does not match the .dat tables", file=sys.stderr)
            return 1
        return 0
    out.write_text(text)
    doc = json.loads(text)["summary"]
    print(f"{out}: {doc['bound']} of {doc['bits']} bits bound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
