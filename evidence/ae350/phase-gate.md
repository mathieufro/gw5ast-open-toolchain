# Phase 2 gate — the four `V` steps, run at the second-pass tip

`blueprints/P2-ae350.md` §5's gate step reads one verdict line off this file.
It is written once, at the close, and only after the four steps below have been
run in the foreground on the tip the phase ships: apicula `epic/gw5ast138c`
`d165577`, nextpnr `epic/gw5ast138c` `850912d0`, open-toolchain `main`.
Full transcripts: `evidence/phase2/validation.md`, §Second pass.

| step | command | result |
|---|---|---|
| `V18` | `check_criteria.py --ae350` | `AE350 ok: 4/4`, exit 0 — every clause read out of the chipdb, the packer or the `.dat`, none out of this phase's prose |
| `V14` | `check_criteria.py <spec-primitives.md> <evidence> --phase 2` | `CRITERIA ok: 4/4`, `PHASE-REPORT phase2/phase-report.md: 1 REACHED, 1 backed, 0 unlinked, 0 unbacked` |
| `V20` | the `D41` storage-hygiene triple | `OK-evidence-gitignore`, `OK-manifests`, `OK-no-binaries` |
| `D50` budget box | `n <= 90` over the three slugs, and the mandatory checkpoint | `17` rows; `RESCOPE-VERDICT` rev 6 closes the `ae350` ledger at 8 of 8 |

`D50`'s checkpoint is `rescope.md`, not `checkpoint-45.md` (`A20`): the phase
finished at 8 vendor runs, which is `F8`'s "written at phase end if the phase
finishes below 45" path.

The dual-purpose namespace tests `P2.T30` locks in, and every other `ae350` and
`dualpin` test, ran in the same pass: `92 passed`, 0 failed, with `GOWINHOME`
exported so none of them skips.

PHASE2-GATE: pass
