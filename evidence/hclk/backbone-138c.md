# GW5AST-138C HCLK -> global-clock backbone — P1.T08c

apicula `clocking/gw5a-hclk-6block`. Oracle: Gowin IDE **1.9.12.03 Standard,
licensed**. Follow-up the P1.T11 measurement forced (`clkdiv-138c.md` §2, D98).

## Verdict, up front

**D98's premise is REFUTED.** The task was to name the sixteen
`{T,B,R,L}BDHCLK{0..3}` backbone wires in `clknames_5ast138c` so that
`gw5_make_hclk_to_clk_gates` fires and a CLKDIV output routes. Measurement says
the GW5AST-138C has neither a sixteen-wire BDHCLK band nor the gate cells that
function reads. **Routing is NOT achieved and no chipdb behaviour changed.**
What this row lands is the measurement, a data table pinning it, and three
tests (one passing, two `xfail(strict=True)` carrying the refutation).

## 1. There is no HCLK->GCLK gate cell on this device (MEASURED, `.fse`)

`gw5_make_hclk_to_clk_gates` builds every gate pip from a table-48 row whose
**source** is in `{25,27,28,29}` (`HCLK_TO_GCLK0..3`) and whose **destination**
is a clock-network wire. Scanning every cell of both dice for exactly that
shape:

| device | cells with such rows | destinations |
|---|---|---|
| GW5A-25A | **4** — ttyp 410 (0,59), 393 (36,46), 187 (27,91), 257 (10,0) | 169-172 / 177-180 / 173-176 / 181-184 = `TBDHCLK0-3` / `BBDHCLK0-3` / `RBDHCLK0-3` / `LBDHCLK0-3`, plus 185-188 / 193-196 / 189-192 / 197-200 = `HCLKDIV*` |
| GW5AST-138C | **0** | — |

On the 138C the only `{25,27,28,29}` rows anywhere are the six HCLK block cells'
own `{25,27,28,29} -> {34,35,36,37}` (which the 25A block cells have too, and
which stay inside the block). The HCLK-block -> clock-mux hop on this device
**carries no fuse at all**, so the primitive it needs is a Himbaechel *node*,
not a gate pip. Naming sixteen wires would not make the function fire.

## 2. What a block's four CLKDIV outputs actually are (MEASURED, 4 vendor runs)

A one-CLKDIV-at-a-time staircase. Column 2 is the block cell's own lit
table-48 wire index at (108,117) (`dest 34+i <= src 30+i`); column 3 is the
clock wire the **central clock mux (54,88), table 38** then selects onto a
SPINE. Every design landed in HCLK block 5 — the vendor's choice, not a
constraint.

| N CLKDIV | block-5 wire indices lit | clock wires selected | vendor `run.fs` sha256 (head) |
|---|---|---|---|
| 1 (P1.T11) | 0 | **109** | `3d36f0aa` |
| 2 | 0,1 | **109, 110** | `91252ceb` |
| 3 | 0,1,2 | **109, 110, 224** | `370de8c9` |
| 4 | 0,1,2,3 | **109, 110, 224, 225** | `e1d97917` |

So block 5's bijection is `{0:109, 1:110, 2:224, 3:225}` — four wires drawn
from **two disjoint bands**, not one contiguous sixteen, and none of them in
the 25A's 169..184. Landed as `chipdb._gw5a_hclk_to_clk` (inert: nothing
consumes it yet, so the chipdb is byte-identical) and pinned by
`test_hclk5_backbone_map_138c_is_the_measured_staircase`.

A fifth run with 24 distinct CLKDIVs (`run.fs` `b0601e78`, vendor utilisation
`CLKDIV 24/24`) put four more wires on spines — **107, 108, 220, 221** — which
is consistent with a 6x4 backbone in two bands but does **not** identify which
block owns them. Twenty of the twenty-four wires are **NOT MEASURED**: the
vendor placed every design in block 5 and the oracle exposes no CLKDIV
placement handle, so isolating the other five blocks needs an instrument this
task did not have. They are absent from the table rather than guessed.

## 3. Two further defects the same measurement exposed (recorded, not fixed)

1. **`fse_clock_pips_138` never reads table 38.** It reads only
   `CLOCK_MUX_TOP`(90) / `CLOCK_MUX_BOTTOM`(91). The 138C's central clock mux
   at (54,88) and (54,93) is a **table-38** cell and that is exactly where the
   vendor's `SPINE17 <= 109` pip lives. Every table-38 clock pip on this device
   is therefore missing from the routing graph.
2. **Its `if srcid in range(164, 237): continue` "skip longwires" rule discards
   the upper backbone band**, 213..236 — which includes the measured 220, 221,
   224, 225.
   Neither is fixed here: both change `dev.clock_pips` for every 138C design
   and re-validating that is a task of its own.

## 4. E0 / E1 — NOT COMPUTED, with the cause measured

**DIFF_COUNT n/a. RESIDUAL_UNEXPLAINED n/a.** The open side still has no `.fs`.
A purpose-built vehicle whose `CLKDIV.CLKOUT` is consumed as **data** rather
than as a clock (`$DATASTORE/batch/p1t08c/e0/top.v`) was built to sidestep the
clock escape, and nextpnr still exits **125**:

```
Warning: Failed to route net 'div_clk' from X64Y108/CLKDIV_O41 to X97Y107/A4 using dedicated routing.
Warning: Failed to route net 'clk_IBUF_I_O' from X91Y108/CLK1 to X64Y108/CLKDIV_I41 using dedicated routing.
Warning: Failed to find a route for arc 24 of net clk_IBUF_I_O.
ERROR: Routing design failed.
```

That is the sharper statement of the blocker: **both** ends of the CLKDIV bel
are islands. The output has no escape (§1/§2, this task); the **input** has
none either, because `_gw5_pin_to_hclk` has no `GW5AST-138C` entry — that is
the S10/S12 seam Phase 3 owns. E0/E1 on this primitive needs both.

The vendor half of the compare is, however, no longer vacuous: the P1.T08c
unpacker work makes `gowin_unpack` decode the primitive, so the moment the open
side routes there is something to compare. `equiv.unpack_netlist` on the P1.T11
vendor bitstream now reports
`CELL TYPES: {'BANK': 8, 'CLKDIV_': 1, 'DFF': 138240, 'HCLK': 1, 'IOB': 324, 'LUT': 28}`
(was 138,600 cells of four types with no CLKDIV at any tile) and
`Cell(x=117, y=108, z=0, type='CLKDIV_') ['DIV_MODE="2"']`.
`DECODE_CHECK` is not run: it needs the open-flow `top_pnr.json` + `.fs` pair.

## 5. Regression baselines

- `GW5A-25A.msgpack.xz` : `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca` — **byte-identical** to the Phase-0 family baseline.
- `GW5AST-138C.msgpack.xz` : 825,580 B, `a3c7510fed6b80ad1540d399e9bb8eb6e406bd7f698eaca5cfe0e227e3402a86` — **byte-identical** to the P1.T08b baseline. Nothing this task landed changes a chipdb.
- Installed `chipdb-GW5AST-138C.bin` left at `72e6ff4a6b5d9a7dd85b9d8dfb6c3a847285ea076a12ba4fb5743dcd5bc4325e` in both `$DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/` and `$DATASTORE/chipdb/std/` — see §6.
- Openflow smoke (`$DATASTORE/oracle-smoke`): yosys/nextpnr/gowin_pack `0/0/0`, `top.fs` **34,668,145 B** `489587b1…`, `chipdb_sha256=72e6ff4a…`.

## 6. NEW FINDING — `gowin_arch_gen.py` is non-deterministic

Two `.bin` regenerations from the **byte-identical** `a3c7510f` msgpack, same
tree, same installed nextpnr `8566c51`, minutes apart:

| run | bytes | sha256 |
|---|---|---|
| 1 | 63,984,467 | `cd616a24fdc145b92e997cb6b975961c2def1eda11d0a2174c92a25118fd3773` |
| 2 | 63,995,091 | `ca53b9e8480f97c35d58bb04abcad0b7805b835e60beba727a47ee0ae821c604` |

They differ in **size**, so this is not a hash-ordering artefact of the writer
alone. Consequence: the `.bin` sha256 recorded in any evidence row is **not
reproducible**, and the "matching binary/.bin pair" discipline cannot be
verified by hash today. This is the `gowin_arch_gen.py` analogue of the
`chipdb_builder` non-determinism P0.T13b fixed, it is pre-existing (the P1.T08b
`72e6ff4a` cannot be reproduced either), and it belongs to nextpnr's uarch
generator, not to this branch. **Recorded, not fixed.** Because the chipdb is
byte-identical to the one the installed `.bin` was generated from, the proven
`72e6ff4a` pair was deliberately left in place rather than replaced by an
unproven fresh one.

## 7. Tests

`tests/test_gw5ast138c_clocking.py`:
`test_hclk5_backbone_map_138c_is_the_measured_staircase` (passes),
`test_clknames_138c_has_16_bdhclk` and `test_hclk_to_clk_gates_fire_138c`
(`xfail(strict=True)`, each carrying the measured refutation as its reason so
the requirement cannot be silently lost),
`test_unpack_decodes_clkdiv_138c` / `test_unpack_hclk_completeness_138c`
(heavy) / `test_unpack_hclk_decode_is_device_gated`.

Fast scope `pytest tests -q -m "not heavy and not gate_proof"`:
**265 passed, 2 skipped, 50 deselected, 1 xfailed**.

## 8. Artefacts

`$DATASTORE/batch/p1t08c/{n2,n3,n4,n24,n24b,e0}/` — `top.v`, `top.cst`,
`run.tcl`, the vendor `run/` tree, and for `e0/` the open-flow logs.
`$DATASTORE/batch/p1t11/clkdiv/` — the N=1 run of the staircase.
