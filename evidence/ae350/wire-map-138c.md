# `AE350_SOC` fabric wire map — GW5AST-138C

> **Superseded as the map of record by `portmap-reconciled-138c.md`.** That
> file is generated from the chipdb the router loads and is the one place the
> map, the direction convention and the residual are stated. Retracted here:
> **the 867 bound / 44 unbound pairing** of §4-§6, which belongs to the
> pre-`6e58e8b` generation — the current map binds **884 of 911** with **27**
> unmapped, and `867/44` and `884/27` are the two generations, never one map.
> Nothing measured is retracted: the parser repair (§1), the table locations
> (§2, §6), the wire classes (§3) and the pip cross-check (§4) all stand, and
> §7 already carries the corrected reading.

`P2.T08a`, extended by `P2.T08b` (§6) and corrected by §7. Companion data
file: `wire-map-138c.json`, regenerated from the `.dat` by
`tools/derive_ae350_wire_map.py`; `fse_create_ae350()` reads the same tables
through its own code and `tools/tests/test_ae350_chipdb_reconciliation.py`
holds the two against each other. Status **PARTIAL**: the input half is
**MEASURED** (415 of 416 taps carry a pip the vendor set), the output half is
**DAT-DERIVED** on a **MEASURED** band. Gowin IDE Standard 1.9.12.03; runs
`p2t26-tilewires` and `p2t26-baseline`, no new vendor run.

## 1. The parser defect, and what it actually was

`P2.T26` recorded a transposed call at `dat_parser.py:545-546`. That is half of
it. The signature is

```
read_scaledGrid16(numRows, numCols, rowScaling, colScaling, baseOffset)
```

and 72 call sites pass `(numRows, numCols, numCols, RSTable5ATOffset + base, k)`
— so the base landed in `colScaling`, a small residual landed in `baseOffset`,
and `_cur` became `row * numCols + col * base * 2 + k`. **The bases at those
call sites are also u16 word offsets, not byte offsets**, which the earlier note
missed. Two independent measurements fix the layout:

- consecutive tables of this family are exactly `numRows * numCols` **words**
  apart — `Gtrl12PmacDBIns` → `Gtrl12UparDBIns` is `0x2238` = 2920 × 3 to the
  word, and `Gtrl12QuadDBOuts1` → `Gtrl12QuadDBOuts2` is 668 × 3 ± 4;
- read that way, `Ae350SocOuts` lands on real `(row, col, wire)` triples inside
  the AE350's measured footprint.

The repair is one reader, `Datfile.read_packed_grid16(num_rows, num_cols,
base_words)`, used at all 72 sites; `rowScaling` was `numCols` at every one of
them, which is the packed layout and nothing else, so the shape is stated once.

Guard: every table of `GW1N-4`, `GW1N-9`, `GW1NZ-1C`, `GW2A-18` and `GW2A-18C`
decodes **byte-identically** before and after (146 tables each, 0 changed).
`GW1N-9C` raises `PartType 4 is not supported` before and after — unchanged.
Those parts never reach `read_5Astuff`, so the repair cannot touch them; the
5-series parts `GW5A-25A` and `GW5AST-138C` change in 53 tables each, which is
the point.

## 2. Where the port map is

| table | shipped base (words) | base used | slots | live | bits of that direction |
|---|---|---|---|---|---|
| `Ae350SocOuts` | `0x8bb0` | `0x8bb1` | 518 | 492 | 495 |
| `Ae350SocIns` | `0x86a0` (stale) | `0x91ea` (§6) | 433 | 415 | 416 |

The shipped `Outs` base is one word short of the record boundary. The shipped
`Ins` base is stale the way `CibFabricNode`'s was: it points at a *different*
block's table, in columns 51-139. `P2.T08a` replaced it with `0x8314`;
`P2.T08b` shows `0x8314` is another block's table too, and that the AE350's own
input table is at `0x91ea` — see §6. The base is no longer addressed at all:
`Datfile.read_ae350_soc_ins` *locates* the table from the block's geometry.

## 3. What the tables say

Every live record has row 1, i.e. **die row 0**. The taps are in row 0 of the
band the presence diff measured. What separates the two directions is the
**wire class**, not the table (§7):

| | wires | columns (0-based) |
|---|---|---|
| inputs | `A0`-`D7`, `CLK0`-`CLK2`, `LSR1`, `LSR2`, `CE0`-`CE2` — pip destinations | 161-180, plus 87 |
| outputs | `F0`-`F7`, `Q0`-`Q7`, `OF0`-`OF7` — what only the block drives | 156-180, plus 22, 23 |

The two halves are disjoint in wire class and *overlapping* in column: the
block reads and drives the same tiles, which is what the P2.T08b relocation
first showed (§6) and the direction repair completed. The earlier reading —
inputs to the left of column 156, outputs to the right — is refuted.

**The row-0 taps are `ttyp` 242 tiles, not 224 or 228.** `ttyp` 224 (rows 10,
28, 46) and `ttyp` 228 (rows 64, 82, 100) carry the block's *configuration* —
they are where the presence diff's bits moved — but no port record names them.
`P2.T26`'s guess that the interface bands carry the ports is wrong.

## 4. The per-bit map

**Rule.** Bit *i* of a direction is record *i* of that direction's map,
counting ports in `primitive.xml` declaration order and each bus LSB first. The
input map is the fabric-driven run of `Ae350SocOuts`; the output map is
`Ae350SocOuts` outside that run with `Ae350SocIns` filling it (§7). A
`0xffff/0xffff/0xffff` record is an unbound bit, and so is the one output bit
past the end of `Ae350SocIns` inside the run.

| | bits | bound | unbound | in footprint | outside |
|---|---|---|---|---|---|
| inputs | 416 | **416** | 0 | 415 | 1 |
| outputs | 495 | **468** | 27 | 466 | 2 |

The counts in the two tables below are `P2.T08a`'s, kept as the record of what
was believed then; §7 carries the current ones.

**Slots that do not fit** (`slots_that_do_not_fit` in the JSON), as read by
`P2.T08a`; the `Ins` row is superseded by §6:

- `Ae350SocOuts`: 3 — columns 22, 23 and 87. Columns 88, 89, 95 and 96 *do*
  appear in the presence diff (the clock spine), so these are plausible and
  simply outside the band.
- `Ae350SocIns`: 142. The AE350's input table holds only **257 records** before
  the neighbouring block's table begins, against 416 input bits, so the ordinal
  rule runs off the end of it at bit 274 and the remaining slots name columns
  109-114 and 50-51, which are not the AE350's. **Input bits 0-273 are mapped;
  274-415 are not.** This is the one open class in the map.

**Cross-check against run `p2t26-tilewires`.** For every row-0 tile in the band,
the pips whose fuses differ between the AE350 bitstream and the baseline were
decoded (`chipdb.tile_bitmap` + the tile's pip table), and each mapped bit was
looked up in that tile's changed-wire set:

- `Ae350SocOuts`: **437 of 466 checked bits matched** (93.8 %). Those 437 taps
  are the ones `wire-map-pipdiff-138c.json` lists, and a bit is `MEASURED` in
  the JSON exactly when its tap is one of them. Under the direction repair 415
  of them are input taps and 22 output ones (§7).
- `Ae350SocIns`: 11 of 256. That, read at the time as "an input tap is
  invisible to a pip diff", was the clue that the direction was backwards: it
  is the `F`/`Q`/`OF` half that a pip diff cannot see, and that half is the
  block's **outputs** (§7).

### The presence differential, re-stated on corrected data

`moved.json` used to write `-1` whenever a tile appeared in one bitmap and not
the other, which arithmetic then read as a count and which made every row-0
column of the band look like an unknown. `chipdb.tile_bitmap` omits a tile whose
every bit is zero, so that case is not an unknown at all: the absent side is
all-zero and the moved count is the popcount of the side that is there. The
producer (`$DATASTORE/ae350-analysis/diff.py`) now records the real count and,
separately, which bitmaps the tile was non-zero in, and the artefact was
regenerated from the same two banked bitstreams — 0 vendor runs.

Corrected totals: **1643** tiles carry a moved bit, **92 350** bits in all, and
**166** of those tiles are non-zero on one side only (previously all `-1`).

What the corrected data **does** support:

- every die-row-0 column of the band, **150 to 180**, carries a real moved-bit
  count — 4 at column 150 rising to 302 at column 173 — and every one of those
  tiles is non-zero **only** in the AE350 bitstream. The control has no set bit
  there at all, so every one of those bits is the block's;
- die-row-0 columns **145-149 carry no moved bit**, which is the observation §6
  rests on when it rejects base `0x8314`;
- column **181** is the only row-0 tile of the band present in both bitstreams
  (28 moved bits).

What it **does not** support, and never did: anything per tap. `moved.json`
counts *bits per tile*; it names no wire, no pip and no port. A statement about
which wire a port bit sits on has to come from the pip decode, not from this
file — that is `portmap-reconciled-138c.md` §2.

The flop endpoints of run `p2t26-tilewires` were **not** pinned — `top.cst`
holds four `IO_LOC` lines and nothing else, and `run.p` is encrypted — so a
per-bit measured map is not available from the banked runs. The pip cross-check
above is the strongest evidence those two runs can carry.

## 5. Other tables the same repair unlocks

`MipiIns1/2`, `MipiOuts1/2`, `MipiDPhy*` and every `Gtrl12*` entry are inside a
triple-quoted block at `dat_parser.py:525-546` — **they are not executed at all**
on any device, so they were never "reading noise"; they are dead source. They
are repaired in place for whoever un-quotes them.

Live and repaired, but **not** validated by any measurement here:

| table | slots | live on 138C |
|---|---|---|
| `MDdrDllIns1`-`7`, `S0DdrDllIns1`-`4`, `S1DdrDllIns1`-`4` | 4 each | 4 each |
| `MDdrDllOuts1`-`7`, `S0DdrDllOuts1`-`4`, `S1DdrDllOuts1`-`4` | 9 each | 9 each |
| `CmseraIns` / `CmseraOuts` | 32 / 96 | 32 / 96 |
| `AdcLRCIns` / `AdcLRCOuts` | 40 / 18 | 40 / 18 |
| `AdcULCOuts` | 18 | 18 |
| `AdcLRCCfgvsenctl1`/`2`, `AdcULCCfgvsenctl` | 3 / 36 / 3 | all |

Their decoded records are **not** grid coordinates on this device (columns run
to 17920), so their bases carry the same kind of drift the `Ins` base did and
each needs its own anchor before Phase 3 or 5b can use it. No consumer reads
any of them today (`chipdb.py` references none), so nothing regresses.

WIRE-MAP-VERDICT: 884/911 port bits carry a (row, col, wire); 881 of those sit in the measured footprint and the other three are named; 437 taps cross-checked MEASURED against the run-1 bitstream, of which 415 are the block's inputs — every input bit bound, 27 output bits unbound.

## 6. `P2.T08b` — where the input tail really is

`P2.T08a` left input bits 274-415 unmapped: read at `0x8314` the table runs out
of the AE350 after 256 records and the ordinal rule walks into a neighbouring
block's, in columns 109-115. Two measurements say `0x8314` was never the
AE350's input table either:

- run `p2t26-tilewires` drives **all 410 fabric-driven input bits from their own
  flops** and its post-PnR netlist keeps all 149 ports, so the block has at
  least 410 taps. 256 is not enough for the design the vendor itself routes.
- of the eleven columns `0x8314` names, **145-149 show no changed bit at all**
  in die row 0 of that run (`moved.json` row 0 covers columns 150-181). A tap
  the design drives cannot sit in a tile the bitstream does not touch.

Sweeping every base in the 5-series table block for a 433-slot window whose live
records are *all* row-0 tap wires (`F`/`Q`/`OF` — what a tile drives, and so the
only thing a block input can read) inside the band `Ae350SocOuts` drives finds
**exactly one** region, at `0x91ea`: 415 live records, every one of them a
distinct tap, in die row 0 columns **159-180**. Every one of those columns is in
the run's row-0 changed set.

So the earlier "inputs read the left of the band, outputs drive the right" is
wrong. **The block reads and drives the same tiles**, over disjoint wire
classes: it taps `F`/`Q`/`OF` and drives `A`-`D`, `CLK`, `CE`, `LSR` in columns
159-180. That is also the only reading with room for the port count — eleven
columns hold 264 taps, against 416 input bits; twenty-two hold 528.

The window can slide within the run without breaking any of those properties,
which would rotate every bit's wire. The block's own layout fixes the phase: the
table walks the band one whole column at a time, so the true base is the one
whose first record opens a column. `0x91ea` is the only candidate that does
(`col 166`, wire `Q0`, a full 24-tap column); every other scores a fragment.

| | before (`0x8314`) | after (`0x91ea`) |
|---|---|---|
| input bits with a record in the AE350's own band | 256 | **398** |
| of the 142 bits `P2.T08a` could not map | 0 | **139** |
| input records in another block's columns | 142 | **0** |

**What still resists.** Three of the 142 land on a sentinel slot and stay
unmapped: `DDR_HRDATA[12]` (bit 276), `GPIO_IN[25]` (bit 376) and `EMA[1]`
(bit 409). They are part of a wider residual: 18 sentinels fall inside the bit
range and 17 live records sit past the last input bit. Single scattered holes in
the middle of `ROM_HRDATA`, `EXTS_HRDATA` and `GP_INT` are not plausible as
genuinely untapped bits, so the phase inside the band is provisional even though
the direction, the row and the band are not. The likeliest explanation is that
the vendor splits this port map across numbered tables the way it splits
`MDdrDllIns1`-`7`; a per-bit trace of the run-1 bitstream would settle it. No
vendor run was spent: this is a `.dat` result.

WIRE-MAP-T08B-VERDICT: table tail sourced from the `.dat`, not from a campaign;
`Ae350SocIns` relocated to base 0x91ea (row 0, columns 159-180) and located by
geometry rather than addressed; the relocation stands, its direction does not —
that run is the middle of the **output** map (§7), and read that way its 18
sentinel slots leave 18 output bits unbound and its 17 slots past bit 415 are
ordinary output bits, closing the residual this verdict left open; band
MEASURED against run `p2t26-tilewires`; 0 vendor runs.

## 7. The direction repair — a tap's direction is the wire's, not the table's

Die row 0 is a row of routing tiles with **no bels**: tile type 242 has 125 pips
and zero LUT/DFF sites. A tap there is an ordinary local wire, so its direction
is fixed by the routing graph and not by which table the record came out of:

- `F`, `Q` and `OF` end no pip, so nothing in the fabric can drive them and only
  the block can — they are the block's **outputs**;
- `A`-`D`, `CE`, `CLK` and `LSR` are pip *destinations* and dead ends unless
  something reads them — they are the block's **inputs**.

Measured on the vendor bitstream of the 149-port vehicle against its own
no-block baseline: 415 of the 416 fabric-driven wires carry a pip the vendor
set, 418 pips are sourced from `F`/`Q`/`OF`, and the `CE`, `LSR` and `CLK` tap
counts are exactly the block's 13 clock-enable, 2 reset and 6 clock inputs.
Bound the other way round, every input pin was an unreachable sink and the open
router stopped; bound this way the flow routes the vehicle and packs a
bitstream.

So neither `.dat` table is one direction. `Ae350SocOuts` holds the whole input
map in one run — slots 44 to 477 — with the head and tail of the output map
either side of it; `Ae350SocIns` holds the output map's middle run. The run
bounds are derived from the wire classes, not written down. Within the head the
slot order and the port order disagree, so the class decides there: an `LSR` tap
can only be a reset input and a `CLK` tap only a clock input.

| | bits | bound | MEASURED | DAT-DERIVED | unbound | outside the band |
|---|---|---|---|---|---|---|
| inputs | 416 | 416 | 415 | 1 | 0 | 1 |
| outputs | 495 | 468 | 22 | 446 | 27 | 2 |
| total | 911 | **884** | 437 | 447 | 27 | 3 |

The three taps outside the band are the clock-spine alternative for `CORE_CLK`
at `(0, 87)/CLK1` — a fabric route the vendor never takes, preferring the
dedicated PLL path — and two `ROM_HADDR` output taps at `(0, 22)/F7` and
`(0, 23)/OF3`. They are as bound as any other bit; the map names them rather
than filtering them away.

The 27 unbound bits are all outputs, and all of them are sentinel records: 18
`Ae350SocIns` slots inside the middle run, 8 `Ae350SocOuts` slots in the head
and tail, and one bit (`SCAN_OUT[3]`) past the end of `Ae350SocIns` inside the
run. They get an `AE350_UNMAPPED_*` placeholder wire that exists in no wire
table, so a design that drives one fails by name instead of routing somewhere
plausible.

**Reproducing this file.** `tools/derive_ae350_wire_map.py` regenerates
`wire-map-138c.json` from the `.dat` tables, the port inventory and
`wire-map-pipdiff-138c.json`; `--check` fails if the committed artefact has
drifted from the tables. It imports no part of `apycula.chipdb`, so the
reconciliation test compares two independent readings rather than one reading
with itself.
