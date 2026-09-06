# DCS on the GW5AST-138C, open flow — half boundary closed, input side named

Follow-up to `P1.T31`/`P1.T32`, whose row recorded `Can't route the muxed_clk
network` and named the cause as "the DCS output reaches only one half of the
clock plane". That diagnosis was half right; both halves are measured below.

## 1. What the vendor does — decoded, not inferred

Vendor bitstream `p1t31-dcs-e1b-clocking_dcs-0000/run/impl/pnr/run.fs`, one
`DCS` on the board clock (`V22`), four loads in the fabric. Every non-default
clock pip it sets:

```
(54,93) R55C94_P26A..P26D <- R55C94_BLMDCLK1     # the DCS input multiplexers
(81,87) R82C88_P16D       <- R82C88_CBRIDGEOUT_TOP6   # the DCS output, crossing
(100,53) R101C54_GT00 <- R101C54_SPINE3
(100,84) R101C85_GT10 <- R101C85_SPINE7
(100,89) R101C90_GT00 <- R101C90_SPINE3
(93,53)  R94C54_GBO0  <- R94C54_GT00
(107,84) R108C85_GBO1 <- R108C85_GT10
(108,89) R109C90_GBO0 <- R109C90_GT00
```

So the DCS output does **not** stay on the spine it is named after: it joins
the half's `CBRIDGEOUT_TOP6` node and re-enters the clock plane through the
other bridge cell's multiplexer, on an ordinary quadrant spine.

## 2. The output side — FIXED (nextpnr)

`globals.cc global_DCS_pip_filter` named eight spine ids —
`SPINE6/7/14/15/22/23/30/31`, the pre-5A CLKOUT spines — as the only ones a
DCS-managed net may travel on. On this die the net legitimately travels on
`SPINE4`, so every route was rejected.

The permitted set is now **derived from the database**
(`gowin_arch_gen.dcs_spines_and_clkouts`): the DCS output wires, plus every
spine a clock pip drives from a wire of the DCS output's node. That returns

* GW5A-25A — exactly the eight ids the filter used to name (no pre-5A device
  changes behaviour), and
* GW5AST-138C — those four plus spines 4 and 5 of each quadrant (16 total).

Two further changes belong to the same rule:

* a DCS-managed net may reach a spine that is **not** a DCS output only from a
  DCS output, otherwise the router simply takes the clock to the loads on a
  spine of its own and leaves the mux out of the network it is meant to gate
  (measured: it did exactly that on the first build of the derived set);
* `route_dcs_net` selected its hardware DCS by asserting that every bound pip
  downhill of the clock source lands on a DCS input. A clock source normally
  feeds more than the DCS — the same pin clocks the logic driving `CLKSEL` —
  so it now takes the pips that carry *this* net into a DCS input, and errors
  if none does.

Measured effect on the `P1.T31` design: `Can't route the muxed_clk network` at
the half boundary is gone; the backwards BFS now reaches the DCS output node
through `X38Y64/SPINE4 <- X93Y54/SPINE14` and stops one hop short of the
source, on the DCS **input** side.

## 3. The input side — GAP, named exactly

`P26A..D` (and `P27*`, `P36*`, `P37*`) are fed, in the model, only by the
bridge cells' `PCLK*`, `*MDCLK*` and `*BDCLK*` wires. In the 138C database
**nothing drives any of them**:

* `PCLKB0` as a pip destination: **0** cells on the whole die (same for
  `PCLKB1`, `PCLKT0`, `BLMDCLK0/1`, `BRMDCLK1`);
* node `PCLKB0` = `{(54,88,'PCLKB0'), (54,93,'PCLKB0')}` — the two bridge
  cells and nothing else; `BLMDCLK1` is in no node at all.

So a clock source cannot reach a DCS input: the primitive is an island on its
input side, and the vendor's own answer (`P26A-D <- BLMDCLK1`) names a wire
the model never connects to anything. This is the same hole the `P1.T31` row
recorded for `SELFORCE`/`CLKSEL` ("no vendor route into the bridge cells"),
now shown to cover the clock inputs too.

**What would close it:** a campaign that measures where `*MDCLK*`/`*BDCLK*`/
`PCLK*` of cells (54,88)/(54,93) come from — which IO, PLL or HCLK output
drives each, and through which pip or fuseless hop — and adds those entries to
`fse_create_5a138_clocks`. It is a device measurement, not a router rule; one
vendor bitstream (the one above) gives one point of it, `BLMDCLK1` for a clock
on `V22`, which is not enough to model a multiplexer.

**Consequence for Phase 1:** the `DCS` row stays open at `E0`; `P1.T40`'s
end-to-end design carries every other clocking primitive and says so.

Pair the measurements above were made with: nextpnr `cfc97099…`, chipdb
`.bin` `0a413537…`, apicula msgpack `8bb0932e…`.
Tests: `himbaechel/uarch/gowin/tests/check_dcs_spines.py` (3 checks).
