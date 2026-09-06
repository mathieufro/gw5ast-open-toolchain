# GW5AST-138C `PLL` sweep campaign, batch D — one placement per site (`P1.T43`)

The slug stays `plla` for path stability; the primitive swept below is **`PLL`**
(`D96` — this device has no `PLLA`).

Shape: `fuzz/gw5ast138c/shapes/clocking_pll.py`, invoked with
`FUZZ_PLL_AXIS=site` — the reuse contract `P1.T23` wrote into that file's
docstring. The `SITE` axis sweeps the **placement** and no parameter at all:
every point renders byte-identical Verilog at `P1.T39`'s reference operating
point and differs only in its `INS_LOC`
(`test_pll_sweep_batch_d_is_the_t39_reference_point_on_every_site`).

Batch: `p1-pll-sweep-d`, **12 oracle runs**, level `E1`, IDE 1.9.12.03 Standard.
Machine-readable decode: **`sites-e1-138c.json`**.

The blueprint budgeted 14 runs (12 sites + 2 baselines); the owner's cap for a
clocking batch is 12, and the batch is complete at 12 — the axis's own baseline
is `PLL_L[0]`, which is one of the twelve, so a separate baseline run would
measure a design already in the batch. With this batch the campaign total
reaches **64**.

## 1. The operating point

`examples/pll/GW5AST-138C.vh` (`P1.T39`), unchanged: `FCLKIN` 50 MHz,
`IDIV` 1, `FBDIV` 1, `MDIV` 16, `ODIV0` 8 → `Fpfd` 50 MHz, `FVCO` 800 MHz,
`CLKOUT0` 100 MHz. `CLKIN` comes from `AA9` (bank 5) and `CLKOUT0` clocks one
fabric flop, exactly as in batches A-C.

`E0`/`E1` scope is every site's three tiles — 36 in all — so a run placed
anywhere in the die is compared inside its own site rather than falling
outside the scope.

## 2. Per-site result — 12 of 12

Anchor and tiles are `P1.T17`'s (`sites-138c.md` §3); `attrs` is the number of
`shortval[35]` attributes the site's three tiles decode to.

| site | anchor (row, col) | tiles | ttyps | attrs | same as `PLL_L[0]` | `E1` |
|---|---|---|---|---|---|---|
| `PLL_L[0]` | (27, 1) | (27,1) (27,2) (27,3) | 74 / 75 / 76 | 45 | reference | **ok** |
| `PLL_L[1]` | (45, 0) | (45,0) (45,1) (45,2) | **268** / 75 / 76 | 46 | + `A_VR_EN` | **ok** |
| `PLL_L[2]` | (63, 0) | (63,0) (63,1) (63,2) | **270** / 75 / 76 | 46 | + `A_VR_EN` | **ok** |
| `PLL_L[3]` | (81, 1) | (81,1) (81,2) (81,3) | 74 / 75 / 76 | 45 | yes | **ok** |
| `PLL_R[0]` | (27, 177) | (27,177) (27,178) (27,179) | 77 / 78 / 79 | 45 | yes | **ok** |
| `PLL_R[1]` | (45, 178) | (45,178) (45,179) (45,180) | 77 / 78 / 79 | 45 | yes | **ok** |
| `PLL_R[2]` | (63, 178) | (63,178) (63,179) (63,180) | 77 / 78 / 79 | 45 | yes | **ok** |
| `PLL_R[3]` | (81, 177) | (81,177) (81,178) (81,179) | 77 / 78 / 79 | 45 | yes | **ok** |
| `PLL_B[0]` | (108, 28) | (108,28) (108,29) (108,30) | 182 / 183 / 184 | 45 | yes | **ok** |
| `PLL_B[1]` | (108, 32) | (108,32) (108,33) (108,34) | 182 / 183 / 184 | 45 | yes | **ok** |
| `PLL_B[2]` | (108, 146) | (108,146) (108,147) (108,148) | 182 / 183 / 184 | 45 | yes | **ok** |
| `PLL_B[3]` | (108, 150) | (108,150) (108,151) (108,152) | 182 / 183 / 184 | 45 | yes | **ok** |

Every row is `verdict: ok` at `E1` with `cells` / `attrs` / `conns` all `0` and
`decode_check {c1: ok, c2: ok}`, and every row carries both a vendor and an
open `.fs`. No site refused to place, in either flow.

## 3. Findings

1. **All twelve sites are real, and the same design builds on each of them —
   through both flows.** `P1.T19` established the twelve-site bijection one
   vendor trace at a time; this batch is the first time the *same* design is
   built at each site and closed against the open flow there. Twelve `INS_LOC`
   values, twelve placements, twelve `E1` `ok` rows.
2. **The attribute encoding is per-site-independent.** Ten of the twelve sites
   decode to an identical 45-attribute map — same attribute ids, same values —
   at three different tile-type triples (74/75/76 left, 77/78/79 right,
   182/183/184 bottom). The encoding is a property of the `PLL`, not of where
   it sits.
3. **`PLL_L[1]` and `PLL_L[2]` carry one attribute more: `A_VR_EN` = 2
   (`DISABLE`).** These are exactly the two sites whose anchor sits in column
   **0** rather than column 1, and whose anchor tile type is unique on the die
   (268 and 270, against 74 for `PLL_L[0]`/`PLL_L[3]`). Their other 45
   attributes are identical to the reference. The internal voltage regulator
   is explicitly disabled on the two left-edge sites and left unprogrammed
   elsewhere; both flows agree, and the difference is a property of the site,
   which is precisely what a placement sweep is for.
4. **Nothing in `sites-138c.md` changed and nothing in the `P1.T39` header
   changed.** Every anchor, tile triple and ttyp reproduces `P1.T17`/`P1.T19`
   exactly, and the reference operating point placed and closed `E1` at all
   twelve sites, so no site coordinate and no parameter range moved. The site
   table is `P1.T17`/`P1.T19`'s to edit and was not edited.

## 4. Runs and artefacts

| item | value |
|---|---|
| batch | `p1-pll-sweep-d`, `BATCH_COMPLETE p1-pll-sweep-d runs=12 ok=12 diff=0 aborted=0` |
| watchdog | `WATCHDOG_ARMED batch=p1-pll-sweep-d stall=5min poll=100s` and `WATCHDOG_COMPLETE … (clean exit)` |
| per-run cost | 1 min 30 s – 2 min 32 s; 24 min for the batch |
| rows | 12 appended to `evidence/plla/runs.jsonl` |
| oracle-run budget | 12 charged; `clocking-runs.tsv` row `p1-pll-sweep-d`, cumulative 216 |
| campaign | batches A (20) + B (20) + C (12) + D (12) = **64** sweep runs |
| artefacts | `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/sweep-d/<run_id>/` |
| analyser | `gen_sites_e1_138c.py` → `sites-e1-138c.json` |
