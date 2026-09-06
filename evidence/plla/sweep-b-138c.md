# GW5AST-138C `PLL` sweep campaign, batch B — `ODIV0` / `ODIV1` / `MDIV` (`P1.T41`)

The slug stays `plla` for path stability; the primitive swept below is **`PLL`**
(`D96` — this device has no `PLLA`).

Shape: `fuzz/gw5ast138c/shapes/clocking_pll.py`, invoked with
`FUZZ_PLL_AXIS=odiv0,odiv1,mdiv` — the reuse contract `P1.T23` wrote into that
file's docstring. The three axes it names were not defined there yet; adding
them is additive (`DEFAULT_AXES` still reads `idiv,fbdiv`, so batch A's twenty
points regenerate byte-identically) and is the coordination note this task
leaves `P1.T23`.

Batch: `p1-pll-sweep-b`, **20 oracle runs**, level `E1`, IDE 1.9.12.03 Standard.
Machine-readable attribution: **`sweep-b-138c.json`**.

## 1. What was swept

One hard `PLL` pinned to `PLL_L[0]` (tiles `(27,1)`, `(27,2)`, `(27,3)`, ttyps
74/75/76, `shortval[35]`), exactly as batch A. Exactly one `#(...)` parameter
differs between a point and **its own axis baseline**.

| axis | `FCLKIN` | fixed | swept | values | baseline | points |
|---|---|---|---|---|---|---|
| `ODIV0` | 100 MHz | `IDIV 4`, `FBDIV 18`, `MDIV 2` (`FVCO` 900) | `ODIV0_SEL` | 1, 2, 3, 4, 8, 16, 64 | 8 | 7 |
| `ODIV1` | 100 MHz | as `ODIV0` + `CLKOUT1_EN "TRUE"` | `ODIV1_SEL` | 2, 4, 8, 16, 32, 64 | 8 | 6 |
| `MDIV` | 100 MHz | `IDIV 4`, `FBDIV 1` (`FVCO` = 25·`MDIV`) | `MDIV_SEL` | 26, 30, 34, 36, 40, 46, 52 | 36 | 7 |

Every point satisfies all four DS1239E Table 3-18 bounds at once, asserted at
generation time by `test_pll_sweep_batch_b_axes_are_inside_every_datasheet_band`.
`ODIV` divides after the VCO, so the two `ODIV` axes sit at one charge-pump
operating point throughout; the `MDIV` axis multiplies into the VCO exactly as
`FBDIV` does and is bounded only by the factor-of-two VCO band.

## 2. Attribution — 20 of 20 points

| points | axis | moved bits | resolves to | agrees with |
|---|---|---|---|---|
| `odiv0_001` … `odiv0_064` (6 non-baseline) | `ODIV0` | 1 … 3, tile (27,1) | `A_ODIV0_SEL` (**114**) alone | `P1.T22` `p06`-`p08` |
| `odiv1_002` … `odiv1_064` (5 non-baseline) | `ODIV1` | **0** | — (see §3) | first sighting |
| `mdiv_026` … `mdiv_052` (6 non-baseline) | `MDIV` | 4 … 7, tile (27,1) | `A_MDIV_SEL` (**113**) + the pump co-movers `A_ICP_SEL` (111) and, above `FVCO` 950 MHz, `A_LPF_RES_SEL` (112) | `P1.T22` `p04`-`p05` |

No bit moved in `(27,2)` or `(27,3)` on any point of any axis, and no attribute
outside the divider + charge-pump set ever appeared. Together with batch A the
`A_ODIV0_SEL` field is now exercised over 7 values, `A_MDIV_SEL` over 7 and the
pump over the whole legal `(Fpfd, FVCO)` region.

## 3. Findings

1. **`ODIV1_SEL` writes no fuse at all — MEASURED, six points.** With
   `CLKOUT1_EN "TRUE"` the vendor does write `A_CLKOUT1_EN` (154, value 50):
   the enable is in the bitstream of every `ODIV1` point and absent from every
   `ODIV0` point. `A_ODIV1_SEL` (115) is written at **none** of the six divider
   values. The cause is in the shape: `CLKOUT1` is left unconnected, so the
   output has no load and the vendor programs the enable without the divider.
   Attributing `A_ODIV1_SEL` needs a shape variant that loads `CLKOUT1` with a
   second flop — an RTL change `P1.T23` owns, recorded here as a coordination
   note rather than made here, because changing the port list would break the
   "byte-identical port list across every point of every axis" invariant batch
   A's twenty rows were measured under.
2. **The `A_LPF_RES_SEL` step sits between `FVCO` 950 and 1000 MHz at
   `Fpfd` 25 MHz** on the `MDIV` axis exactly as it does on batch A's `FBDIV`
   axis — two independent dividers reaching the same VCO frequency give the
   same pump, which is what a pump that depends only on `(Fpfd, FVCO)` must do.
   `pump-138c.md` turns that into the fitted table.
3. **The open half now completes.** Batch B's rows were produced before the
   four `openflow-gap-138c.md` gaps were closed, so they carry `aborted` on the
   open side like batch A's; the same design run afterwards closes `E1`
   (`p1-pll-e1`, §`pump-138c.md`).

## 4. Runs and artefacts

| item | value |
|---|---|
| batch | `p1-pll-sweep-b`, `BATCH_COMPLETE p1-pll-sweep-b runs=20 ok=0 diff=0 aborted=20` |
| watchdog | `WATCHDOG_ARMED batch=p1-pll-sweep-b stall=5min poll=100s` and `WATCHDOG_COMPLETE … (clean exit)` |
| verdict `aborted` | the **open** half only; the vendor half produced `run.fs` in all 20 |
| rows | 20 appended to `evidence/plla/runs.jsonl` |
| oracle-run budget | 20 charged; `clocking-runs.tsv` row `p1-pll-sweep-b`, cumulative 169 |
| artefacts | `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/sweep-b/<run_id>/` |
| analyser | `gen_sweep_b_138c.py` → `sweep-b-138c.json` |
