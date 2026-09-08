# The on-die ADC of the GW5AST-138C (`P3.T28`, `P3.T29`)

## Verdict (`P3.T28b`): **both blocks anchored; both bels built; the open flow now places and routes an ADC and refuses only to configure it.**

`refused:ADCLRC cannot be configured on GW5AST-138C: its port map is anchored
and its bel exists, but the .fse carries no ADC fuse table for this die`

The sections up to `P3.T28a` are the record of how the anchor was reached;
`P3.T28b` at the end supersedes their conclusions, and in one case
(`P3.T28a`'s direction rule) corrects them.

Four vendor runs, all `gw_sh` exit 0 with **zero** errors and a full `run.fs`:

| run | primitive | sweep | vendor | resource report |
|---|---|---|---|---|
| `p3-adc-adc_osc-0000` | `ADCLRC` | `VSENCTL=1` (on-die thermometer) | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0001` | `ADCLRC` | `VSENCTL=2` (`vdd09_0`) | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0002` | `ADCLRC` | `DIV_CTL=2` | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0003` | `ADCULC` | `VSENCTL=1` | accepted | `ADCULC 1/1 100%` |

So the die has **two** ADC blocks, one of each kind, one site each — not the
25A's single `ADC`. The primitives are `ADCLRC` and `ADCULC`
(`$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:17539`, `:17592`; the vendor's own
comment on the second reads `//ADCULC,GW5AT-138K`). The vendor also brings out
dedicated analog pads for them, which the pin report names:
`N9/ADCTN`, `N10/ADCTP`, `M9/ADCVN`, `L10/ADCVP`, plus `ADCINCK0` on `B1`
(`IOL2[A]`) and `ADCINCK1` on `G17` (`IOR107[A]`).

## Where the blocks are — MEASURED, at zero extra vendor runs

The four bitstreams differ only in the ADC's own parameters, so a pairwise
diff localises the block without a control run:

| pair | what changed | tiles that move |
|---|---|---|
| `0000` vs `0001` | `VSENCTL` 1 → 2 | `(108,180)` 8 bits, `(108,167)` 4 bits |
| `0000` vs `0002` | `DIV_CTL` 0 → 2 | `(108,181)` 4 bits |
| `0000` vs `0003` | `ADCLRC` → `ADCULC` | 304 tiles, largest `(108,179)`, `(1,1)`, `(108,180)` |

`ADCLRC`'s configuration is in the **lower-right** corner, tiles `(108,180)`
and `(108,181)` — `dev.rows-1 = 108`, `dev.cols-1 = 181` — and `ADCULC`'s in
the **upper-left**, around `(1,1)`. The two names are literal.

## Why `P3.T28` did not create the bels

`fse_create_adc` builds its portmap from `dat.gw5aStuff['Adc25kIns'/'Adc25kOuts']`,
which are 25A tables. The 138C's own tables are `AdcLRCIns` (0x28 records),
`AdcLRCOuts` (0x12), `AdcULCOuts` (0x12) and the two `Cfgvsenctl` tables —
`P2.T08a` unlocked them, but **at their declared bases they read zeros and
ASCII bytes**, i.e. the base has drifted between IDE releases exactly as
`Ae350SocIns`' and `CibFabricNode`'s did. A bel whose portmap comes from a
mis-based table is worse than no bel: `nextpnr` binds it and then fails in the
router on a wire that was never the port's (`D30`). So the bels are **not**
created, both open tools refuse by name, and what this task hands the
follow-up is the anchor work already done:

* the record *shapes* are confirmed by the primitive's own port count —
  `ADCLRC` has 37 input ports (8 analog `ADCINBK*` + `VSENCTL[2:0]` +
  `FSCAL_VALUE[9:0]` + `OFFSET_VALUE[11:0]` + `ADCEN`/`CLK`/`DRSTN`/`ADCREQI`)
  against 0x28 = 40 slots, and 15 output ports (`ADCRDY` + `ADCVALUE[13:0]`)
  against 0x12 = 18 slots. Three trailing pad slots in each case;
* filtered by the corners measured above, the `.dat` yields a **small** set of
  surviving bases rather than the hundreds a plain plausibility filter leaves.
  The strongest single candidate for `AdcLRCOuts` is byte `0xa2044`
  (`0x135cc` words from the RS table anchor, against the declared `0x13078`):
  15 live records then 3 absent, walking `(109,168,37..45)`, `(109,167,36..40)`,
  `(109,169,40)` — one column band at a time — and its columns 167/168 are
  **the same tiles the `VSENCTL` bitstream diff moves**, which is an
  independent confirmation the plausibility filter could not give;
* the strongest candidate for `AdcLRCIns` is byte `0xa1bca`: exactly 37 live
  records then 3 absent, all in the block's own columns 180/181;
* `AdcULCOuts` is **not** at the same drift as `AdcLRCOuts`, which is the fact
  that stops this being finished here: two structurally clean candidates
  survive for it (`0x80e24` and `0xa194e`) and nothing measured yet separates
  them. Separating them needs one `ADCULC` bitstream diff against an
  `ADCULC`-free control — one vendor run, outside this task's four.

Until that run, the ADC row is `refused` with the open flow's exact words.

## Shape caveat

`adc_osc.py` XOR-reduces `ADCVALUE[13:10]` onto one ball, because bank 5 brings
out eleven free balls and not fifteen, and it claims **no analog ball at all** —
the sweep uses the internal sources `VSENCTL` selects, so the board's IO
envelope is untouched. The row is an adjudication and a localisation, not an
`E1` identity claim.

## `P3.T28a` — anchored geometrically, and what that settled

`P3.T28a` re-ran the anchoring with the method that anchored the AE350 tables
(`P2.T08a`/`P2.T08b`: locate a table by sweeping the 5-series block for a window
whose live records land in the measured cells) and added a check plausibility
alone cannot make — **each candidate record is held against the vendor's own ADC
bitstreams**: is the wire it names one the vendor's routing actually drives, in
the cell the record names? The tool is
`$OTC/tools/anchor_adc_tables_138c.py`, it spends **no vendor run**, and it
reads the four bitstreams `P3.T29` already bought.

The measured wire sets come from a background subtraction: each ADC-corner tile
is compared against a distant tile of the same type, so only the corner's own
routing survives. Tiles (108, 180) and (108, 181) have types unique to the
corner and therefore no twin; they contribute nothing rather than everything,
which is why the confirmation below rests on (108, 179) and (108, 167).

### What it settled

* **The region is confirmed.** A run of records starting around word `0x1360e`
  (byte `0xa20c8`) holds nothing but pip-destination wires — `A`-`D`, `CLK` —
  in the block's own cells, and **every** one of them that falls in a
  checkable tile is a wire the vendor's ADC routing drives there: 13 of 13 at
  the best-covered phase, and 100 % at every phase in the run. Two of the
  cells are independent of one another — `(109, 181)` = tile (108, 180), whose
  `A0`/`A1` are the wires the `VSENCTL 1 -> 2` diff moves, and `(109, 168)` =
  tile (108, 167), the second tile that diff moves — so this is not one
  coincidence seen twice.
* **The direction is the opposite of the table's name.** These are wires the
  fabric drives and the block reads, i.e. the block's **inputs**, and they are
  in the 0x12-slot table `dat_parser` calls `AdcLRCOuts`. That is the same
  lesson `Ae350SocOuts` taught (`tools/derive_ae350_wire_map.py`: "the
  direction rule is the load-bearing part, and it is not the table names").
  Fifteen live records is also exactly the number of *fabric* inputs `ADCLRC`
  has: of its 37 input ports, `ADCINBK[7:0]` are analog pads and
  `FSCAL_VALUE[9:0]`/`OFFSET_VALUE[11:0]` are static configuration, leaving 15.

### Why there is still no bel

* **The phase is not fixed.** Every window in the run confirms at 100 %,
  because the run is one long region of ADC-cell wires and sliding the window
  by one record still lands inside it. A portmap is an assignment of *slot
  index* to port name, so a window that is right about the region and wrong by
  one record about the phase gives every port the wrong wire — silently. The
  three filters that fixed the AE350's phase (the table walks the band column
  by column, so the true base opens a column) do not fix this one: these
  records do not walk their cells in column order.
* **The output half has no candidate at all.** No 0x28-slot window of `F`/`Q`/
  `OF` wires exists in the block's cells, and the only structurally clean
  output-role windows anywhere near sit at `(109, 167)` = tile (108, 166),
  where the bitstream shows no ADC routing, while the tile the bitstream *does*
  show driving `OF0`-`OF7`/`F0`-`F5` — (108, 168) — appears in no window.
* **`AdcULC*` has no candidate at all** under the same filters, in any of the
  upper-left cells.

So the row stays `refused` with the open flow's exact words, and it stays that
way on a sharper reason than `P3.T28`'s: not "the tables read as zeros" but
"the input table's region is confirmed by the vendor's own routing and its
phase is not, and the output table is not located at all". This also
**supersedes** `P3.T28`'s candidate bases `0xa2044` and `0xa1bca`: neither
survives the wire-role filter.

### The one measurement that would finish it

A phase needs a record whose port is known independently. One vendor `ADCLRC`
run that drives a **single** fabric input -- `ADCEN` alone, everything else
tied off -- moves exactly one wire against the runs already on disk, and that
one wire's position in the confirmed run fixes the phase for all fifteen. It is
one run, and it was not spent here because the same run cannot also locate the
output table, which is the other half of a portmap.


## `P3.T28b` — both halves anchored, at **zero** vendor runs

### The mistake that had blocked it

`P3.T28a` searched for the block's *inputs* among `A`-`D`/`CLK` wires and its
*outputs* among `F`/`Q`/`OF`. That is the direction backwards, and the chipdb
this project already ships settles it without a single run: `BSRAM` reads its
address bus `AD0`-`AD13` off `C0`-`C7` and drives `DO0`-`DO35` onto
`F0`-`F5`/`Q0`-`Q5`; `ALU` reads `I0` off `A0` and drives `SUM` onto `F0`. So a
hard block's **input** is an `A`-`D`/`CLK`/`CE`/`LSR` wire and its **output** an
`F`/`Q`/`OF` wire. With the roles the right way round, "the output half has no
candidate at all" disappears: the output records were there all along, in the
table `P3.T28a` was reading as inputs.

### What locates the tables, and what fixes the phase

The blocks' port counts are the fingerprint, and they are specific:

* the **input** table is `0x28` = 40 slots and `ADCLRC` has exactly 29 fabric
  input bits, which the table lays out in three runs separated by an unbound
  slot — seven controls at slots 9-15, ten `FSCAL_VALUE` at 17-26 and twelve
  `OFFSET_VALUE` at 28-39, with 16 and 27 unbound. **7/10/12** is not a shape a
  wrong window produces;
* slot 13 of that run lands on a `CLK`-class wire in both blocks, which is the
  independent phase check a region match cannot make — and it puts the seven
  controls in the vendor's own declaration order, `VSENCTL[2:0]`, `ADCEN`,
  `CLK`, `DRSTN`, `ADCREQI`;
* the **output** table is `0x12` = 18 slots holding `ADCRDY`, one unbound slot,
  then `ADCVALUE[13:0]` as a single cell's `F0`-`F5`/`OF0`-`OF7` run, then two
  more outputs — 17 live, exactly the port count of the vendor's own
  `ADCLRC_DB`/`ADCULC_DB` (`ADCRDY`, `ADCVALUE[13:0]`, `ADC1BIT`, `ADCCLKO`).
  The plain `ADCLRC` exposes the first fifteen of them;
* the unbound slot at index 1 of the output table is the same gap the 25A's
  `_adc_outputs` list leaves at index 1, and the two tables sit `0x28` records
  apart exactly as the declared bases do.

Those two fingerprints together match at **exactly two** bases in the whole
5-series table block of a 1.9.12.03 `GW5AST-138C.dat`, one per ADC:

| block | `Ins` base (words) | `Outs` base | `CLK` tap | `ADCVALUE` cell |
|---|---|---|---|---|
| `ADCLRC` | `0x135f9` | `0x13671` | `(109,180) CLK0` | `(109,169)` = tile (108,168) |
| `ADCULC` | `0x136a4` | `0x1371c` | `(1,4) CLK2` | `(109,166)` = tile (108,165) |

(`.dat` cells are one-based; the tile grid is the cell minus one.) The declared
bases are `0x13000`/`0x13078` for `AdcLRC*`, so both have drifted by a constant
`+0x5f9` words. `AdcULCIns` is not declared by `dat_parser` at all; the geometry
finds it anyway.

### The vendor's own bitstreams confirm it, with a control

`tools/anchor_adc_tables_138c.py` holds each located output table against the
four ADC bitstreams already on disk: how many of the fourteen `ADCVALUE` wires
does the vendor's routing actually drive in the cell the table names?

| block / cell | `0000` LRC | `0001` LRC | `0002` LRC | `0003` **ULC** |
|---|---|---|---|---|
| `ADCLRC`, tile (108,168) | **14/14** | **14/14** | **14/14** | 6/14 |
| `ADCULC`, tile (108,165) | 6/14 | 6/14 | 6/14 | **14/14** |

Each table reads 14 of 14 in exactly the runs that instantiate its own block,
and background elsewhere. The input side is confirmed the same way by the
`P3.T29` diffs: in the `ADCLRC` runs tile (108,180) carries pips into
`A0`/`A1`/`A2`/`B3` — `VSENCTL[2:0]` and `ADCEN` — and tile (108,179) carries
`CLK0<-GB10`, the `CLK` port on a global; in the `ADCULC` run tiles (0,3),
(0,5) and (0,6) carry `CLK2`, `CE2` and `LSR2`, which are that block's `CLK`,
`ADCEN` and `VSENCTL[2:1]`.

### What was built

* `Datfile.locate_adc_tables` locates both pairs and names every port;
* `chipdb.fse_create_adc` gains a 138C branch: bels `ADCLRC` at (108,181) and
  `ADCULC` at (0,0), 29 inputs and 17 outputs each, with a Himbaechel node for
  every tap outside the bel's own cell. Two guards came out of building it —
  `_adc_site_is_unique`, because a bel put on a *shared* tile type appears at
  every cell of that type (the first attempt put `ADCULC` at (1,1) and got
  16 200 of them, silently), and `fse_adc_join_nodes`, run last in
  `chipdb_builder`, because a Himbaechel wire may belong to one node only and
  this die's two ADCs share a tap outright: both `DRSTN` ports read `C1` of the
  same cell;
* `nextpnr` gains 46 constids and `type_is_adc` learns the two names.

**Result, at zero vendor runs**: re-running only the open half over the four
bitstreams already on disk, `nextpnr` reports `ADCLRC: 1/1 100%` and
`ADCULC: 0/1` on the `ADCLRC` designs — the vendor's own resource report —
places the block and routes all 52 arcs to completion.

### What is still refused, and the one measurement that closes it

`gowin_pack` refuses to *configure* an ADC. This die's `.fse` carries **no ADC
fuse table at all**: the bits the `VSENCTL 1->2` and `DIV_CTL 0->2` diffs move
sit in the unattributed `unknown_136`, `unknown_137` and `unknown_138`
`shortval` tables of tiles (108,167), (108,180) and (108,181). The block has
sixteen parameters and a guess at any one of them is a wrong bitstream with no
error (`D30`), so the row closes `refused:adc-config-fuses-unattributed`.

The finisher is an attribute sweep, not an anchor: `VSENCTL` over its eight
values and `DIV_CTL` over its four, diffed against the baseline already on
disk, would attribute those three tables. That is eight vendor runs; `D111`
authorised eight for this task and none of them were needed for the anchoring,
so none were spent.
