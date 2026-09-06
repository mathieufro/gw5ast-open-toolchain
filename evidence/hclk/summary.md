# `evidence/hclk/` — GW5AST-138C HCLK

## Row

One row so far, `hclk-note-0001` — `kind=note`: the P1.T05-T09 verification
record, not an oracle/fuzz run (`level: E0`, `verdict: ok`, no vendor run
charged). Its full write-up is `port-138c.md`; the measured topology it is
checked against is `../clocking/hclk-topology.md` (P1.T04).

## Sweep

None. The measurement sweep for this slug is P1.T04's (14 vendor runs, recorded
in `../clocking/oracle-runs.jsonl`); P1.T14-T16 add the CLKDIV / CLKDIV2 /
HCLK-to-FCLK shape rows.

## Verdict

P1.T05, T06, T07, T08 **PASS**; P1.T09 **FIXED** (it was missing from the
landed commits). Built 138C chipdb: 6 HCLK blocks x 4 = 24 CLKDIV + 24 CLKDIV2,
halves 2 top / 4 bottom, `HAS_5A_HCLK` set. GW5A-25A chipdb byte-identical to
the Phase-0 baseline. Openflow smoke still routes.

**Not closed**: the 138C's HCLK *routing* model is still four-block and
fuse-less — `gw5_hclk_idx` returns `-1` for the 138C and
`gw5_make_hclk_pips`' default-PIP section is `range(4)`. Both are pre-existing
25A-shaped code outside Phase 1's owned-function list, both are measured and
quantified in `port-138c.md` §FINDINGS, and P1.T14-T16 cannot close `S8`'s
HCLK->FCLK half until they are taken.

## Artefacts

- `port-138c.md` — the verification write-up (verdicts, hashes, findings)
- `runs.jsonl` — the rows, including the two E2E rows whose `primitive` is
  `HCLK block` (`p1t40-e2e-clocking_e2e-0000`, `p1t38b-e2e2-clocking_e2e-0000`).
  They were produced by the `clocking_e2e` shape and are filed here, under the
  primitive's own slug, per `spec-harness.md` §6 — `evidence/clocking/` keeps
  the design's artefacts and no `runs.jsonl` (`P1.F1`, gestalt `B1a`)
- `../_runs/hclk-port-138c-openflow.log` — the openflow smoke log
- `$DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin`
  sha256 `0227f0914c615cf6858c8cb4e0e1e17afbe7d2c399d705a9c01dd12bc5ac14b3`, 63,860,996 B
