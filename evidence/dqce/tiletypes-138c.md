# `evidence/dqce/tiletypes-138c.md` — P1.T28: 138C DQCE tile types, re-derived

Full structured data: `tiletypes-138c.json` (this file summarizes it).

## The four 138C tile types

`chipdb.py`'s DQCE builder (`:2757-2790`) searches `fse['header']['grid'][61]`
for values `80, 81, 84, 85`. **MEASURED** directly from the shipped
`GW5AST-138C.fse` (109x182 grid): all four values occur, **each exactly
once**:

| type | cell (row, col) | occurs |
|------|------------------|--------|
| 80   | (54, 88)         | 1      |
| 81   | (54, 89)         | 1      |
| 84   | (54, 92)         | 1      |
| 85   | (54, 93)         | 1      |

For comparison, on `GW5A-25A` (37x92 grid) the same four values also occur
exactly once each, clustered the same way:

| type | cell (row, col) |
|------|------------------|
| 80   | (18, 43) |
| 81   | (18, 44) |
| 84   | (18, 47) |
| 85   | (18, 48) |

## Why they differ from a naive per-quadrant assumption

The four numbers 80, 81, 84, 85 are **not invalid** on the 138C `.fse` — each
resolves to a real, unique cell, so `chipdb.py`'s existing "stop at first
match" search already finds *a* cell for every type, on both devices. What
was unverified is the geometry those cells sit in. On both devices the four
types cluster at the die's geometric center row (`54 = floor(109/2)` on
138C, `18 = floor(37/2)` on 25A), in two adjacent-column pairs straddling
`center_col` — never scattered one-per-physical-quadrant the way the source
comment's ASCII diagram (`chipdb.py:2752-2756`) suggests to a first reading.
That is fine for 25A, a single clock-plane device. P1.T04 already measured
138C as a **two-half** topology (6 HCLK blocks split 2-top/4-bottom, joined
by a central bridge) — so a single central-row cluster of 4 cells is only
the right host for *both* halves if those 4 cells are genuinely shared
between halves, an assumption the pre-5A-derived search never had to make.

## Naming: `DQCE` is not the vendor's name on this family (MEASURED)

Compiling `examples/dqce.v`'s generic (pre-5A) `DQCE` instantiation against
`GW5AST-138C` fails at Gowin's own Verilog elaboration:
`EX3937 Instantiating unknown module 'DQCE'`. `UG306-1.0.1E` (Arora V Clock
User Guide) never mentions `DQCE`; its §3.1 primitive is **`DCE`**
(port-identical: `CLKIN`/`CE`/`CLKOUT`). Renaming the instantiation to `DCE`
compiles cleanly (all 8 oracle runs below, `verdict=ok`). apycula's own
`extra_func['dqce']` dict key is an internal name, unaffected by this — but
any GW5A(ST)-targeted Verilog (this probe, or a future user example) must
say `DCE`.

## Oracle campaign (8 runs, 0 aborted)

`fuzz.gw5ast138c.shapes.clocking_dqce_probe` (sequences A/B, `n_dqce=1..4`
simultaneous `DCE` instances, CE from combinational functions of two IO
pins), run via `evidence/dqce/run_probe.py`. Batch log:
`evidence/_runs/p1-dqce-types.log`. Ledger:
`evidence/dqce/runs/oracle-runs.jsonl` (8 rows, all `verdict=ok`).

```
BATCH_COMPLETE p1-dqce-types runs=8 ok=8 diff=0 aborted=0
```

## Presence-diff: which of the 4 cells actually carry fuses (MEASURED)

`presence_diff(oracle-smoke baseline, A4.fs)` and `presence_diff(baseline,
B4.fs)` (the two `n_dqce=4` builds):

| cell | type | A4 bits moved | B4 bits moved | verdict |
|------|------|---------------|----------------|---------|
| (54, 88) | 80 | 18 | 14 | **MEASURED live** |
| (54, 92) | 84 | 7  | 7  | **MEASURED live** |
| (54, 93) | 85 | 9  | 9  | **MEASURED live** |
| (54, 89) | 81 | 0  | 0  | **ASSUMED** — see note |

Three of the four grid-derived cells show real, repeatable fuse movement
when `DCE` instances are added — confirming those three are genuinely live
DQCE hosts on 138C, at exactly the cells the existing (pre-5A-derived)
search already finds. The fourth, `81@(54,89)`, shows **zero** movement in
either 4-instance build. This does not refute it: apycula's own model gives
each quadrant cell 6 `dqce[j]` sub-slots (`chipdb.py:2895-2911`), so a
4-instance test can legitimately never touch a 4th distinct physical host.
Confirming or refuting `81@(54,89)` needs a >=6-simultaneous, spine-distinct
design — exactly what P1.T29/T30 build next; left **ASSUMED** here rather
than spending more of this task's budget chasing it.

Two unrelated large diffs, `(55,86)` and `(55,85)` (one row south of the
DCE cluster), track the combinational CE logic itself, not clock
infrastructure — see `tiletypes-138c.json` for the full residual list.

## Comparison to 25A / Verdict for `S9`

The 138C tile-type search values are **identical** to 25A's (80/81/84/85),
and their physical arrangement (single central-row cluster, two
adjacent-column pairs) is structurally identical too. The open question the
existing code's comment worried about — a mismatched search silently
attaching a DQCE block to the wrong cell — is **not observed**: 3 of 4
cells are confirmed live at the exact positions the current search already
finds; the 4th is unconfirmed-but-unrefuted. `P1.T29` can key the 138C
per-device DCE cell table off this artifact's `tiletypes-138c.json` without
re-deriving it.
