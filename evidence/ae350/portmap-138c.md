# `P2.T07`/`P2.T08` — `fse_create_ae350()`: the bel and its fabric port map

apicula branch `ae350/create-138c`. No vendor run: the map is read from the
device data, cross-checked against `wire-map-138c.json` (`P2.T08a`).

> **Superseded.** Three of this row's premises were later refuted by
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
