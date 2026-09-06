"""P1.T08d -- one BEL-constrained CLKDIV per HCLK lane, all six blocks.

P1.T08c could only measure HCLK block 5 because the vendor placed every design
there and no placement handle was known.  There is one: UG/SUG1018 §2.9 "HCLK
Primitive Constraints" -- `INS_LOC "<inst>" BOTTOMSIDE[n];` with
`{LEFT,RIGHT,BOTTOM}SIDE[0~7]` on the GW5A(S)(T)-138.  Twenty-four positions,
six blocks x four lanes.

This runner builds one design per position, each holding exactly ONE CLKDIV
whose CLKOUT clocks a counter (so the output must escape onto a global spine),
and charges one oracle run per position.  The decode is `probe_clkmux.py`:
the HCLK block cell's lit table-48 `HCLK_MUX_BETA0i <= L2HCLK0i` row names the
(block, lane), and the central clock mux's lit table-38 row names the clock
wire.  Together they are the (block, lane) -> clock-wire bijection.

Run from the apicula worktree with PYTHONPATH=. :
    python staircase_blocks.py --out-root <scratch> --log <log> \
        --ledger <jsonl> --result <json> [--only BOTTOMSIDE:4]
"""
import argparse, json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import oracle  # noqa: E402

BATCH_ID = "p1t08d-insloc"

# The p1t08c CST, unchanged: banks 4/5 only, never the PR #423 bank-6/7 class.
CST = """IO_LOC  "led[0]" P19;
IO_PORT "led[0]" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8 BANK_VCCIO=3.3;
IO_LOC  "led[1]" R19;
IO_PORT "led[1]" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8 BANK_VCCIO=3.3;
IO_LOC  "led[2]" T21;
IO_PORT "led[2]" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8 BANK_VCCIO=3.3;
IO_LOC  "led[3]" U21;
IO_PORT "led[3]" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8 BANK_VCCIO=3.3;
IO_LOC "clk" V22;
IO_PORT "clk" IO_TYPE=LVCMOS33 PULL_MODE=NONE BANK_VCCIO=3.3;
IO_LOC  "reset" Y12;
IO_PORT "reset" IO_TYPE=LVCMOS33 PULL_MODE=UP BANK_VCCIO=3.3;
"""
SDC = "create_clock -name clk -period 20 -waveform {0 10} [get_ports {clk}]\n"
POSITIONS = [(side, i) for side in ("LEFTSIDE", "RIGHTSIDE", "BOTTOMSIDE")
             for i in range(8)]

RTL = """module top (
\tinput wire clk,
\tinput wire reset,
\toutput wire [3:0] led
);
\twire dclk;
\tCLKDIV div0 (.HCLKIN(clk), .RESETN(reset), .CALIB(1'b0), .CLKOUT(dclk));
\tdefparam div0.DIV_MODE = "2";
\treg [11:0] ctr0;
\talways @(posedge dclk) ctr0 <= ctr0 + 1;
\tassign led[0] = ctr0[11];
\tassign led[1] = ctr0[10];
\tassign led[2] = ctr0[9];
\tassign led[3] = ctr0[8];
endmodule
"""


def write_design(d, side, idx):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "top.v"), "w").write(RTL)
    open(os.path.join(d, "top.cst"), "w").write(
        CST + f'INS_LOC "div0" {side}[{idx}];\n')
    open(os.path.join(d, "top.sdc"), "w").write(SDC)


def log(fh, msg):
    fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    fh.flush()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--only", default=None, help="SIDE:idx[,SIDE:idx...]")
    args = ap.parse_args(argv)

    plan = POSITIONS
    if args.only:
        want = {(s.split(":")[0], int(s.split(":")[1])) for s in args.only.split(",")}
        plan = [p for p in POSITIONS if p in want]

    fsdir = os.path.join(args.out_root, "fs")
    os.makedirs(fsdir, exist_ok=True)
    rows, ok, aborted = [], 0, 0
    with open(args.log, "a") as fh:
        log(fh, f"BATCH_START {BATCH_ID} runs={len(plan)}")
        for side, idx in plan:
            name = f"{side.lower()}{idx}"
            d = os.path.join(args.out_root, name)
            shutil.rmtree(d, ignore_errors=True)
            write_design(d, side, idx)
            t0 = time.time()
            verdict, detail = "ok", ""
            try:
                res = oracle.run_oracle(d, timeout=1800,
                                        extra_options=("-use_sspi_as_gpio 1",))
                if not res["preflight"].ok:
                    verdict, detail = "refused", res["preflight"].reason
            except Exception as exc:                    # a vendor refusal is a result
                verdict, detail = "refused", f"{type(exc).__name__}: {exc}"
            wall = round(time.time() - t0, 1)
            fs = os.path.join(d, "run", "impl", "pnr", "run.fs")
            kept = None
            if os.path.isfile(fs):
                kept = os.path.join(fsdir, f"{name}.fs")
                shutil.copyfile(fs, kept)
            errs = []
            gwlog = os.path.join(d, "gw_sh.log")
            if os.path.isfile(gwlog):
                for line in open(gwlog, errors="replace"):
                    u = line.upper()
                    if "ERROR" in u or "WARN" in u and "INS_LOC" in u:
                        errs.append(line.strip())
            shutil.rmtree(os.path.join(d, "run"), ignore_errors=True)
            if verdict == "ok" and kept:
                ok += 1
            else:
                verdict, aborted = "refused", aborted + 1
            row = {"run_id": f"{BATCH_ID}-{name}", "shape": "clkdiv_insloc_lane",
                   "primitive": "CLKDIV", "ins_loc": f"{side}[{idx}]",
                   "verdict": verdict, "wall_clock_s": wall, "fs": kept,
                   "detail": detail, "errors": errs[:6], "task": "P1.T08d",
                   "device": "GW5AST-138C", "edu_provisional": False,
                   "gowinhome": oracle.resolve_gowinhome(None), "ts": time.time()}
            rows.append(row)
            with open(args.ledger, "a") as lf:
                lf.write(json.dumps(row) + "\n")
            log(fh, f"RUN {name} verdict={verdict} wall={wall}s errs={errs[:2]}")
        json.dump({"rows": rows}, open(args.result, "w"), indent=1)
        log(fh, f"BATCH_COMPLETE {BATCH_ID} runs={len(plan)} ok={ok} diff=0 "
                f"aborted={aborted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
