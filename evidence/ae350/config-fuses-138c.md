# `P2.T24` — the `AE350_SOC` configuration fuse set, GW5AST-138C

> **SUPERSEDED by `fuse-set-138c.md` (2026-09-07).** The filter used below
> subtracts pips and bel `modes`/`flags` but **not** the `shortval` tables of
> tile types 224/228 — which are ordinary CLS logic tiles whose `LUT`/`CLS*`
> tables occupy exactly the tile rows all 77 bits are in. Subtract every
> modelled table and the count is **0**, in five AE350 bitstreams and in the
> control. The 77 bits are one design's LUT and CLS configuration, not an
> AE350 configuration band; there is no AE350 configuration band. The two
> sentences below that are wrong as written are corrected in place: the table
> is **not** emitted (`get_AE350_SOC_fuses` returns `[]`), and the closing
> `CONFIG-FUSE-VERDICT` line is retracted. The measurement itself — which bits
> that filter leaves — stands, and is reproducible with
> `$OTC/tools/derive_ae350_band_bits.py`.

Source: the two banked runs, `p2t26-tilewires` (instantiates `AE350_SOC`) and
`p2t26-baseline` (does not). **0 new vendor runs.**

## Method

The two designs differ in all of their fabric logic, so a raw presence diff is
useless: 85 411 bits move over 1 643 tiles, 82 249 of them in ordinary `ttyp` 17
logic tiles. The block's configuration is isolated by three filters, in order:

1. keep only tiles of `ttyp` **224** and **228** — the interface bands
   `P2.T07` marked as the block's own;
2. drop every differing bit that belongs to a pip of that tile type
   (`Tile.pips` + `Tile.clock_pips`) or to a bel fuse of it (`Bel.modes`,
   `Bel.flags`) — those are routing and ordinary LUT/DFF/ALU configuration;
3. keep only bits **set** in the AE350 bitstream.

| filter | bits left |
|---|---|
| all differing bits | 85 411 |
| in `ttyp` 224/228 | 2 583 |
| not a modelled pip or bel fuse | 990 |
| set in the AE350 run | **77**, over **9** tiles |

## The control

In the baseline bitstream, **not one** of the 216 `ttyp` 224/228 tiles carries a
single unmodelled set bit. So the 77 are AE350-correlated, not a per-tile
default the diff happens to catch.

## The set

Keyed `(x, y)` = `(col, row)`; values are `(bit_row, bit_col)` inside the tile.
Every bit is in tile-bitmap rows 10-11 of a 12-row tile — a band below every
row a pip or a bel fuse of these tile types uses.

| tile | `ttyp` | bits |
|---|---|---|
| `(156, 10)` | 224 | 3 |
| `(157, 10)` | 224 | 13 |
| `(158, 10)` | 224 | 9 |
| `(159, 10)` | 224 | 9 |
| `(160, 10)` | 224 | 9 |
| `(158, 28)` | 224 | 13 |
| `(159, 28)` | 224 | 13 |
| `(159, 46)` | 224 | 5 |
| `(159, 64)` | 228 | 3 |

The literal bit list is the `routing_and_bels` filter of
`$OTC/evidence/ae350/band-bits-138c.json`. Nothing emits it: the table it once
lived in, `GW5AST_138C.AE350_SOC_CONFIG_FUSES`, is retracted, and
`get_AE350_SOC_fuses` returns `[]`.

## What this is not

The bits are **not** uniform across the nine tiles, and one AE350 design cannot
separate an unconditional block enable from a configuration that follows the
ports a design uses. The claim proved here is narrow and exact: *these* 77 bits
are set by the vendor for *this* AE350 design and by nothing in the AE350-free
one, and no pip or bel apicula models accounts for any of them. Closing the
weaker half needs a second AE350 design with a different port set — one vendor
run, not spent here.

CONFIG-FUSE-VERDICT: **RETRACTED**, superseded by `fuse-set-138c.md`'s
`FUSE-SET-VERDICT: zero, measured`. The 77 bits are `shortval:LUT`/`CLS*`
fuses of ordinary logic in CLS tiles, not block configuration.
