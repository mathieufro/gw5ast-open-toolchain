# TLVDS differential IO on GW5AST-138C

## Row

**`E1` on all three points**, `cells` 0, `attrs` 0, `conns` 0, both decode
checks `ok`, no unexplained bit. **3 oracle runs** (`p3-tlvds`, ledger
`evidence/_budget/iologic-runs.tsv`, cumulative 92/140). The open half was
rebuilt afterwards at no run cost (`tools/redo_open_half.py`) for the packer
fix below and the new chipdb.

| point | primitive | level | verdict | cells / attrs / conns | decode c1 / c2 |
|---|---|---|---|---|---|
| `tlvds-ibuf` | `TLVDS_IBUF` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `tlvds-obuf` | `TLVDS_OBUF` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `tlvds-tbuf` | `TLVDS_TBUF` | `E1` | ok | 0 / 0 / 0 | ok / ok |

## The 3.3 V question, answered

The blueprint asks the sweep to *verify* that the vendor accepts TLVDS at
`BANK_VCCIO=3.3` rather than assume it. It does: all three types placed,
routed and generated a bitstream on bank 3 with the pair's bank declared at
3.3 V. That is the die's only `TRUELVDS` pair (`J14`/`H14` = `IOR103A`/`B`,
tile `(181,102)`), and bank 3 on this board carries nothing but the HDMI TMDS
pairs.

The contrast with ELVDS is the measurement that makes this meaningful:
`ELVDS_*` at the same balls, same bank, same 3.3 V is **refused**
(`evidence/elvds/`). So 3.3 V is not a blanket differential rail on this die
— it is TLVDS's.

## The one packer delta, and the fix

The P half of a `TLVDS_OBUF` was the only configuration that differed. On tile
`(181,102)` `IOBA` the vendor programs `ODMUX_1='1'` and leaves `PERSISTENT`
clear; the inherited `GW5A` default set programs `ODMUX_1='UNKNOWN'` — the
zero code, which costs no fuse and so reaches the bitstream as nothing — and
`PERSISTENT='OFF'`.

Those two attributes are exactly the ones `gowin_unpack`'s mode rule reads
(`gowin_unpack.py:926-931`: `PERSISTENT=OFF` ⇒ `IOBUF`, else `ODMUX*` ⇒
`OBUF`), so the over-emission did not just move two fuses — it turned a pure
differential **output** into an `IOBUF`, an input path enabled on a pad the
design only drives.

The fix is half-specific, because the N half is exact as inherited: `Device`
gains `tlvds_obuf_attrs(idx_str)` returning the one list every other family
uses, and `GW5AST_138C` overrides it to answer with a `PERSISTENT`-free,
`ODMUX_1='1'` list for the `A` half only. `TLVDS_TBUF` and `TLVDS_IBUF` were
byte-identical to the vendor before the fix and are untouched by it.

## What carries `E1` here

An IO-only design has no `CLS` cell, so `INS_LOC`'s half of `E1` has nothing
to assert (`EC9`). `IOB` therefore joins `BITSTREAM_ADDRESSED_CELL_TYPES`
beside `IOLOGIC`, `CLKDIV` and `PLL`: an IOB's site is a package ball fixed by
the **same `IO_LOC` line in both flows**, so a mismatch would be a broken
constraint path rather than a placer's choice. On its own that is weak — the
vendor configures every pad on the die — and what makes it evidence is the
scope beside it: the row's `E0` is restricted to tile `(181,102)`, where the
buffer under test is, and it is `cells` 0 / `attrs` 0 / `conns` 0 there.

## Deviations from the blueprint's literal text

The blueprint budgeted **6** runs for "type identity (3) plus `DRIVE` where
the vendor exposes it". The vendor exposes no `DRIVE` on a differential pad —
the pair carries `PULL_MODE`/`PULL_STRENGTH`/`BANK_VCCIO` and no `IO_TYPE` at
all, which is how the vendor's own `tang_mega_138K_pins.cst` spells the TMDS
pairs — so type identity is the whole axis and the row is **3** points. The
three tests are named as the blueprint names them, with `3` where it says `6`.
