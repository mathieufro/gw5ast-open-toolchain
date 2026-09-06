# gw5ast-open-toolchain

Evidence, check tools and gate scripts for the open FPGA toolchain on the Gowin
GW5AST-LV138PG484AC1/I0 (Tang Mega 138K). The fuzzing harness itself lives in the
apicula fork (`fuzz/gw5ast138c/`); nextpnr changes live in the nextpnr fork.

- `evidence/` — one directory per primitive/slug with `runs.jsonl` rows (29-field schema
  defined in the apicula harness `evidence.py`), sha256 manifests, small logs. Bitstreams and
  run trees stay in the data store (`~/fine-line-data/open-toolchain-gw5ast`), referenced by sha256.
- `tools/` — DEL-e checks: `check_evidence.py`, `check_criteria.py`, `check_timing_l0.py`, with tests.
- `*.sha256` — manifests of the archived vendor device trees and docs.

Pipeline documents (spec, roadmap, blueprints, ledger) are NOT here: they live in
`fine-line/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84/`.

## Local gate (C12, D94-D95; supersedes C8/S23b's blocking pre-commit shape)

Owner ruling: "ci should only run on big branch push like main or dev, not
on every push, we don't have time for this (and also it should be
detached)". There is **no `pre-commit` hook**. `.githooks/pre-push` is the
only hook, mirroring the one in the `apicula` and `nextpnr` checkouts (and
the umbrella): it reads the pushed refs once and, unless one targets `main`,
`dev`, `integration/*` or `epic/*`, exits 0 immediately -- a task-branch push
gets zero gate. Otherwise it spawns `make gate GATE_SCOPE=branch` **detached**
(nohup, logged to `evidence/_gates/<repo>-<branch>-<sha>.log`, watched by an
out-of-process stall watchdog, `tools/gate_watchdog.sh`) and still exits 0
right away -- **a push is never blocked**. The gate writes
`<same-stem>.result` (`PASS`/`FAIL`) as its last action. As of D181
(2026-09-06) the hook above is a no-op unless `LANDING_GATE=1` is set for that
push -- no push runs a gate any more; landings are checked by targeted tests,
full gates run once at phase close.

`GATE_SCOPE=fast` is unit tests only (no bitstream, no evidence tools,
target < 30 s); `GATE_SCOPE=branch` is fast plus the evidence/criteria tools
run for real (`check_evidence.py`, `check_criteria.py --phase <n>`);
`GATE_SCOPE=full` is everything including heavy checks and is
orchestrator-only, run in the foreground at phase close / pre-merge, never
from a hook. `gate.env` carries the `GOWINHOME`/`DYLD_*` defaults; the
gate's own Python interpreter is derived from the checkout location (no
hardcoded path) in the `Makefile`.

Run `tools/gate_status.py` to list every gate marker under
`evidence/_gates/` (PASS/FAIL/RUNNING with age); it exits non-zero if any
gate FAILed or a RUNNING gate is stale (> 30 min) -- the orchestrator checks
this (or runs `GATE_SCOPE=full make gate` itself) before any merge.

The hook only runs once `core.hooksPath` is pointed at `.githooks` --
this is a local (not versioned) git config, set once per checkout:

```
git config core.hooksPath .githooks
```

Run `make gate GATE_SCOPE=<fast|branch|full>` by hand at any time to check
the tree without pushing.
