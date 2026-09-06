"""P1.T29/T31 -- how many `DCE` and `DCS` the GW5AST-138C really carries.

`P1.T28` measured which grid cells the pre-5A tile-type search resolves to;
it could not say how many primitives those cells host, because a 4-instance
probe cannot exhaust a 6-slot model.  This driver asks the vendor directly:
build `n` simultaneous instances for a rising `n` and record the first `n`
the vendor refuses, together with its own `Clock Resource Usage Summary`.

Usage (from `$FL_WT/apicula`):

    python <this file> --kind dce --points 1,12,13 \
        --out-root <scratch> --log <batch log> --ledger <jsonl> --result <json>
"""
import argparse, json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import oracle                      # noqa: E402
from fuzz.gw5ast138c.shapes import clocking_dqce, clocking_dcs   # noqa: E402

SHAPES = {"dce": (clocking_dqce, "DCE", "clocking_dqce"),
          "dcs": (clocking_dcs, "DCS", "clocking_dcs")}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=sorted(SHAPES), required=True)
    ap.add_argument("--points", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--batch-id", required=True)
    args = ap.parse_args()

    shape, primitive, shape_name = SHAPES[args.kind]
    points = [int(p) for p in args.points.split(",") if p]
    fsdir = os.path.join(args.out_root, "fs")
    os.makedirs(fsdir, exist_ok=True)
    os.makedirs(os.path.dirname(args.ledger), exist_ok=True)
    rows, ok, aborted = [], 0, 0

    with open(args.log, "a") as fh:
        log(fh, f"BATCH_START {args.batch_id} runs={len(points)}")
        for n in points:
            name = f"{args.kind}{n:02d}"
            d = os.path.join(args.out_root, name)
            shutil.rmtree(d, ignore_errors=True)
            shape.write_design(d, n)
            t0 = time.time()
            verdict, detail = "ok", ""
            try:
                res = oracle.run_oracle(d, timeout=1800)
                if not res["preflight"].ok:
                    verdict, detail = "refused", res["preflight"].reason
            except Exception as exc:            # a vendor refusal is a result
                verdict, detail = "refused", f"{type(exc).__name__}: {exc}"
            wall = round(time.time() - t0, 1)
            fs = os.path.join(d, "run", "impl", "pnr", "run.fs")
            kept = None
            if os.path.isfile(fs):
                kept = os.path.join(fsdir, f"{name}.fs")
                shutil.copyfile(fs, kept)
            clk_res = clock_resources(
                os.path.join(d, "run", "impl", "pnr", "run.rpt.txt"))
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
            row = {"run_id": f"{args.batch_id}-{name}", "shape": shape_name,
                   "primitive": primitive, "n": n, "verdict": verdict,
                   "wall_clock_s": wall, "fs": kept, "detail": detail,
                   "errors": errs[:6], "clock_resources": clk_res,
                   "task": "P1.T29/T31", "device": "GW5AST-138C",
                   "gowinhome": oracle.resolve_gowinhome(None),
                   "edu_provisional": False, "ts": time.time()}
            rows.append(row)
            with open(args.ledger, "a") as lf:
                lf.write(json.dumps(row) + "\n")
            log(fh, f"RUN {name} n={n} verdict={verdict} wall={wall}s "
                    f"clk_res={clk_res} errs={errs[:2]}")

        json.dump({"rows": rows}, open(args.result, "w"), indent=1, default=str)
        log(fh, f"BATCH_COMPLETE {args.batch_id} runs={len(points)} ok={ok} "
                f"diff=0 aborted={aborted}")


if __name__ == "__main__":
    main()
