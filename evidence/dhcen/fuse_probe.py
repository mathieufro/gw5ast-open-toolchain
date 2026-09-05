"""P1.T26 -- attribute the DHCE enable (`CEN`) *fuses* on GW5AST-138C.

`P1.T25` measured *where* the DHCE sites are and which wire carries `CEN`.
It did not attribute a fuse: its presence diff counted moved fuses per HCLK
block cell, and the `.fs` files it produced were pruned from the datastore.

`P1.T26` has to emit fuses, so it needs the per-`(block, idx)` bit set.  This
driver takes the minimal incremental sweep that yields it inside the four-run
budget of the dispatch:

    n_div = 4 held constant, n_dhce = 0, 1, 2, 3

All four `CLKDIV` land in the first-filled block `(108, 64)` (`P1.T25` §3.2
fill order), so the *only* thing that changes between adjacent points is one
more DHCE.  `fuses(n) - fuses(n-1)` restricted to that tile is therefore the
bit set of DHCE index `n-1`; index 3 is then the one remaining member of the
same `shortval['HCLK']` family, which the analysis states explicitly rather
than measuring.

Four vendor compiles, booked to `../_budget/clocking-runs.tsv`.
"""
import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import oracle                       # noqa: E402
from fuzz.gw5ast138c.shapes import clocking_dhcen_trace as SHAPE  # noqa: E402

DEVICE = "GW5AST-138C"
BATCH_ID = "p1-dhce-fuse"

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


def log(fh, msg):
    fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    fh.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--budget", default=None)
    ap.add_argument("--pidfile", default=None)
    ap.add_argument("--n-div", type=int, default=4)
    ap.add_argument("--points", default="0,1,2,3")
    args = ap.parse_args()

    points = [int(p) for p in args.points.split(",") if p != ""]
    fsdir = os.path.join(args.out_root, "fs")
    os.makedirs(fsdir, exist_ok=True)
    ok = aborted = 0

    with open(args.log, "a") as fh:
        if args.pidfile:
            open(args.pidfile, "w").write(str(os.getpid()) + "\n")
        log(fh, f"BATCH_START {BATCH_ID} runs={len(points)} n_div={args.n_div}")
        for n in points:
            name = f"fz{n:02d}_div{args.n_div}"
            d = os.path.join(args.out_root, name)
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "top.v"), "w").write(
                SHAPE.rtl(SHAPE.SPEC, n, tie_resetn=True, n_div=args.n_div))
            open(os.path.join(d, "top.cst"), "w").write(CST)
            open(os.path.join(d, "top.sdc"), "w").write(SDC)
            t0 = time.time()
            verdict, detail = "ok", ""
            try:
                res = oracle.run_oracle(d, timeout=1800)
                if not res["preflight"].ok:
                    verdict, detail = "refused", res["preflight"].reason
            except Exception as exc:
                verdict, detail = "refused", f"{type(exc).__name__}: {exc}"
            wall = round(time.time() - t0, 1)
            fs = os.path.join(d, "run", "impl", "pnr", "run.fs")
            kept = None
            if os.path.isfile(fs):
                kept = os.path.join(fsdir, f"{name}.fs")
                shutil.copyfile(fs, kept)
            shutil.rmtree(os.path.join(d, "run"), ignore_errors=True)
            if verdict == "ok" and kept:
                ok += 1
            else:
                verdict, aborted = "refused", aborted + 1
            row = {"run_id": f"{BATCH_ID}-{name}", "shape": "clocking_dhcen_trace",
                   "primitive": "DHCE", "n_dhce": n, "n_div": args.n_div,
                   "verdict": verdict, "tie_resetn": True, "wall_clock_s": wall,
                   "fs": kept, "detail": detail, "task": "P1.T26",
                   "device": DEVICE, "gowinhome": oracle.resolve_gowinhome(None),
                   "edu_provisional": False, "ts": time.time()}
            with open(args.ledger, "a") as lf:
                lf.write(json.dumps(row) + "\n")
            log(fh, f"RUN {name} n_dhce={n} verdict={verdict} wall={wall}s "
                    f"detail={detail[:120]}")
        if args.budget:
            with open(args.budget, "a") as bf:
                bf.write(f"{BATCH_ID}\tdhcen\t{len(points)}\t-\t"
                         f"{time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime())}\n")
        fh.write(f"BATCH_COMPLETE {BATCH_ID} runs={len(points)} ok={ok} "
                 f"diff=0 aborted={aborted}\n")
        fh.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
