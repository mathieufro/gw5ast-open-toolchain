# How a GW5AST-138C `PLL` output reaches the clock plane (`P1.F3`)

Two of the four gaps `P1.T40` carried out of Phase 1 are the same question
asked twice:

* **no `PLL`->HCLK path in the model** — nextpnr refused
  `MPLLCLKOUT0 -> CLKDIV_I50` "using dedicated routing", so the E2E design had
  to run its `PLL` *beside* the HCLK chain instead of through it;
* **`PLL_B[*]` outputs reach no fabric flop** — from `PLL_B[2]` the same
  refusal came for an ordinary flop, while `PLL_L[0]` was fine.

Batch `p1f3-pll-route` (6 vendor runs, driver `route_probe.py`, log
`../_runs/p1f3-pll-route.log`,
`BATCH_COMPLETE p1f3-pll-route runs=6 ok=6 diff=0 aborted=0`) answers both.
Each point is one `PLL` at a pinned site at the `P1.T39` reference operating
point; the `a-*` points take `CLKOUT0` into an HCLK lane (`CLKDIV`,
`INS_LOC BOTTOMSIDE[4]` = block 5 lane 0), the `b-*` points into a fabric
flop. Every `.fs` is decoded with `../clocking/decode_route.py` against
chipdb `faa33ef4…` — the pair the gaps were measured on.

## 1. A left-edge site owns a clock-plane wire; a bottom-edge site does not

| point | site | spine the clock lands on | the pip that drives it |
|---|---|---|---|
| `a-l0-hclk` | `PLL_L[0]` | `SPINE9` | **`(54, 93) SPINE9 <= TLPLL0CLK0`** |
| `a-b0-hclk` | `PLL_B[0]` | `SPINE19` | no `*PLL*` wire anywhere in the bitstream |
| `b-b0` | `PLL_B[0]` | `SPINE9` | **`(81, 85) SPINE9 <= BRMDCLK1`** |
| `b-b1` | `PLL_B[1]` | `SPINE9` | `(81, 85) SPINE9 <= BRMDCLK1`, same bits |
| `b-b2` | `PLL_B[2]` | `SPINE27` | as `b-b0`, in the right-hand quadrant |
| `b-b3` | `PLL_B[3]` | `SPINE27` | as `b-b0`, in the right-hand quadrant |

`TLPLL0CLK0` is clock wire 81 and the database already carried it as a source
of the bridge cells' spine multiplexers. What it had at the **site** end was
nothing at all: `MPLL0CLKOUT0` was a node of one wire, `(27, 1)
MPLLCLKOUT0`, and `TLPLL0CLK0` a node of two, `(54, 88)` and `(54, 93)`. The
two were never joined, so no route existed between a `PLL` and its own clock
wire, and the only way out of the site was the fuseless
`MPLLCLKOUT0 -> F0` logic pip — which is a fabric wire in the site's own row,
and row 108 (the bottom-edge sites) has no CLS on it. That is the whole of
gap b: not a different primitive, a different row.

The bottom sites use no `*PLL*` clock wire at all. The vendor takes their
output to fabric and back onto the plane through a **logic-to-clock gate**,
and the gate drives the quadrant spine directly. The identical mechanism, at
the identical bits, in two independent runs.

## 2. The HCLK entry is not a `PLL` entry — it is the ordinary logic entry

Decoding the block-5 cell of `a-l0-hclk` and `a-b0-hclk` gives, in both:

```
108 117 bel HCLK5 ['HCLK_BUF_BI50="HCLK_MUX_BETA50"',
                   'HCLK_MUX_ALPHA50="HCLK_BUF_BO50"',
                   'HCLK_MUX_BETA50="L2HCLK50"']
108 117 pips CLK0 <= GB20
108 116 pips GBO0 <= GT00
100 116 clock_pips GT00 <= SPINE19
```

`L2HCLK50` is the block cell's own `CLK0`, taken off a global branch. So a
`PLL`->HCLK cascade needs **no** new HCLK-side pip and no `PLL` entry in table
48: every hop from the spine on already existed. The one missing hop was the
`PLL`'s entry onto a spine, §1.

## 3. What the database was dropping — one filter, one line

`chipdb.fse_clock_pips_138` walked the two half-backbone tables and threw away
every spine source that is not a `CBRIDGEOUT*` unless the cell is one of the
two bridge cells:

```python
if dest.startswith('SPINE'):
    if ttyp not in bridge_tile_types_138:
        if not src.startswith('CBRIDGEOUT') or not is_allowed_spine_input(src, dest):
            continue
```

`(81, 85)` is a quadrant cell, not a bridge cell, so `SPINE9 <= BRMDCLK1` —
the row §1 measured — was discarded, together with every other gate->quadrant
spine row on the die. With it went the only way onto the clock plane that a
site with no clock wire of its own has.

## 4. The change

`apycula/chipdb.py`

* `_gw5_logic_clock_gate_ids()` — the gate band, read from the wire names, so
  the spine sources here and `gw5_logic_clock_gates` read one table.
* `fse_clock_pips_138` — a gate is a legal spine source at **any** cell, with
  the half suffix the gate names carry; the `CBRIDGEOUT` rule keeps its place
  for everything else. `(81, 85) SPINE9` gained
  `BLBDCLK0_BOT BRBDCLK3_BOT BRMDCLK1_BOT TLBDCLK0_BOT TLBDCLK2_BOT
  TLMDCLK0_BOT TRBDCLK1_BOT` beside the two `CBRIDGEOUT*` it had.
* `_gw5a_pll_clk_wires` + `fse_create_slot_plls` — the measured
  `(slot 0, CLKOUT0) -> TLPLL0CLK0`, added as a fuseless pip inside the site's
  own tile and a node member on the clock wire. A fuseless pip and not a plain
  merge, for the reason the file already records for the logic wire: one node
  would leave a single wire with a single type and the global router would
  refuse it.

Only the measured entry is in `_gw5a_pll_clk_wires`. The other eleven sites
are **not** claimed: they reach the plane through a gate, which §1 shows every
site can do, and their own clock wires stay an open measurement (one vendor
run each) rather than an inferred table.

## 5. Verdicts

Both rows are in `runs.jsonl`; the batch lines and `EQUIV` lines are in
`summary.md` §6.
