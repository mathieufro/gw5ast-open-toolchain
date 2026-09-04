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
