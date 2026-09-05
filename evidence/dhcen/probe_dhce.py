"""P1.T25 -- trace the DHCEN (GW5A spelling: `DHCE`) enable wires on GW5AST-138C.

Method (`apycula/chipdb.py` `_dhcen_ce` comment, the maintainer's own): build
vendor images with the maximum allowable number of DHCE instances whose enable
ports are driven from IO, then trace the route from the IO to the final wire --
that wire is the enable (`CE`) port of the DHCEN bel.

Every vendor compile is one oracle run against the D62 budget and is appended
to `$OTC/evidence/dhcen/oracle-runs.jsonl` and to
`$OTC/evidence/_budget/clocking-runs.tsv`.

Run from the apicula worktree that owns `clocking/dhcen-gw5a`:

    PYTHONPATH=$PWD python <this file> --out-root <scratch> --log <batch log> \
        --ledger <jsonl> --result <json>
"""
import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import oracle                       # noqa: E402
from fuzz.gw5ast138c.shapes import clocking_dhcen_trace as SHAPE  # noqa: E402

BATCH_ID = "p1-dhcen-trace"
DEVICE = "GW5AST-138C"

#: The six measured HCLK block cells (`P1.T04`), 0-based `(row, col)`.
HCLK_CELLS = SHAPE.HCLK_CELLS

CST = """IO_LOC  "clk" AA9;
IO_PORT "clk" IO_TYPE=LVCMOS33 PULL_MODE=NONE PULL_STRENGTH=MEDIUM BANK_VCCIO=3.3;
IO_LOC  "rst_n" AA10;
IO_PORT "rst_n" IO_TYPE=LVCMOS33 PULL_MODE=UP PULL_STRENGTH=MEDIUM BANK_VCCIO=3.3;
IO_LOC  "cen" AA11;
IO_PORT "cen" IO_TYPE=LVCMOS33 PULL_MODE=UP PULL_STRENGTH=MEDIUM BANK_VCCIO=3.3;
IO_LOC  "dout" P20;
IO_PORT "dout" IO_TYPE=LVCMOS33 PULL_MODE=NONE PULL_STRENGTH=MEDIUM BANK_VCCIO=3.3;
"""
SDC = "create_clock -name clk -period 20 -waveform {0 10} [get_ports {clk}]\n"


def write_design(d, n, tie_resetn=False, n_div=None):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "top.v"), "w").write(
        SHAPE.rtl(SHAPE.SPEC, n, tie_resetn=tie_resetn, n_div=n_div))
    open(os.path.join(d, "top.cst"), "w").write(CST)
    open(os.path.join(d, "top.sdc"), "w").write(SDC)


def log(fh, msg):
    fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    fh.flush()


def clock_resources(rpt_path):
    """The vendor's own `Clock Resource Usage Summary` as `{name: (used, cap)}`."""
    out = {}
    if not os.path.isfile(rpt_path):
        return out
    seen = False
    for line in open(rpt_path, errors="replace"):
        if "Clock Resource Usage Summary" in line:
            seen = True
            continue
        if seen:
            if line.strip().startswith("==="):
                break
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and "/" in parts[1]:
                used, _, cap = parts[1].partition("/")
                try:
                    out[parts[0]] = (int(used), int(cap.split()[0]))
                except ValueError:
                    pass
    return out


# --------------------------------------------------------------------------
# The trace itself
# --------------------------------------------------------------------------

def trace_enable_wires(fs_path, db):
    """Return the enable net's terminal wires inside the HCLK block cells.

    The enable of every DHCE instance is driven from **one** package pin, so
    the whole fan-out is a single connected component of the routing graph.
    The component is identified structurally -- it is the net that reaches an
    HCLK block cell from outside it -- and the wires reported are that net's
    wires that live in an HCLK block cell and drive nothing further, i.e. the
    ends of the route.  Those ends are the DHCEN enable ports.
    """
    from fuzz.gw5ast138c.harness.equiv import unpack_netlist
    nl = unpack_netlist(fs_path, db=db)

    net_wires = collections.defaultdict(set)
    for wire, net in nl.wire_net.items():
        net_wires[net].add(wire)

    wire_tiles = collections.defaultdict(set)
    srcs = set()
    for rc, pips in nl.raw_pips.items():
        for dest, src in pips.items():
            wire_tiles[dest].add(rc)
            wire_tiles[src].add(rc)
            srcs.add(src)

    hcells = set(HCLK_CELLS)
    found = []
    for net, wires in net_wires.items():
        tiles = set()
        for wire in wires:
            tiles |= wire_tiles.get(wire, set())
        hit = tiles & hcells
        if not hit or tiles <= hcells:
            continue                      # never leaves the block: not our net
        ends = []
        for wire in wires:
            wt = wire_tiles.get(wire, set()) & hcells
            if wt and wire not in srcs:
                for rc in sorted(wt):
                    ends.append((rc[0], rc[1], wire))
        if ends:
            found.append({"net": str(net), "n_wires": len(wires),
                          "hcells": sorted(hit), "ends": sorted(set(ends))})
    found.sort(key=lambda f: -len(f["ends"]))
    return {"pip_count": nl.pip_count, "nets": len(nl.nets), "candidates": found}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--budget", default=None)
    ap.add_argument("--pidfile", default=None)
    ap.add_argument("--tie-resetn", action="store_true",
                    help="tie CLKDIV.RESETN to a constant so the enable net is "
                         "the only IO-driven net reaching the HCLK blocks")
    ap.add_argument("--batch-id", default=BATCH_ID)
    ap.add_argument("--n-div", type=int, default=None,
                    help="override the CLKDIV count (control point: 0 DHCE, "
                         "24 CLKDIV)")
    ap.add_argument("--points", default="0,1,2,3,4,6,12,24,25")
    ap.add_argument("--trace-points", default="1,2,3,4,6,12,24")
    args = ap.parse_args()

    points = [int(p) for p in args.points.split(",") if p != ""]
    trace_points = {int(p) for p in args.trace_points.split(",") if p != ""}
    fsdir = os.path.join(args.out_root, "fs")
    os.makedirs(fsdir, exist_ok=True)
    rows, ok, aborted = [], 0, 0

    with open(args.log, "a") as fh:
        if args.pidfile:
            with open(args.pidfile, "w") as pf:
                pf.write(str(os.getpid()) + "\n")
        log(fh, f"BATCH_START {args.batch_id} runs={len(points)}")
        for n in points:
            name = (f"dhce{n:02d}" + ("_tr" if args.tie_resetn else "")
                    + (f"_div{args.n_div}" if args.n_div is not None else ""))
            d = os.path.join(args.out_root, name)
            shutil.rmtree(d, ignore_errors=True)
            write_design(d, n, tie_resetn=args.tie_resetn, n_div=args.n_div)
            t0 = time.time()
            verdict, detail = "ok", ""
            try:
                res = oracle.run_oracle(d, timeout=1800)
                if not res["preflight"].ok:
                    verdict, detail = "refused", res["preflight"].reason
            except Exception as exc:                 # a vendor refusal is a result
                verdict, detail = "refused", f"{type(exc).__name__}: {exc}"
            wall = round(time.time() - t0, 1)
            fs = os.path.join(d, "run", "impl", "pnr", "run.fs")
            kept = None
            if os.path.isfile(fs):
                kept = os.path.join(fsdir, f"{name}.fs")
                shutil.copyfile(fs, kept)
            clk_res = clock_resources(os.path.join(d, "run", "impl", "pnr",
                                                   "run.rpt.txt"))
            errs = []
            gwlog = os.path.join(d, "gw_sh.log")
            if os.path.isfile(gwlog):
                for line in open(gwlog, errors="replace"):
                    if "ERROR" in line.upper():
                        errs.append(line.strip())
            shutil.rmtree(os.path.join(d, "run"), ignore_errors=True)
            if verdict == "ok" and kept:
                ok += 1
            else:
                verdict, aborted = "refused", aborted + 1
            row = {"run_id": f"{args.batch_id}-{name}", "shape": "clocking_dhcen_trace",
                   "primitive": "DHCE", "n_dhce": n, "verdict": verdict,
                   "tie_resetn": bool(args.tie_resetn),
                   "wall_clock_s": wall, "fs": kept, "detail": detail,
                   "errors": errs[:6], "clock_resources": clk_res,
                   "task": "P1.T25", "device": DEVICE,
                   "gowinhome": oracle.resolve_gowinhome(None),
                   "edu_provisional": False, "ts": time.time()}
            rows.append(row)
            with open(args.ledger, "a") as lf:
                lf.write(json.dumps(row) + "\n")
            log(fh, f"RUN {name} n_dhce={n} verdict={verdict} wall={wall}s "
                    f"dhce={clk_res.get('DHCE')} errs={errs[:2]}")

        # ---- trace ---------------------------------------------------------
        from fuzz.gw5ast138c.harness.equiv import load_db
        log(fh, "TRACE loading chipdb")
        db = load_db(DEVICE)
        traces = {}
        for r in rows:
            if not r["fs"] or r["n_dhce"] not in trace_points:
                continue
            t0 = time.time()
            traces[r["n_dhce"]] = trace_enable_wires(r["fs"], db)
            cands = traces[r["n_dhce"]]["candidates"]
            log(fh, f"TRACE n={r['n_dhce']} cands={len(cands)} "
                    f"ends={[len(c['ends']) for c in cands[:3]]} "
                    f"wall={round(time.time() - t0, 1)}s")
            if cands:
                log(fh, f"TRACE n={r['n_dhce']} top={cands[0]['ends']}")

        json.dump({"rows": rows, "traces": traces}, open(args.result, "w"),
                  indent=1, default=str)
        if args.budget:
            with open(args.budget, "a") as bf:
                bf.write(f"{args.batch_id}\tdhcen\t{len(points)}\t-\t"
                         f"{time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime())}\n")
        # written raw, at line start: the watchdog greps `^BATCH_COMPLETE <id> `
        fh.write(f"BATCH_COMPLETE {args.batch_id} runs={len(points)} ok={ok} "
                 f"diff=0 aborted={aborted}\n")
        fh.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
