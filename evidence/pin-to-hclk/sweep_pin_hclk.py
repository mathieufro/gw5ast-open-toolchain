"""P3.T07/P3.T08 -- sweep board pins for HCLK reachability, and close the row.

What this measures, and with which instrument
---------------------------------------------
A package pin "reaches FCLK" on this die if its clock can enter the HCLK
network and an IOLOGIC can take its fast clock from there.  The instrument is
`fuzz.gw5ast138c.shapes.io_basic`'s **HCLK probe** (`hclk_probe=True`): one
`DHCE` per candidate ball, each feeding an unpinned `CLKDIV`, with an `IDES4`
whose `FCLK` is clock 0's HCLK.  `io_basic`'s own docstring records the three
vendor runs that show why every weaker design measures nothing.

The read-out is the decoded vendor bitstream, never the report:

* an `HCLK` bel decodes with flags spelled `HCLK_MUX_BETA<block><lane>=<src>`
  (`P1.T26`/`P1.T27`), so the block, the lane **and the wire the clock entered
  on** all come out of the decode;
* a `CLKDIV_` bel decodes with `DIV_MODE="<n>"`, and the probe gives each
  clock a distinct `DIV_MODE`, so a design carrying several clocks still says
  which **pin** landed on which block and lane;
* an `IOLOGIC` bel decodes with `MODE=IDES4` and its `FCLK` port bound to the
  tile's own `FCLK` wire.

Usage (from the apicula worktree, `PYTHONPATH=.`)::

    python $OTC/evidence/pin-to-hclk/sweep_pin_hclk.py \
        --batch-id p3-pin-to-hclk --design-root $DATASTORE/p3t07 --run all

`--run decode-only` re-derives every row from the vendor bitstreams already on
disk and spends no oracle run.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

#: `HCLK_MUX_BETA<block><lane>` -- the lane entry multiplexer, whose selected
#: source is the wire the clock entered the HCLK network on (`P1.T27`).
BETA_RE = re.compile(r"^HCLK_MUX_BETA(\d)(\d)=(?:\"?)([A-Za-z0-9_]+)")
DIV_MODE_RE = re.compile(r'^DIV_MODE="([^"]+)"$')

#: The runs this task spends, in order.  Three sweep runs carry the twelve
#: `io_basic.CLOCK_CANDIDATES` balls four at a time; each run mixes banks, so
#: a ball's landing is never read off a run in which its bank was the only
#: one present.
#:
#: The last two runs are the controls the sweep alone cannot supply.  The
#: sweep answers "which block did the vendor pick for this ball"; it does not
#: answer "could it have picked another", and without that the table would
#: record a placer preference as if it were a property of the ball.  So each
#: control takes a ball the sweep landed on one edge and **pins** its divider
#: to a block on a different edge (`INS_LOC`, the `{...}SIDE[n]` spelling of
#: SUG1018-1.7E 2.9): a bottom-edge ball onto a right-edge block and a
#: right-edge ball onto a bottom-edge block.  Two routes that succeed refute
#: pin-determination in both directions; a refusal would establish it.
PLAN = (
    {"id": "sweep-a", "balls": ("V19", "F20", "Y17", "G15"), "ins_loc": {}},
    {"id": "sweep-b", "balls": ("W20", "D21", "W14", "N15"), "ins_loc": {}},
    {"id": "sweep-c", "balls": ("P20", "F21", "AA9", "V22"), "ins_loc": {}},
    {"id": "ctl-v22-rightside", "balls": ("V22",),
     "ins_loc": {"div0": "RIGHTSIDE[4]"}},
    {"id": "ctl-f20-bottomside", "balls": ("F20",),
     "ins_loc": {"div0": "BOTTOMSIDE[4]"}},
)


def _candidate_tables():
    from fuzz.gw5ast138c.shapes import io_basic
    banks = {ball: bank for ball, bank, _role in io_basic.CLOCK_CANDIDATES}
    roles = {ball: role for ball, _bank, role in io_basic.CLOCK_CANDIDATES}
    return banks, roles


def decode_hclk(netlist, div_modes):
    """`{clock index: {...}}` for one decoded vendor bitstream.

    `div_modes` is the probe's `DIV_MODE` per clock index, which is what ties
    a decoded `CLKDIV_` back to the ball that clocked it.
    """
    by_mode = {mode: index for index, mode in enumerate(div_modes)}
    dividers = {}
    hclks = {}
    iologic = []
    for cell, flags in netlist.cells.items():
        if cell.type == "CLKDIV_":
            for flag in flags:
                match = DIV_MODE_RE.match(flag)
                if match and match.group(1) in by_mode:
                    dividers[by_mode[match.group(1)]] = {
                        "block_tile": [cell.x, cell.y],
                        "lane": cell.z,
                        "div_mode": match.group(1),
                    }
        elif cell.type == "HCLK":
            for flag in sorted(flags):
                match = BETA_RE.match(flag)
                if match:
                    block, lane, source = match.groups()
                    hclks[(cell.x, cell.y, int(block), int(lane))] = source
        elif cell.type == "IOLOGIC":
            mode = next((f.split("=", 1)[1] for f in flags
                         if f.startswith("MODE=")), None)
            iologic.append({"tile": [cell.x, cell.y], "z": cell.z,
                            "mode": mode,
                            "fclk": (netlist.conns.get(cell) or {}).get("FCLK")})
    out = {}
    for index, divider in sorted(dividers.items()):
        entry = dict(divider)
        entry["hclk_block"] = None
        entry["hclk_entry_wire"] = None
        for (x, y, block, lane), source in hclks.items():
            if [x, y] == divider["block_tile"] and lane == divider["lane"]:
                entry["hclk_block"] = block
                entry["hclk_entry_wire"] = source
        out[index] = entry
    return {"clocks": out, "iologic": iologic,
            "hclk_bels": {"%d,%d,%d,%d" % k: v for k, v in sorted(hclks.items())}}


def build_spec(balls, ins_loc):
    from fuzz.gw5ast138c.shapes import io_basic
    return io_basic.IoBasicShape(hclk_probe=True, clk_balls=balls,
                                 ins_loc=ins_loc).spec()


def run_one(step, design_root, batch_id, do_oracle=True):
    """Generate, optionally run the vendor, then decode.  Returns the rows."""
    from fuzz.gw5ast138c.harness import equiv, gen, oracle
    from fuzz.gw5ast138c.shapes import io_basic

    design_dir = os.path.join(design_root, step["id"])
    spec = build_spec(step["balls"], step["ins_loc"])
    gen.run(spec, design_dir, "iddr-default")

    started = time.time()
    if do_oracle:
        result = oracle.run_oracle(design_dir, top_module="top")
        ok = result["preflight"].ok
        reason = result["preflight"].reason
        fs_paths = result["artefacts"]["fs"]
        log_path = result["log_path"]
    else:
        fs_paths = [os.path.join(design_dir, "run/impl/pnr/run.fs")]
        ok = os.path.isfile(fs_paths[0])
        reason = "decode-only" if ok else "no vendor .fs on disk"
        log_path = os.path.join(design_dir, "gw_sh.log")

    base = {
        "device": "GW5AST-138C",
        "shape": "io_basic",
        "primitive": spec.primitive,
        "level": "E0",
        "oracle_log": log_path if os.path.isfile(log_path) else None,
        "wall_clock_s": {"oracle": round(time.time() - started, 3)},
    }
    if not ok:
        return [dict(base, run_id="%s-%s-%s" % (batch_id, step["id"], ball),
                     verdict="aborted",
                     sweep={"clk_ball": ball, "step": step["id"],
                            "reaches_fclk": False},
                     notes="vendor run did not produce a bitstream: %s" % reason)
                for ball in step["balls"]]

    BANK_OF_BALL, ROLE_OF_BALL = _candidate_tables()
    decoded = decode_hclk(equiv.unpack_netlist(fs_paths[0]),
                          io_basic.PROBE_DIV_MODES[:len(step["balls"])])
    iologic = decoded["iologic"]
    rows = []
    for index, ball in enumerate(step["balls"]):
        clock = decoded["clocks"].get(index)
        reaches = bool(clock and clock["hclk_block"] is not None)
        sweep = {
            "clk_ball": ball,
            "step": step["id"],
            "bank": BANK_OF_BALL[ball],
            "clock_role": ROLE_OF_BALL[ball],
            "reaches_fclk": reaches,
            "hclk_block": clock["hclk_block"] if clock else None,
            "hclk_lane": clock["lane"] if clock else None,
            "hclk_block_tile": clock["block_tile"] if clock else None,
            "hclk_entry_wire": clock["hclk_entry_wire"] if clock else None,
            "ins_loc": step["ins_loc"] or None,
            # Only clock 0 drives the IDES4's FCLK, so only clock 0's row can
            # carry the IOLOGIC evidence; the others measure the HCLK entry.
            "iologic": iologic if index == 0 else None,
        }
        rows.append(dict(base,
                         run_id="%s-%s-%s" % (batch_id, step["id"], ball),
                         timestamp=datetime.now(timezone.utc).isoformat(),
                         verdict="ok" if reaches else "diff",
                         sweep=sweep,
                         artefacts={"vendor_fs": fs_paths[0]},
                         notes=""))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sweep_pin_hclk")
    parser.add_argument("--batch-id", default="p3-pin-to-hclk")
    parser.add_argument("--design-root", required=True)
    parser.add_argument("--run", choices=("all", "decode-only"), default="all")
    parser.add_argument("--out", default=None,
                        help="JSON Lines file the rows are written to.")
    parser.add_argument("--only", default=None,
                        help="Comma-separated PLAN ids to run.")
    args = parser.parse_args(argv)

    only = set(args.only.split(",")) if args.only else None
    rows = []
    for step in PLAN:
        if only and step["id"] not in only:
            continue
        rows.extend(run_one(step, args.design_root, args.batch_id,
                            do_oracle=args.run == "all"))
        print("STEP %s done (%d rows)" % (step["id"], len(rows)), flush=True)
    if args.out:
        with open(args.out, "w") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    for row in rows:
        sweep = row["sweep"]
        print("%-6s bank %-2s -> block %-4s lane %-4s entry %-12s %s"
              % (sweep["clk_ball"], sweep.get("bank"), sweep.get("hclk_block"),
                 sweep.get("hclk_lane"), sweep.get("hclk_entry_wire"),
                 row["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
