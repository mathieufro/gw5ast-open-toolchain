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

## `P1.F3` — four independent global clock nets, and the E2E re-run

Two rows added to `runs.jsonl`. The four-global-net defect, its second half
(a global net left half-bound, which hangs the timing analyser rather than
failing), and the change are in `../clocking/four-globals-138c.md`.

### Sweep

Single-point on both: `clocking_four_globals` is four buffered clocks plus one
`CLKDIV` on block 5 lane 0, pinned on both sides so the comparison has a
fuse-backed scope; `clocking_e2e` is `P1.T40`'s end-to-end clock tree,
unchanged, re-run through the new pair.

### Verdict

```
BATCH_COMPLETE p1f3-c runs=1 ok=1 diff=0 aborted=0
BATCH_COMPLETE p1f3-e2e runs=1 ok=1 diff=0 aborted=0
```

| run | shape | level | verdict | cells/attrs/conns | unexplained | decode |
|---|---|---|---|---|---|---|
| `p1f3-c-clocking_four_globals-0000` | `clocking_four_globals` | `E1` | **ok** | 0/0/0 | **none** | c1 ok (21/21), c2 ok |
| `p1f3-e2e-clocking_e2e-0000` | `clocking_e2e` | `E1` | **ok** | 0/0/0 | **none** | c1 ok (18/18), c2 ok |

The same `clocking_four_globals` design on the pre-fix pair
(binary `cfc97099…`, `.bin` `d700cade…`) is `ERROR: Can't route the
clk0_IBUF_I_O net`, nextpnr exit 125.

Pair: nextpnr binary `28f4cbeb…`, `chipdb-GW5AST-138C.bin` `0206b922…`,
`GW5AST-138C.msgpack.xz` `6e95b906…`, installed together. The `apicula_sha`
and `nextpnr_sha` the rows carry are the commits the working trees were on
when the batches ran; the change itself is `apicula 4aba1ef` /
`nextpnr 17610ef3`.
