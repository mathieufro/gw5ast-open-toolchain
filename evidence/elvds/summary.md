# ELVDS differential IO on GW5AST-138C

## Row — `refused`, with the oracle's own words

The three ELVDS types the family offers (`ELVDS_OBUF`, `ELVDS_TBUF`,
`ELVDS_IOBUF` — UG304E documents no `ELVDS_IBUF`; the input side is
`ELVDS_IOBUF`) are **refused by the vendor at every VCCIO level this board
can reach outside banks 6/7**, which is 3.3 V and only 3.3 V.

| point | primitive | level | verdict | vendor |
|---|---|---|---|---|
| `elvds-obuf` | `ELVDS_OBUF` | — | refused | `ERROR (CT1108): Illegal port attribute value specified 'BANK_VCCIO = 3.3' on 'pad_p'` / `on 'pad_n'` |
| `elvds-tbuf` | `ELVDS_TBUF` | — | refused | same |
| `elvds-iobuf` | `ELVDS_IOBUF` | — | refused | same |

`DONE-STD` admits this: *"a type the vendor does not offer is `refused` with
the oracle artefact"*. The artefact is `run.tcl` + `gw_sh.log` per point under
`$DATASTORE/open-toolchain-gw5ast/p3t25/`, and the rows carry the text.

**3 oracle runs** for the sweep (`p3-elvds`, ledger cumulative 96/140) plus
**2** for the matrix probe below (`p3-elvds-vccio`, 98/140).

## The matrix — recorded, not asserted

The refusal names the *attribute value*, so on its own it cannot separate
"ELVDS is illegal on this die" from "ELVDS is illegal at 3.3 V". Two more
oracle runs settle it (`tools/probe_elvds_vccio.py`, moving **only** bank 3's
rail and leaving the single-ended pins at 3.3 V so a refusal is about the
ELVDS pad and nothing else):

| `BANK_VCCIO` on bank 3 | vendor |
|---|---|
| 3.3 V | refused, `CT1108` |
| **2.5 V** | **accepted** — placed, routed, bitstream generated; the vendor's own pin report gives the pair `IO_TYPE=LVDS25E` |
| 1.8 V | refused, `CT1108` |
| 1.5 V (`SSTL15D`, bank 6 DQS) | not built — see the deferred point |

Full table with run ids in `vccio-matrix.tsv`.

**This refutes `spec-primitives.md`'s standing claim.** The spec says
`LVDS25E` "is only apicula's default `IO_TYPE` for ELVDS … it is **not** a
VCCIO requirement, and the earlier claim that 'ELVDS needs 2.5 V VCCIO' was
wrong". Measured on this die, the earlier claim was right and the correction
was wrong: the vendor gates `ELVDS_OBUF` to **exactly** 2.5 V — not a
ceiling, since 1.8 V is refused too — and names the standard `LVDS25E` itself
when it accepts. Recorded here rather than argued: two runs, two refusals and
one acceptance.

## What this means for the board

Every bank the Tang Mega 138K brings out below banks 6/7 runs at 3.3 V
(`_io_base.SAFE_PINS`, 34 balls, cross-checked against the vendor pinout for
all 297 balls of the package). No ELVDS buffer is therefore usable on this
board outside the DDR3 banks — which is consistent with where the golden
netlist actually puts them: `ELVDS_IOBUF` ×2 on the DDR3 DQS pins, in a bank
hard-wired to 1.5 V.

## The deferred point

deferred-point: elvds-iobuf-sstl15d -> P5b

The 1.5 V / `SSTL15D` `ELVDS_IOBUF` on the DDR3 DQS pins needs a bank-6 ball,
which Phase-3 shape identity forbids (`D54`, `spec-harness.md` §7). It is
**not** built here. `P5b.T27` sweeps it and appends it, append-only, to this
same `evidence/elvds/` slug; Phase 5b may not close its DQS row until it has.
That narrowing of the ELVDS↔DQS cross-link is **`SA-P3-1`**, recorded in
`spec-primitives.md`'s amendment log and cited in every row's `notes`.
`deferred-point:` is prose and appears in no status cell — it is not in the
status vocabulary.

## Deviations from the blueprint's literal text

- **10 runs budgeted, 5 spent.** The blueprint's 10 assumed a type × VCCIO
  grid. The board offers one level, so the grid collapses to 3 types × 3.3 V,
  and the two probe runs buy the rest of the matrix.
- **The row reads `refused:`, not `E1`.** `P3.T25`'s Done-when says the cell
  reads exactly `E1`; that was written expecting ELVDS to build. It does not,
  and a measured refusal with the vendor's words is the stronger row.
  `SA-P3-1` is still what makes the DQS point a named deferral rather than a
  hole, so it is recorded and cited either way.
