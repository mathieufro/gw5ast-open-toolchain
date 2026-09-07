# `P2.T07`/`P2.T08` — `fse_create_ae350()`: the bel and its fabric port map

apicula branch `ae350/create-138c`. No vendor run: the map is read from the
device data, cross-checked against `wire-map-138c.json` (`P2.T08a`).

> **Superseded; the map of record is `portmap-reconciled-138c.md`.** Three
> of this row's premises were later refuted by
> measurement: the bel is at `(0, 159)`, not `(0, 145)` (`e0-138c.md` §1); the
> band filter is gone, so a live record binds wherever it lands; and a tap's
> direction is its wire's, not its table's (`route-138c.md` §1-3,
> `wire-map-138c.md` §7). The current map binds **884 of 911** bits. The
> numbers below are `P2.T07`'s and are kept as the record of what was believed
> then — including the cross-check against the version of
> `wire-map-138c.json` that stood at the time.

## The bel

| | |
|---|---|
| tile | die `(0, 145)`, `ttyp` **242** |
| why | Every live record in both tables names die row 0, and the block's band is contiguous and disjoint — it reads columns 145-155 and drives 156-180 (`wire-map-138c.md` §3). `(0, 145)` is the row-0 tile at the **first tapped column**: inside the block's own footprint, and a cell whose wires it really reads. The EMCU's `(0, 0)` rests on a GW1NS-4 CPU-enable flag with no counterpart here, so it is not inherited (`P2.T07` HOW allowed either; this is the measured choice). |
| configuration tiles | the 216 cells of `ttyp` **224** (rows 10, 28, 46) and **228** (rows 64, 82, 100), columns 145-180 — where the presence diff's bits move. Each is marked `extra_func['ae350_config']`; none carries a port. |

## The port map

Source: `dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts']`, read by `P2.T08a`'s
`read_packed_grid16`. Slot *i* of a direction's table is bit *i* of that
direction, counting `primitive.xml`'s 149 ports in declaration order with each
bus LSB first. A record is bound only when it is live **and** names a column in
that direction's half of the band.

| | bits | bound | placeholder |
|---|---|---|---|
| inputs (`AE350_IN`, clocks `TILE_CLK`) | 416 | **256** | 160 |
| outputs (`AE350_OUT`) | 495 | **466** | 29 |
| total | 911 | **722** | **189** |

Ports: **98 of 149** fully bound, 13 partly, 38 not at all.
Placeholder reasons: 145 `outside-footprint`, 44 `unbound` (an all-`0xffff`
record). The six clock inputs — `CORE_CLK`, `DDR_CLK`, `AHB_CLK`, `APB_CLK`,
`RTC_CLK`, `DBG_TCK` — are all bound and all typed `TILE_CLK`.

**Cross-check**: every one of the 911 bits agrees with `wire-map-138c.json`
bit for bit — 0 mismatches, in both directions, including which bits are
placeholders.

## The unmapped bits

The input table holds 257 records against 416 input bits, so the ordinal rule
runs off its end and the remaining slots name columns 50, 51, 101 and 109-114,
which belong to the neighbouring block. Those bits, plus the all-sentinel
records of both directions, get a wire named `AE350_UNMAPPED_<PORT>` and an
entry in `extra_func['ae350']['unmapped']` giving the reason. The name is in no
wire table, so nextpnr can neither route it nor alias it to a real wire: a
design that drives such a port fails **naming the port**, rather than being
routed somewhere plausible and wrong. Closing this class is `P2.T08b`.

## Guard — `S3` / §7.4

Built on `ae350/create-138c`, IDE Standard 1.9.12.03, and compared against a
control build of the same device at the `epic/gw5ast138c` tip:

| device | branch | control / recorded | verdict |
|---|---|---|---|
| GW5A-25A | `60f1ba427f96…` 321512 | `60f1ba42…` (`P1.T38` second pass) | **identical** |
| GW5AT-60B | `615d4d0349ba…` 322028 | `615d4d03…` (`P0.T40`) | **identical** |
| GW1N-9C (pre-GW5) | `6d07813c0811…` 191840 | `6d07813c…` control build, epic tip | **identical** |
| GW5AST-138C | `b2df200a0412…` 833336 | `100ffd8e…` 821444 (installed) | **differs, as intended** |

`GW1N-9C`'s recorded `P0.T15b` sha `54cc6fa4…` is stale — it predates the
`P0.T35`/`P0.T40` `tm_parser` de-aliasing — so the control build above is the
baseline, not that line.

### The 138C delta, key by key

Purely additive; nothing removed, nothing modified.

| structure | delta |
|---|---|
| `extra_func` | +217 tiles: `ae350` x1 at `(0, 145)`, `ae350_config` x216 |
| `nodes` | +698 Himbaechel nodes, all `X145Y0/AE350_SOC*` aliases for ports outside the anchor cell |
| every other top-level field | unchanged |

Artefacts: `$DATASTORE/chipdb/p2t07/` (branch) and
`$DATASTORE/chipdb/p2t07-control/` (epic tip).
Batch log: `evidence/_runs/p2t07-chipdb.log`,
`BATCH_COMPLETE p2t07-chipdb runs=2 ok=2 diff=0 aborted=0`.

## Tests

`apicula/tests/test_ae350.py`, 8 passed:
`test_fse_create_ae350_is_noop_for_gw5a_25a`,
`test_fse_create_ae350_registers_extra_func_for_138c`,
`test_from_fse_calls_ae350_exactly_once`,
`test_ae350_portmap_covers_every_port_bit_of_the_primitive`,
`test_ae350_clock_ports_are_tile_clk`,
`test_ae350_no_port_maps_to_negative_coordinate`,
`test_ae350_unmapped_bits_get_unroutable_placeholder_wires`,
`test_ae350_config_tiles_are_marked_as_the_blocks_own`.

## Band, stated once (gestalt-p2 `C2`, 2026-09-07)

The block's "band" has been stated four incompatible ways across this tree
(`chipdb.py` `_AE350_SOC_ANCHOR (0,159)` / `_AE350_SOC_BAND_COLS 159-181`;
`dat_parser.py` docstrings saying "160-181"; commit `654f5b4`'s message
saying "156-180"; `tests/test_dat_packed_grid16.py`'s `FOOTPRINT_COLS =
range(145,182)`; `AE350_SOC_CONFIG_FUSES` keyed at `x=145` and `156-160`).
They disagree because they are measuring three different things, not because
any of them is wrong. **Stated once, so the rest cite this:**

* **Bel anchor**: `(0, 159)` — the die tile `fse_create_ae350()` places the
  bel at. One coordinate, not a range.
* **Port columns**: die row 0, columns **145-181** — where the block's fabric
  ports (`Ae350SocIns`/`Ae350SocOuts`) actually land, measured as the columns
  holding 99.99% of the bits that move between a bitstream instantiating the
  block and one that does not (`wire-map-138c.md`). `test_dat_packed_grid16.py`'s
  `FOOTPRINT_COLS` and `AE350_SOC_CONFIG_FUSES`'s `x=145`/`156-160` keys are
  both inside this span; they are not a second, disagreeing band, they are
  points within this one.
* **Clock-spine taps**: columns 22, 23, 87 also carry AE350 clock-related
  wires (e.g. the `(0,87,CLK1)` fabric tap `core-clock.md` and `B1` discuss) —
  outside the 145-181 port-column span, reached over the die's ordinary
  clock spine rather than the block's own dense column band. These are cited
  separately, never folded into "the band".
* **Tile types 224/228 are not a configuration band at all.** They are
  ordinary CLS logic tiles, at rows 10/28/46/64/82/100, columns 145-180 —
  the tiles where the presence-marking config bits `config-fuses-138c.md`
  records happen to live, because the vendor's synthesis places incidental
  logic for the block's interface there. Calling them "the config band" (as
  earlier phase prose does) overstates them into a distinct structural
  region; they are fabric like any other CLS tile, just ones this design's
  place-and-route happened to use.

`chipdb.py`'s `_AE350_SOC_ANCHOR`/`_AE350_SOC_BAND_COLS` naming is unchanged
here (off-limits to this pass — owned by another agent mid-edit); the
constant-level correction it should carry is one sentence: **rename
`_AE350_SOC_BAND_COLS` to document that it is the *port-column* span
(145-181, matching `FOOTPRINT_COLS`), not the bel anchor's own coordinate,
and drop the current `159-181` value in favour of the measured `145-181`
unless a citation shows the narrower range is deliberate.**
