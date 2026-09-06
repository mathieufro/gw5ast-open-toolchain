"""P1.T28 -- 8 oracle runs re-deriving the 138C DQCE/DCS tile-hosting cells.

Runs `fuzz.gw5ast138c.shapes.clocking_dqce_probe.PLAN` (8 designs: two
CE-assignment sequences A/B, each sweeping 1..4 simultaneous DQCE instances)
through the vendor oracle, keeps every `.fs`, then `presence_diff`s each
build against its predecessor in the same sequence (and against a shared
DQCE-free baseline reused from `oracle-smoke`, no fresh compile spent on it)
to find which physical tile gains fuses when the Nth DQCE instance is added.

Prerequisite: `<apicula worktree>/apycula/GW5AST-138C.msgpack.xz` must exist
(`attribute.load_tile_bitmaps` needs it to segment a `.fs` into tiles) --
build it with `python3 -m apycula.chipdb_builder GW5AST-138C` if missing, or
copy the one an already-built sibling worktree has (this repo's
`.gitignore` excludes `*.msgpack.xz`; it is a local build artefact, not a
tracked file, same as every other clocking task's chipdb).

Usage (from `$FL_WT/apicula`, the `clocking/dqce-dcs-quadrants-138c`
worktree):

    python /path/to/evidence/dqce/run_probe.py \\
        --out-root <scratch> --log <batch log> \\
        --ledger $OTC/evidence/dqce/runs/oracle-runs.jsonl \\
        --result $OTC/evidence/dqce/runs/diff-result.json
"""
import argparse, json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.getcwd())
from fuzz.gw5ast138c.harness import oracle, attribute  # noqa: E402
from fuzz.gw5ast138c.shapes import clocking_dqce_probe as probe  # noqa: E402

BATCH_ID = "p1-dqce-types"
DATASTORE = oracle.paths.datastore()
BASELINE_FS = os.path.join(DATASTORE, "oracle-smoke", "run", "impl", "pnr", "run.fs")


def log(fh, msg):
    fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    fh.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--result", required=True)
    args = ap.parse_args()

    plan = probe.PLAN
    fsdir = os.path.join(args.out_root, "fs")
    os.makedirs(fsdir, exist_ok=True)
    os.makedirs(os.path.dirname(args.ledger), exist_ok=True)
    rows, ok, aborted = [], 0, 0
    with open(args.log, "a") as fh:
        log(fh, f"BATCH_START {BATCH_ID} runs={len(plan)}")
        for name, seq, n in plan:
            d = os.path.join(args.out_root, name)
            shutil.rmtree(d, ignore_errors=True)
            probe.write_design(d, seq, n)
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
            errs = []
            gwlog = os.path.join(d, "gw_sh.log")
            if os.path.isfile(gwlog):
                for line in open(gwlog, errors="replace"):
                    if "ERROR" in line.upper() or line.startswith("CT") or "Error" in line:
                        errs.append(line.strip())
            shutil.rmtree(os.path.join(d, "run"), ignore_errors=True)
            if verdict == "ok" and kept:
                ok += 1
            else:
                verdict, aborted = "refused", aborted + 1
            row = {"run_id": f"{BATCH_ID}-{name}", "shape": "clocking_dqce_probe",
                   "primitive": "DQCE", "sequence": seq, "n_dqce": n,
                   "verdict": verdict, "wall_clock_s": wall, "fs": kept,
                   "detail": detail, "errors": errs[:6],
                   "task": "P1.T28", "device": "GW5AST-138C",
                   "gowinhome": oracle.resolve_gowinhome(None),
                   "edu_provisional": False, "ts": time.time()}
            rows.append(row)
            with open(args.ledger, "a") as lf:
                lf.write(json.dumps(row) + "\n")
            log(fh, f"RUN {name} seq={seq} n_dqce={n} verdict={verdict} "
                    f"wall={wall}s errs={errs[:2]}")

        # ---- presence diffs -------------------------------------------------
        log(fh, "DIFF loading chipdb")
        from fuzz.gw5ast138c.harness.equiv import load_db
        db = load_db("GW5AST-138C")
        base_tiles = None
        if os.path.isfile(BASELINE_FS):
            base_tiles = attribute.load_tile_bitmaps(BASELINE_FS, db=db)
            log(fh, f"DIFF baseline reused from {BASELINE_FS} (no fresh compile)")
        else:
            log(fh, f"DIFF no baseline at {BASELINE_FS}; skipping baseline diff")

        by_seq = {"A": {}, "B": {}}
        for r in rows:
            if r["fs"]:
                by_seq[r["sequence"]][r["n_dqce"]] = r["fs"]

        summary = {}
        for seq in ("A", "B"):
            prev_tiles = base_tiles
            for n in (1, 2, 3, 4):
                fs = by_seq[seq].get(n)
                if not fs:
                    summary[f"{seq}{n}"] = {"error": "no .fs (refused)"}
                    continue
                t = attribute.load_tile_bitmaps(fs, db=db)
                added = {}
                if prev_tiles is not None:
                    deltas = attribute.presence_diff(prev_tiles, t)
                    for fd in deltas:
                        added[(fd.tile_y, fd.tile_x)] = added.get((fd.tile_y, fd.tile_x), 0) + 1
                vs_base = {}
                if base_tiles is not None:
                    deltas_b = attribute.presence_diff(base_tiles, t)
                    for fd in deltas_b:
                        vs_base[(fd.tile_y, fd.tile_x)] = vs_base.get((fd.tile_y, fd.tile_x), 0) + 1
                summary[f"{seq}{n}"] = {
                    "new_vs_prev": sorted(((rc[0], rc[1], c) for rc, c in added.items()),
                                           key=lambda x: (-x[2], x[0], x[1])),
                    "all_vs_baseline": sorted(((rc[0], rc[1], c) for rc, c in vs_base.items()),
                                               key=lambda x: (-x[2], x[0], x[1])),
                }
                log(fh, f"DIFF {seq}{n} new_vs_prev={summary[f'{seq}{n}']['new_vs_prev'][:8]}")
                prev_tiles = t

        json.dump({"rows": rows, "diffs": summary}, open(args.result, "w"), indent=1)
        log(fh, f"BATCH_COMPLETE {BATCH_ID} runs={len(plan)} ok={ok} diff=0 aborted={aborted}")
    return 0 if aborted == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
