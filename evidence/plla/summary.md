# `evidence/plla/` — P1 clocking evidence skeleton (`P1.T03`)

## Row

_No oracle runs recorded yet. This is the pre-measurement evidence skeleton
(`P1.T03`); rows land here as `runs.jsonl` entries appended by the
harness (`fuzz.gw5ast138c.harness.evidence.append_row`), one per
(primitive, shape, sweep point), per `spec-harness.md` §6. `runs.jsonl`
itself is created lazily on the first appended row, exactly as
`append_row` already does elsewhere in this tree — an empty `runs.jsonl`
is deliberately never committed (`D90`: "an empty ... evidence file is not
evidence")._

## Sweep

_Filled in once the owning task's first batch runs; see
`blueprints/P1-clocking.md` for this slug's sweep plan._

## Verdict

_Pending._

## Artefacts

_None yet._
