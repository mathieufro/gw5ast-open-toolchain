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

## Local blocking gate (C8, S23b)

This repo has a local blocking gate, mirroring the one in the `apicula` and
`nextpnr` checkouts: `.githooks/pre-commit` and `.githooks/pre-push` both run
`make gate` in the foreground and refuse the commit/push on any failing
check. `pre-push` gates at `GATE_SCOPE=all` when pushing to `main` or
`integration`, `full` otherwise. `gate.env` carries the `GOWINHOME`/`DYLD_*`
defaults; the gate's own Python interpreter is derived from the checkout
location (no hardcoded path) in the `Makefile`.

The hooks only run once `core.hooksPath` is pointed at `.githooks` --
this is a local (not versioned) git config, set once per checkout:

```
git config core.hooksPath .githooks
```

Run `make gate` by hand at any time to check the tree without committing.
