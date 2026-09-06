# GW5AST-138C `PLL` sweep campaign, batch A — `IDIV` / `FBDIV` (`P1.T23`)

The slug stays `plla` for path stability; the primitive swept below is **`PLL`**
(`D96` — this device has no `PLLA`).

Shape: `fuzz/gw5ast138c/shapes/clocking_pll.py` (authored here, reused unedited
by `P1.T41`-`T43` through `$FUZZ_PLL_AXIS`).
Batch: `p1-pll-sweep-a`, **20 oracle runs**, level `E1`, IDE 1.9.12.03 Standard.
Machine-readable attribution: **`sweep-a-138c.json`**; the blockers on the open
half: **`openflow-gap-138c.md`**.

---

## 1. What was swept, and why the two axes sit at different `FCLKIN`

One hard `PLL` pinned to `PLL_L[0]` (`INS_LOC "dut_pll" PLL_L[0]`; tiles
`(27,1)`, `(27,2)`, `(27,3)`, ttyps 74/75/76, `shortval[35]`), `CLKIN` from a
bank-5 IO pin, `CLKOUT0` clocking a fabric register. Exactly one `#(...)`
parameter differs between a point and **its own axis baseline**; the port list
is byte-identical across all twenty runs.

| axis | `FCLKIN` | fixed | swept | values | baseline | points |
|---|---|---|---|---|---|---|
| `IDIV` | 400 MHz | `FBDIV 2`, `MDIV 14`, `ODIV0 8` | `IDIV_SEL` | 9 .. 17 | 13 | 9 |
| `FBDIV` | 100 MHz | `IDIV 4`, `MDIV 2`, `ODIV0 8` | `FBDIV_SEL` | 13 .. 23 | 18 | 11 |

Every point satisfies all four DS1239E Table 3-18 bounds at once — `Fpfd` in
[19, 81.25], `FVCO` in [650, 1300] (`S7`, `P1.T21`), `CLKOUT0` in
[5.079, 1000], `FCLKIN` <= `FINMAX` 800 — asserted at generation time by
`test_pll_sweep_shape_points_are_inside_every_datasheet_band`.

**Why the `IDIV` axis runs at 400 MHz.** The VCO band is exactly a factor of
two wide, so a one-parameter sweep of a divider `D` can only cover
`D in [n, 2n]` — at most `n + 1` values. For `IDIV` the `Fpfd >= 19 MHz` floor
then forces `FCLKIN >= 38 n`, so **nine `IDIV` points are impossible below
342 MHz**. `FCLKIN = 400 MHz` is the smallest round value that admits nine and
is well inside `FINMAX`. The vendor accepted it: all nine `IDIV` runs produced
a `run.fs` of the usual 34,668,941 B. The `FBDIV` axis does not move `Fpfd` at
all and stays at the familiar 100 MHz.

Sweep order is the full Gray sequence restricted to each axis's legal set, with
the axis baseline emitted first (`spec-harness.md` §7).

## 2. Results — the E1 verdict and the attributed fuses, per point

`E1` was **requested** on every row; the recorded verdict is `aborted` on all
twenty because the **open half cannot run at all** on this device
(`openflow-gap-138c.md`): `nextpnr` exits 125 on
`Unknown placement macro PLL_L`, and behind that on cell type `PLL` having no
bel, and behind that `gowin_pack` has no `get_PLL_fuses` and no charge-pump
constants for this part. The **vendor half completed in all twenty**, which is
what batch A measures. This is the same admissible shape `P1.T22` landed.

`moved` = bits differing from the axis baseline inside the site's three tiles.
`resolves to` = the names those bits' `shortval[35]` rows carry, through
`logicinfo['PLL']` and `pll_attrids` — the identical procedure `P1.T22` used.

| point | `IDIV`/`FBDIV` | `FVCO` MHz | E1 verdict | moved | tile | resolves to | = `P1.T22` |
|---|---|---|---|---|---|---|---|
| `idiv_013` | 13 | 861.54 | `aborted` (open) | 0 | — | — (axis baseline) | yes |
| `idiv_012` | 12 | 933.33 | `aborted` (open) | 3 | 27,1 | `A_IDIV_SEL` | yes |
| `idiv_015` | 15 | 746.67 | `aborted` (open) | 2 | 27,1 | `A_IDIV_SEL`, `FLDCOUNT` | yes |
| `idiv_014` | 14 | 800.00 | `aborted` (open) | 2 | 27,1 | `A_IDIV_SEL`, `FLDCOUNT` | yes |
| `idiv_010` | 10 | 1120.00 | `aborted` (open) | 2 | 27,1 | `A_IDIV_SEL` | yes |
| `idiv_011` | 11 | 1018.18 | `aborted` (open) | 2 | 27,1 | `A_IDIV_SEL` | yes |
| `idiv_009` | 9 | 1244.44 | `aborted` (open) | 1 | 27,1 | `A_IDIV_SEL` | yes |
| `idiv_017` | 17 | 658.82 | `aborted` (open) | 4 | 27,1 | `A_IDIV_SEL`, `FLDCOUNT` | yes |
| `idiv_016` | 16 | 700.00 | `aborted` (open) | 3 | 27,1 | `A_IDIV_SEL`, `FLDCOUNT` | yes |
| `fbdiv_018` | 18 | 900.00 | `aborted` (open) | 0 | — | — (axis baseline) | yes |
| `fbdiv_013` | 13 | 650.00 | `aborted` (open) | 6 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |
| `fbdiv_015` | 15 | 750.00 | `aborted` (open) | 7 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |
| `fbdiv_014` | 14 | 700.00 | `aborted` (open) | 6 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |
| `fbdiv_020` | 20 | 1000.00 | `aborted` (open) | 7 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL`, `A_LPF_RES_SEL` | yes |
| `fbdiv_021` | 21 | 1050.00 | `aborted` (open) | 4 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL`, `A_LPF_RES_SEL` | yes |
| `fbdiv_023` | 23 | 1150.00 | `aborted` (open) | 5 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL`, `A_LPF_RES_SEL` | yes |
| `fbdiv_022` | 22 | 1100.00 | `aborted` (open) | 3 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL`, `A_LPF_RES_SEL` | yes |
| `fbdiv_019` | 19 | 950.00 | `aborted` (open) | 3 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |
| `fbdiv_017` | 17 | 850.00 | `aborted` (open) | 5 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |
| `fbdiv_016` | 16 | 800.00 | `aborted` (open) | 7 | 27,1 | `A_FBDIV_SEL`, `A_ICP_SEL` | yes |

**20 of 20 points agree with `P1.T22`'s attrmap.** Every `IDIV_SEL` step moves
attribute **109** `A_IDIV_SEL` and every `FBDIV_SEL` step moves attribute
**110** `A_FBDIV_SEL`, both in tile `(27, 1)` — exactly the `(attr, tile)` pairs
`attrmap-138c.md` §4 recorded, now over 9 and 11 fresh divider values instead
of two and one. No bit moved in `(27,2)` or `(27,3)` on any point of either
axis, and no attribute outside the divider + charge-pump set ever appeared.

## 3. Findings

1. **`A_LPF_RES_SEL` (attribute 112) — FIRST SIGHTING.** `P1.T22`'s twelve
   points never crossed a loop-filter-resistor threshold, so its attrmap has no
   `A_LPF_RES_SEL` row. Batch A's four highest-`FVCO` `FBDIV` points
   (`FVCO` 1000 .. 1150 MHz) move it. This is not a discrepancy: `FLDCOUNT`
   (16), `KVCO` (28), `A_ICP_SEL` (111) and `A_LPF_RES_SEL` (112) are exactly
   the tuple `GW5A.get_pll_attrvals` derives from `get_pll_pump`
   (`gowin_pack.py:5586-5590`), so a divider step that crosses a pump threshold
   moves them by construction. It does locate the `r_idx` boundary for this
   part between `FVCO` 950 and 1000 MHz at `Fpfd` 25 MHz — the first measured
   point of the pump curve `openflow-gap-138c.md` §4 says a follow-up campaign
   must fit.
2. **The `Fpfd` floor is what makes a wide `IDIV` sweep expensive**, not the
   VCO band: nine `IDIV` points need `FCLKIN >= 342 MHz`. `P1.T41`'s `ODIV`
   axis has no such constraint (`ODIV` does not touch the VCO) and its `MDIV`
   axis behaves like `FBDIV`.
3. **The open half is blocked by four independent gaps**, one of which needs
   its own oracle campaign — see `openflow-gap-138c.md`. Batch A's twenty
   vendor `.fs` are retained precisely because they are the first twenty
   samples that campaign needs.
4. **Provenance nit, recorded not fixed:** `openflow.provenance` stamps
   `nextpnr_sha` from the `nextpnr` submodule checkout's HEAD (`8566c51d`),
   not from the tree the installed binary was built from (`527c7169`). Every
   row of this batch carries `8566c51d` for that reason. Unrelated to `P1.T23`.

## 4. Runs and artefacts

| item | value |
|---|---|
| batch | `p1-pll-sweep-a`, `BATCH_COMPLETE p1-pll-sweep-a runs=20 ok=0 diff=0 aborted=20` |
| watchdog | `WATCHDOG_ARMED` (stall 5 min, poll 100 s) and `WATCHDOG_COMPLETE ... (clean exit)` |
| verdict `aborted` | the **open** half only; the vendor half produced `run.fs` (34,668,941 B) in all 20 |
| rows | 20 appended to `evidence/plla/runs.jsonl` (44 total in this slug) |
| oracle-run budget | 20 charged; `clocking-runs.tsv` row `p1-pll-sweep-a` |
| artefacts | `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/sweep-a/<run_id>/` (2.4 GB, **retained** — every row points at a live path with its sha256, `D99`) |
| chipdb | `GW5AST-138C.msgpack.xz` `89922831…` and `chipdb-GW5AST-138C.bin` `e95f3594…`, built from this branch and pinned with `--chipdb`; the installed pair was not touched |
| analyser | `gen_sweep_a_138c.py` (attribution + the `P1.T22` cross-check) -> `sweep-a-138c.json` |
| row merge | `merge_sweep_rows.py` (rewrites `sweep` to `{axis, <param>}`; reused by `P1.T41`-`T43`) |
