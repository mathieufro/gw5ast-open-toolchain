# `evidence/dqce/quadrants-138c.md` — P1.T29: the 138C's DQCE quadrants

## The premise the blueprint and `spec-primitives.md` carried was wrong twice

**MEASURED.** `spec-primitives.md`'s DQCE row says the 138C "runs against
unverified tables, and for only 2 of 4 quadrants". Both halves of that are
false on this die:

1. **It ran for none of them.** `fse_create_clocks` dispatches
   `GW5AST-138C` to `fse_create_5a138_clocks` and `return`s
   (`apycula/chipdb.py`, the `if device in {'GW5AST-138C'}` branch) — and the
   DQCE and DCS builders sit *after* that return. Loading the shipped
   `GW5AST-138C.msgpack.xz` (`a2d134c3`, the T38b/T41 pair) and counting
   `extra_func` entries gives `DQCE cells: []` and `DCS cells: []`. Zero, not
   two of four.
2. **There are not four quadrants to fill.** The pre-5A search values
   80/81/84/85 all resolve on this die (`P1.T28`), but they resolve to four of
   the *six* clock-bridge cells (`chipdb.bridge_tile_types_138 = {80..85}` at
   (54, 88)..(54, 93)), and only two of those six carry a spine multiplexer at
   all:

   | cell | ttyp | SPINE multiplexers | DCS port muxes |
   |---|---|---|---|
   | (54, 88) | 80 | `SPINE16..21` | `P36A-D`, `P37A-D` |
   | (54, 89) | 81 | none | none |
   | (54, 90) | 82 | none | none |
   | (54, 91) | 83 | none | none |
   | (54, 92) | 84 | none | none |
   | (54, 93) | 85 | `SPINE8..13` | `P26A-D`, `P27A-D` |

   Under the pre-5A spine formula `SPINE(q * 8 + j)`, `SPINE8..13` is exactly
   quadrant 1's six `dqce[j]` slots and `SPINE16..21` is quadrant 2's. So the
   die has **quadrants 1 and 2 and no others** — its clock plane is two
   halves, not four quadrants (`fse_create_5a138_clocks`: "these halves are
   not organised into a 2x2 matrix ... but stretched out as 1x4"), and
   quadrant 1 is the top half, quadrant 2 the bottom.

   A naive un-gating of the pre-5A `q < 2` skip would have given the 138C
   quadrants 2 **and 3**, attaching quadrant 3 to type 81 at (54, 89) — a cell
   with no spine multiplexer in it. That is the silent mis-attachment `S9`
   guards against, and it is why the quadrant map is a per-device table
   (`chipdb._dqce_quadrants`) rather than a widened allow-list.

## Vendor confirmation — batch `p1t29-dce`, 3 oracle runs, 0 aborted

`fuzz.gw5ast138c.shapes.clocking_dqce`, `n` simultaneous `DCE` instances each
on its own clock net, driver `evidence/dqce/probe_capacity.py`, ledger
`evidence/dqce/runs/capacity-runs.jsonl`, log `evidence/_runs/p1t29-dce.log`.

```
BATCH_COMPLETE p1t29-dce runs=3 ok=3 diff=0 aborted=0
```

| run | vendor `Clock Resource Usage Summary` | spine multiplexer pips the bitstream sets |
|---|---|---|
| `dce01` (n=1)  | `DCE 1/76`  | `(54,93) SPINE8 <- BLMDCLK1_BOT` |
| `dce12` (n=12) | `DCE 12/76` | `(54,93) SPINE8..13 <- BLMDCLK1_BOT` **and** `(54,88) SPINE16..21 <- BRMDCLK1_BOT` |
| `dce13` (n=13) | `DCE 13/76` | as `dce12`, plus fuse movement in (54, 88) that no further spine pip accounts for |

The `dce12` row is the decisive one: twelve `DCE` occupy **exactly** the twelve
spine multiplexers the model above predicts, six in each of the two cells, and
nothing else. The vendor's own `76` is a family-generic pool figure, not the
number of spine-gating sites this die exposes — the routed bitstream is the
measurement, the summary line is not.

Attribution is by `unpack_netlist` on the kept `.fs` (no extra compiles): the
pips listed are the ones present inside those two cells and absent from the
`n = 1` build.

## What the model now says

`chipdb.fse_create_dqce` (extracted from `fse_create_clocks` so both the pre-5A
path and the 138C path call it) builds, for `GW5AST-138C`:

* `extra_func[(54, 93)]['dqce'][0..5]` — `clkin = SPINE8..13`
* `extra_func[(54, 88)]['dqce'][0..5]` — `clkin = SPINE16..21`
* `ce = ['A0','B0','C0','D0','A1','B1'][j]` in both, unchanged from the pre-5A
  model — every one of those wires exists in the cell.

Pre-5A devices are unaffected: `dqce_quadrant_types(device)` reproduces the old
`enumerate([85,80,81,84])` + `q < 2` skip exactly, and a `GW2A-18` chipdb built
from the base commit and from this one have **identical** `dqce`/`dcs`
`extra_func` dicts (4 cells each).
