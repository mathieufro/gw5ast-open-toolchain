# DCS on the GW5AST-138C, open flow — the input side, closed

`P1.F2`, closing the gap `evidence/dcs/openflow-gap-138c.md` named: the DCS
**output** side routed, and the router then stopped one hop short of the clock
source because the DCS **input** multiplexers `P{26,27,36,37}{A..D}` are fed
only by the bridge cells' bare `*MDCLK*` / `*BDCLK*` / `PCLK*` wires, and
nothing in the 138C database drove any of them.

## 1. What was actually missing — one hardcoded gate

`chipdb.get_logic_clock_ins` returns, per half of the clock plane, the 24
logic-to-clock gates the `.dat` `CMuxTopIns` / `CMuxBotIns` tables describe.
For the 138C it returned a literal instead:

```python
return [{}, {(160, 108, 91, 125)}]  # XXX for now only one gate: BRMDCLK1
```

so the whole die carried exactly **one** gate node — `BRMDCLK1_BOT` — and the
top half none at all. The tables were there all along: 24 entries per half,
`(row, col, wire)` 1-based, `wire` always `CLK1` or `CLK2`. The MDCLK gates
sit in the central columns 90/91 at rows 9, 27, 45, 54 (top half) and 63, 81,
99, 108 (bottom); the BDCLK gates on the edge columns 0/181.

Second, subtler half of the same hole: the **central** clock multiplexer (fse
table 38, the one that feeds the DCS clock inputs) names a gate *bare*
(`BLMDCLK1`), while the two half backbones (fse tables 90 and 91) name the
same gate with a half suffix (`BLMDCLK1_TOP` / `_BOT`). The bare wire was in
no node, so even with both halves built the DCS input would still have had no
driver.

## 2. Which half the bare name is — MEASURED, not assumed

A gate name denotes two different wires, one per half. Five vendor bitstreams
decide which one the central multiplexer means. In each, the bare source the
DCS input multiplexer selects is listed with the gate cells whose `CLK1` the
vendor actually drives.

| run | CLKIN source | DCS input pip | gate cells driven | resolves to |
|---|---|---|---|---|
| `p1t31-dcs-e1b-…-0000` (baseline) | pin `V22` | `(54,93) P26A-D <- BLMDCLK1` | `(108,90) CLK1 <- GB10`; `(54,90)` **no bits** | `_BOT` |
| `p1f2-dcsin/a-fabric` | fabric-divided net | `(54,93) P26A-D <- BLMDCLK1` | `(108,90) CLK1 <- GB30`; `(54,90)` **no bits** | `_BOT` |
| `p1f2-dcsin/b-two-dcs` | pin + fabric net, 2 DCS | `(54,93) P26A-D <- BLMDCLK1` | `(108,90) CLK1 <- GB10`, `(54,90) CLK1 <- GB30` | `_BOT` (the `_TOP` tap is consumed by a spine pip) |
| `p1f2-dcsin/c-four-dcs` | 4 distinct clocks, 4 DCS | `(54,93) P26A-D <- BLMDCLK1`, `(54,88) P36A-D <- TLMDCLK1`, `(54,88) P37A-D <- TRMDCLK1` | `(81,90)`, `(81,91)`, `(108,90)`, `(108,91)` driven; `TRMDCLK1_TOP (27,91)` **not driven** | `_BOT` |
| `p1f2-dcsin/d-pll` | `PLL.CLKOUT0` | `(54,93) P26A-D <- BLMDCLK1` | `(108,90) CLK1 <- X01`; `(54,90)` **no bits** | `_BOT` |

Run `c` is the decisive one: it programs three different bare gate names at
once and every `_TOP` twin is either not driven at all or already consumed by
a half-backbone spine pip (`(54,93) SPINE8 <- TLMDCLK1_TOP`,
`SPINE13 <- BRMDCLK1_TOP`, `(54,88) SPINE16 <- BRMDCLK1_BOT`) — the suffixed
names, which the model already had right.

**Attribution: the bare gate source of the central multiplexer is this die's
`CMuxBotIns` gate**, recorded as `chipdb._central_mux_gate_half` with the
citation, and applied only to bridge cells whose fse tables really list that
gate as a source.

## 3. The change

`apycula/chipdb.py`

* `gw5_logic_clock_gates(dat, table)` — the derivation, one place; the 25A
  keeps `CMuxTopIns` and its result is byte-for-byte what it was.
* `get_logic_clock_ins('GW5AST-138C')` returns **both** halves from the `.dat`;
  the literal is gone. 24 gates per half, 48 nodes instead of 1.
* `central_mux_gate_cells` + `fse_create_logic2clk` alias the bare bridge wire
  onto the measured half's node, so `P26A <- BLMDCLK1` now has a driver at
  `(108, 90) CLK1`.

`nextpnr` needed **no** source change: with the nodes present the global
router walks back through the gate on its own. What it gained is a gate check
(`himbaechel/uarch/gowin/tests/check_dcs_spines.py::test_dcs_clock_inputs_are_reachable`)
that fails on the pre-fix database — 16 of 16 DCS input multiplexers had no
source with a driver — and passes on this one.

## 4. Verdict lines

`p1f2-dcs-e0b`, three points, all against chipdb `d700cade…`:

```
BATCH_COMPLETE p1f2-dcs-e0b runs=3 ok=3 diff=0 aborted=0
```

`q1` — the `P1.T31` design, one `DCS`, four `CLKIN` on the board clock:

```
EQUIV E0 ok
DIFF_COUNT cells=0 attrs=0 conns=0
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=ok c2=ok (c1 recovered 23/23 placed cells, 9 not fuse-backed; c2 0 differing bytes of 4147478)
```

`q2` — the same design at the second bridge cell:

```
EQUIV E0 ok
DIFF_COUNT cells=0 attrs=0 conns=0
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=ok c2=ok (c1 recovered 23/23 placed cells, 9 not fuse-backed; c2 0 differing bytes of 4147478)
```

`sel4` — the DCS-with-selection variant, four different clocks on the four
`CLKIN`, dynamic `CLKSEL` and `SELFORCE`:

```
EQUIV E0 ok
DIFF_COUNT cells=0 attrs=0 conns=0
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=ok c2=ok (c1 recovered 29/29 placed cells, 9 not fuse-backed; c2 0 differing bytes of 4147478)
```

`E1` is not reached: `clocking_dcs` pins no CLS placement, so there is no
`INS_LOC` to compare — `E0` is the level this shape can carry.

### One defect found on the way, fixed

The first pass returned `verdict=diff` on a bitstream whose cells, attrs and
conns all matched and whose residual was empty: `c1` demanded a `DCS` cell
back from the decode. There is none to give — `DCS_MODE` lives in the
`longfuses` tables and `gowin_unpack` decodes no `longfuses` table on **any**
device, the same architectural hole `dqce_recovered_via_pip` already worked
around one table up. `c1` now requires of a used `DCS` the positive evidence
the bitstream does carry: its output node (`CBRIDGEOUT_<half><n>`) driving the
clock plane. It proves the route, not the mode fuse; the mode fuse stays
covered by the bit-level comparison and by `c2`.

The pair the measurements were made with: nextpnr binary `cfc97099…`
(unchanged — this task needed no nextpnr source change), chipdb `.bin`
`d700cade…`, apicula msgpack `faa33ef4…` (rebuilt twice, byte-identical).

## 5. Rows

| batch | runs | ok | diff | aborted | what it measured |
|---|---|---|---|---|---|
| `p1f2-dcsin` | 4 | 4 | 0 | 0 | attribution: which half the bare central-mux gate name is |
| `p1f2-dcs-e0` | 2 | 0 | 2 | 0 | first pass; both `diff` on the `c1` defect above, both `EQUIV E0 ok` |
| `p1f2-dcs-e0b` | 3 | 3 | 0 | 0 | `q1`, `q2` and `sel4` after the `c1` fix — the authoritative rows |

Runs this task: 9. Cumulative: 230.

## 6. Still open

* `SELFORCE` / `CLKSEL` fuses stay UNVERIFIED. Every bitstream in this
  campaign, the four-DCS one included, leaves both bridge cells' `SELFORCE`
  and `CLKSEL` wires unrouted — the vendor drives the selection from fabric
  logic through wires that carry no fuse of their own in these designs, so
  there is nothing to attribute. Naming what would close it: a design whose
  `CLKSEL` cannot be constant-folded *and* whose selection logic the vendor is
  forced to place where the bridge cell can see it.
* `PCLK*` as a DCS input source is still driverless: `get_clock_ins` builds
  the 138C's PCLK entries but `fse_create_5a138_clocks` never turns them into
  nodes (the loop is commented out upstream). Out of this task's scope — no
  bitstream in this campaign selects a `PCLK*` source.
* `nextpnr` reports `DCS: 5/4 125%` utilisation on a one-DCS design. Present
  identically in the `P1.T31` log, so not a regression of this change; it is a
  bel-accounting defect, not a placement one (the design places and routes).
