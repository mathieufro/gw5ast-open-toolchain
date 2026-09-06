# `evidence/dcs/ports-138c.md` — P1.T31: the 138C's DCS quadrants and ports

## Premise correction

Same two refutations as the DQCE row (`evidence/dqce/quadrants-138c.md`): the
shipped 138C chipdb carried **zero** `extra_func['dcs']` entries, not "2 of 4
quadrants", because `fse_create_clocks` returns before the DCS builder for this
device; and the die has two quadrants, not four.

The DCS-specific finding on top of that: **both DCS of a quadrant live in the
same cell on this die.** The pre-5A model pairs a quadrant's two DCS across two
tile types (`[(85,84),(80,81),(80,81),(85,84)]`) and keys the sub-entry by
`q // 2`, which relies on the cell coordinate to carry the `(q, dcs_idx)`
identity. Here (54, 93) carries `P26A-D` **and** `P27A-D`, and (54, 88) carries
`P36A-D` **and** `P37A-D` — so the quadrant's two DCS would collide on one
sub-entry. `fse_create_dcs` therefore keys by `dcs_idx` whenever a quadrant's
two tile types are equal, and by `q // 2` otherwise (the pre-5A behaviour,
untouched).

## Vendor confirmation — batch `p1t31-dcs`, 2 oracle runs, 0 aborted

`fuzz.gw5ast138c.shapes.clocking_dcs`, `n` simultaneous `DCS`, driver
`evidence/dqce/probe_capacity.py`, ledger `evidence/dcs/runs/capacity-runs.jsonl`,
log `evidence/_runs/p1t31-dcs.log`.

```
BATCH_COMPLETE p1t31-dcs runs=2 ok=2 diff=0 aborted=0
```

| run | vendor summary | DCS input-mux pips the bitstream sets |
|---|---|---|
| `dcs01` (n=1) | `DCS 1/20` | `(54,93) P26A,P26B,P26C,P26D <- BLMDCLK1` |
| `dcs04` (n=4) | `DCS 4/20` | `(54,93) P26A-D, P27A-D <- BLMDCLK1` **and** `(54,88) P36A-D, P37A-D <- BRMDCLK1` |

Four `DCS` occupy exactly the four port groups the model predicts — two per
cell, all four `CLKIN` multiplexers of each programmed — and nothing else. As
with `DCE`, the vendor's `20` is a family pool figure, not this die's site
count; the routed bitstream is the measurement.

Model, per `chipdb.fse_create_dcs` for `GW5AST-138C`:

| cell | `dcs_idx` | `clkout` | `clk` |
|---|---|---|---|
| (54, 93) | 0 | `SPINE14` | `P26A`, `P26B`, `P26C`, `P26D` |
| (54, 93) | 1 | `SPINE15` | `P27A`, `P27B`, `P27C`, `P27D` |
| (54, 88) | 0 | `SPINE22` | `P36A`, `P36B`, `P36C`, `P36D` |
| (54, 88) | 1 | `SPINE23` | `P37A`, `P37B`, `P37C`, `P37D` |

`dcs_prefix` is `CLKIN` on this family (`examples/gw5a/dcs.v`,
`UG306-1.0.1E` §3.2), so the bel pins are `CLKIN0..3`, not `CLK0..3`.

Each quadrant's eight spines are therefore fully accounted for: six DQCE-gated
(`SPINE q*8+0..5`) plus two DCS outputs (`SPINE q*8+6,7`).

## GAP — the control wires are UNVERIFIED (owner: a later DCS row)

`SELFORCE` and `CLKSEL[0..3]` are **not traced on this die.** In all five kept
vendor bitstreams (`dce01`, `dce12`, `dce13`, `dcs01`, `dcs04`) no external net
is routed into either bridge cell for those ports: every one of the cells'
`A*`/`B*`/`C*`/`D*` inputs is driven by the cell's own `F*` outputs, exactly as
in a `DCE`-only build. Where the vendor puts a dynamically-driven `CLKSEL` on
this die is an open question, and answering it needs its own campaign.

`gowin_arch_gen.py` requires a `selforce` and a `clksel` list to create the bel
at all, so the model supplies the two pre-5A wire sets — `C2` +
`C1/D1/A2/B2` for one DCS of a cell and `D3` + `D2/A3/B3/C3` for the other, so
that two DCS sharing a cell at least name different wires. Those names are
UNVERIFIED and are marked as such in `chipdb.fse_create_dcs`. Consequence: a
138C design that drives `CLKSEL` dynamically is not yet modelled; a design that
uses the mux with a static selection is.

## `gowin_pack`

`GW5A.get_DCS_fuses` refuses the whole family. The scan-every-cell emitter the
25A used is now `GW5A.gw5a_dcs_fuses` (behaviour unchanged — `GW5A_25A`
delegates to it) and `GW5AST_138C.get_DCS_fuses` delegates to it too, because
this die scatters DCS fuses the same way.
