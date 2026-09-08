# The on-die ADC of the GW5AST-138C (`P3.T28`-`P3.T29`, `P3.T28a`-`P3.T28b`, `P3.T39`)

## Verdict: **`E0`, row closed** — both blocks anchored and built, the one fuse-backed parameter attributed and emitted, every other one refused by name

12 vendor runs in total. Four adjudication/localisation runs (`P3.T28`/`P3.T29`),
zero for the anchoring (`P3.T28a`/`P3.T28b`), eight for the fuse sweep (`P3.T39`,
the whole of the cap `D111` authorised).

| run | primitive | sweep | vendor | resource report |
|---|---|---|---|---|
| `0000` | `ADCLRC` | `VSENCTL=1` (on-die thermometer) | accepted | `ADCLRC 1/1 100%` |
| `0001` | `ADCLRC` | `VSENCTL=2` (`vdd09_0`) | accepted | `ADCLRC 1/1 100%` |
| `0002` | `ADCLRC` | `DIV_CTL=2` | accepted | `ADCLRC 1/1 100%` |
| `0003` | `ADCULC` | `VSENCTL=1` | accepted | `ADCULC 1/1 100%` |
| `0004`-`0009` | `ADCLRC` | `VSENCTL` 0, 3, 4, 5, 6, 7 | accepted | `ADCLRC 1/1 100%` |
| `0010`-`0011` | `ADCLRC` | `DIV_CTL` 1, 3 | accepted | `ADCLRC 1/1 100%` |

So the die has **two** ADC blocks, one of each kind, one site each -- not the 25A's
single `ADC`. The primitives are `ADCLRC` and `ADCULC`
(`$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:17539`, `:17592`; the vendor's own comment on
the second reads `//ADCULC,GW5AT-138K`). The vendor brings out dedicated analog pads
the pin report names: `N9/ADCTN`, `N10/ADCTP`, `M9/ADCVN`, `L10/ADCVP`, plus
`ADCINCK0` on `B1` (`IOL2[A]`) and `ADCINCK1` on `G17` (`IOR107[A]`).

**Shape caveat.** `adc_osc.py` XOR-reduces `ADCVALUE[13:10]` onto one ball, because
bank 5 brings out eleven free balls and not fifteen, and it claims **no analog ball
at all** -- the sweep uses the internal sources `VSENCTL` selects, so the board's IO
envelope is untouched.

**Superseded stages, kept in git and not restated here.** `P3.T28` did not create the
bels because `AdcLRC*`/`AdcULC*` read zeros and ASCII at their declared bases (base
drift, as `Ae350SocIns` had); its candidate bases `0xa2044`/`0xa1bca` are **refuted**.
`P3.T28a` confirmed a region but not a phase, and had the direction backwards -- it
searched for the block's inputs among `F`/`Q`/`OF`; the chipdb already settled the
roles (`BSRAM` reads `AD0`-`AD13` off `C0`-`C7` and drives `DO*` onto `F0`-`F5`/
`Q0`-`Q5`), so a hard block reads `A`-`D`/`CLK`/`CE`/`LSR` and drives `F`/`Q`/`OF`.
## Where the blocks are — MEASURED, at zero extra vendor runs

The bitstreams differ only in the ADC's own parameters, so a pairwise diff
localises the block without a control run: `VSENCTL` 1 -> 2 moves `(108,180)`
8 bits and `(108,167)` 4; `DIV_CTL` 0 -> 2 moves `(108,181)` 4; `ADCLRC` ->
`ADCULC` moves 304 tiles, largest `(108,179)`, `(1,1)`, `(108,180)`. So
`ADCLRC`'s configuration is in the **lower-right** corner, tiles `(108,180)`
and `(108,181)` (`dev.rows-1 = 108`, `dev.cols-1 = 181`), and `ADCULC`'s in
the **upper-left**, around `(1,1)`. The two names are literal.

## `P3.T28b` — both halves anchored, at **zero** vendor runs

**What locates the tables, and what fixes the phase.** The blocks' port counts are the fingerprint, and they are specific:

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
* the output table's unbound slot at index 1 is the same gap the 25A's
  `_adc_outputs` leaves there, and the two tables sit `0x28` records apart
  exactly as the declared bases do.

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

**The vendor's own bitstreams confirm it, with a control.** `tools/anchor_adc_tables_138c.py` asks, of each located output table: how many
of the fourteen `ADCVALUE` wires does the vendor's routing actually drive in
the cell the table names?

| block / cell | `0000` LRC | `0001` LRC | `0002` LRC | `0003` **ULC** |
|---|---|---|---|---|
| `ADCLRC`, tile (108,168) | **14/14** | **14/14** | **14/14** | 6/14 |
| `ADCULC`, tile (108,165) | 6/14 | 6/14 | 6/14 | **14/14** |

Each table reads 14 of 14 in exactly the runs that instantiate its own block,
and background elsewhere. The input side is confirmed the same way by the
`P3.T29` diffs: in the `ADCLRC` runs tile (108,180) carries pips into
`A0`/`A1`/`A2`/`B3` (`VSENCTL[2:0]` and `ADCEN`) and (108,179) carries
`CLK0<-GB10`; in the `ADCULC` run tiles (0,3), (0,5) and (0,6) carry `CLK2`,
`CE2` and `LSR2` — that block's `CLK`, `ADCEN` and `VSENCTL[2:1]`.

**What was built.** `Datfile.locate_adc_tables` locates both pairs and names every port.
`chipdb.fse_create_adc` gains a 138C branch: bels `ADCLRC` at (108,181) and
`ADCULC` at (0,0), 29 inputs and 17 outputs each, with a Himbaechel node for
every tap outside the bel's own cell. `nextpnr` gains 46 constids and
`type_is_adc` learns the two names. Two guards came out of building it:
`_adc_site_is_unique`, because a bel put on a *shared* tile type appears at
every cell of that type (the first `ADCULC` site gave **16 200** of them and
nothing said so), and `fse_adc_join_nodes`, run last in `chipdb_builder`,
because a Himbaechel wire may belong to one node only while this die's two ADCs
share a tap outright — both `DRSTN` ports read `C1` of the same cell.

**Result, at zero vendor runs**: `nextpnr` reports the vendor's own
`ADCLRC: 1/1 100%` / `ADCULC: 0/1` on the `ADCLRC` designs, places the block
and routes all 52 arcs to completion.

## `P3.T39` — the fuse sweep, and what it found the parameters to be

Eight vendor runs, the cap `D111` authorised and the whole of it: the six
`VSENCTL` values and the two `DIV_CTL` values the four earlier points had not
built. Completing both axes is the point, not thoroughness for its own sake —
a shortval entry is `code -> bits`, so a code is identified by the bits it
moves and a parameter is decoded only once every one of its values exists.

### `VSENCTL` is not a fuse, which is why no fuse table was ever going to be found
Diffing each `VSENCTL` point against the baseline and asking, of every moved
bit, **which structure of the chipdb claims it** — a pip, a shortval entry, or
nothing — gives the same answer at every one of the eight points:

| point | tile | bits moved | claimed by routing | claimed by a table | unattributed |
|---|---|---|---|---|---|
| `vsen0` | (108,167) / (108,180) | 6 / 8 | 6 / 8 | 0 | **0** |
| `vdd09` (=2) | (108,167) / (108,180) | 4 / 8 | 4 / 8 | 0 | **0** |
| `vsen3` | (108,167) / (108,180) | 2 / 4 | 2 / 4 | 0 | **0** |
| `vsen4` | (108,167) / (108,180) / (108,181) | 14 / 40 / 4 | 14 / 40 / 4 | 0 | **0** |
| `vsen5` | (108,167) / (108,180) / (108,181) | 12 / 26 / 4 | 12 / 26 / 4 | 0 | **0** |
| `vsen6` | (108,167) / (108,180) / (108,181) | 16 / 28 / 4 | 16 / 28 / 4 | 0 | **0** |
| `vsen7` | (108,167) / (108,180) / (108,181) | 22 / 44 / 4 | 22 / 44 / 4 | 0 | **0** |

Every bit is a pip into the block's own `A0`/`A1`/`A2`/`B3`/`B4` wires.
`VSENCTL` is a **port**, not a parameter — as are `ADCEN`, `CLK`, `DRSTN`,
`ADCREQI`, and the ten `FSCAL_VALUE` and twelve `OFFSET_VALUE` bits the
`0x28`-slot input table lays out. The vendor drives them with fabric
constants, and the open flow already routes them: nothing here needs a fuse,
which is the reason this die's `.fse` declares no `ADC` `logicinfo`/`shortval`
pair at all. `P3.T28b` recorded the absence of that table as the gap; the
sweep says the absence is the *answer*.

### `DIV_CTL` is a fuse, and its complete axis names it
| value | bits moved in (108,181) | table entries that reproduce them |
|---|---|---|
| 0 | none | — (a default measurably costs no fuse) |
| 1 | `(20,32)`, `(20,63)` | `unknown_137 (57,0)` + `unknown_138 (57,0)` |
| 2 | `(20,31)`, `(20,32)`, `(20,62)`, `(20,63)` | `unknown_137 (58,0)` + `unknown_138 (58,0)` |
| 3 | `(20,31)`, `(20,62)` | `unknown_137 (59,0)` + `unknown_138 (59,0)` |

Two tables, written together on every `ADCLRC` run, carrying the same three
codes 57/58/59 at two column pairs. `DIV_CTL=1`'s fuses are a proper subset of
`DIV_CTL=2`'s, so both the attribution tool and the unpacker match on the
**exact** set and never on a subset — a subset match would decode a `/4` clock
divider as `/2` with nothing to say so.

### What was built, and what stays refused
* `chipdb._adc_config_fuses` reads the two tables **by code**, so the
  attribution follows a device-file revision that moves the bits rather than
  pinning their coordinates; it is attached to the `ADCLRC` site only, because
  the upper-left corner's tables carry none of those codes and no run measured
  it.
* `gowin_pack.GW5AST_138C._adc_fuses` emits `DIV_CTL` and refuses **by name**
  every one of the block's other sixteen parameters, and any `DIV_CTL` outside
  the measured axis. A guess at a configuration fuse is a wrong bitstream with
  no error (`D30`).
* `gowin_unpack._adc_modes_from_config` decodes it back, so the row's `c1`
  check has something to recover — except when the block is left at every
  default, which spends no fuse at all and which `equiv` therefore skips **by
  name**, exactly as it already did for an `IOLOGIC` empty half.

### The row
**All 12 points `verdict: ok`, `E0`, `cells`/`attrs`/`conns` 0/0/0,
`fuses_moved` empty, `unexplained_bits` empty, `c1`/`c2` ok.**

`E1` is unreachable for a stated reason (`EC9`) and not for want of effort: an
ADC design holds no `CLS` cell, so the open flow exports no placement
constraint for `E1` to assert, and the block's site is fixed by the die in both
flows anyway.

Named, not absorbed:

* **`ADCULC`'s parameters are unattributed.** Its corner's `unknown_136` holds
  none of the measured codes and the one `ADCULC` run built at every default.
  A default `ADCULC` packs; setting any parameter on one is refused by name.
  One `ADCULC` run at `DIV_CTL=2` would settle it.
* **The other sixteen `ADCLRC` parameters are unattributed** —
  `SAMPLE_CNT_SEL`, `RATE_CHANGE_CTRL`, `ADC_MODE`, `VSEN_CTL`, the seven
  `BUF_*_EN` sets, `CLK_SEL`, `PIOCLK_SEL`, `VSEN_CTL_SEL`, `DYN_BKEN`. Each
  is one complete axis away, and each is refused by name until then.
* **A latent unpacker defect this work exposed and fixed**: `gowin_unpack`
  read `db.logicinfo['ADC']` for any bel whose name starts with `ADC`, so once
  this die had ADC bels every tile walk that reached a corner died with a bare
  `KeyError: 'ADC'` — which took the batch head's three self-tests with it and
  blocked every batch on this device. The decode is now skipped where there is
  no table, which is what the bitstream says.
