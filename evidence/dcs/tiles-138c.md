# `evidence/dcs/tiles-138c.md` — P1.T28: 138C DCS tile types (cross-referenced)

Full structured data: `tiles-138c.json` (this file summarizes it).

## Derivation

`chipdb.py`'s DCS builder (`:2790-2880`) searches the **same**
`fse['header']['grid'][61]` values 80/81/84/85 the DQCE builder searches
(`evidence/dqce/tiletypes-138c.md`), just paired two-per-quadrant instead of
one-per-quadrant: `for q, types in enumerate([(85, 84), (80, 81), (80, 81),
(85, 84)])` (`chipdb.py:2790`). No separate oracle campaign was run for DCS
— the physical cells are, by construction, the same four cells the DQCE
8-run probe already measured:

| type | cell (row, col) | DQCE-probe status |
|------|------------------|--------------------|
| 80   | (54, 88)         | MEASURED live |
| 81   | (54, 89)         | ASSUMED (unconfirmed, unrefuted) |
| 84   | (54, 92)         | MEASURED live |
| 85   | (54, 93)         | MEASURED live |

## Quadrant pairing (as coded today)

```
q=0: (85, 84)   q=1: (80, 81)   q=2: (80, 81)   q=3: (85, 84)
```

`q=0` and `q=3` share the `(85, 84)` pair; `q=1` and `q=2` share `(80, 81)`.
Each quadrant's two DCS instances (`j=0,1`) resolve to whichever of the
pair's two cells the linear search finds — so, on both 25A and 138C, all
four DCS quadrants ultimately route through the same four-cell cluster the
DQCE builder uses. This is a **naming-orthogonal** finding: unlike `DQCE`
(vendor name `DCE` on Arora V, see the DQCE artifact), `DCS` needed no
rename — it is documented unchanged for Arora V (`UG306-1.0.1E` §3.2,
`CLKIN0-3`/`CLKSEL`/`SELFORCE`/`CLKOUT`) and `examples/gw5a/dcs.v` already
instantiates it under that name.

## Current gap (not this task's fix — P1.T31)

138C's DCS allow-list (`chipdb.py:2825-2832`) admits only `q>=2` for devices
outside `{GW1N-9, GW1N-9C, GW2A-18, GW2A-18C, GW5A-25A}` — so 138C today
builds 2 of 4 DCS quadrants (`q=2,3`), the same shortfall DQCE had before
`P1.T29`; where it does run, it falls into the pre-5A generic port-name
branch instead of a 138C-traced `gw5_dcs_inputs_138c` table.

## Verdict for `S9`

DCS's 138C tile types are the same four values, at the same four cells,
that the DQCE oracle campaign measured — 3 of 4 confirmed live, 1
unconfirmed-but-unrefuted. `P1.T31` can key its 138C allow-set and quadrant
pairing off `tiles-138c.json`/`tiletypes-138c.json` directly, with no
further oracle spend for the tile-type question (only the port-table trace
`P1.T31` itself owns needs new runs).
