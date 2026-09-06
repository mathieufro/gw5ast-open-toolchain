import json, os, sys, time
sys.path.insert(0, "<apicula worktree for clocking/dqce-dcs-quadrants-138c>")
from fuzz.gw5ast138c.harness import attribute
from fuzz.gw5ast138c.harness.equiv import load_db

DATASTORE = "/Users/alex/fine-line-data/open-toolchain-gw5ast"
BASELINE_FS = os.path.join(DATASTORE, "oracle-smoke", "run", "impl", "pnr", "run.fs")
FSDIR = "/private/tmp/claude-501/-Users-alex-fine-line/c69a0923-3e81-4174-918e-14c4125b8202/scratchpad/dqce-probe-out2/fs"

t0=time.time()
db = load_db("GW5AST-138C")
print("db loaded", time.time()-t0, flush=True)

base_tiles = attribute.load_tile_bitmaps(BASELINE_FS, db=db)
print("base loaded", time.time()-t0, flush=True)

out = {}
for name in ("A4", "B4"):
    t = attribute.load_tile_bitmaps(os.path.join(FSDIR, f"{name}.fs"), db=db)
    print(name, "loaded", time.time()-t0, flush=True)
    deltas = attribute.presence_diff(base_tiles, t)
    print(name, "diffed", time.time()-t0, flush=True)
    per = {}
    for fd in deltas:
        per[(fd.tile_y, fd.tile_x)] = per.get((fd.tile_y, fd.tile_x), 0) + 1
    out[name] = sorted(((rc[0], rc[1], c) for rc, c in per.items()), key=lambda x: (-x[2], x[0], x[1]))
    print(name, out[name][:12], flush=True)

json.dump(out, open("/private/tmp/claude-501/-Users-alex-fine-line/c69a0923-3e81-4174-918e-14c4125b8202/scratchpad/diff_fast.json", "w"), indent=1)
print("DONE", time.time()-t0)
