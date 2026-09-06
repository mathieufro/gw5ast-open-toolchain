# GW5AST-138C `PLL` sweep campaign, batch C — the `DYN` modes and a loaded `CLKOUT1` (`P1.T42`)

The slug stays `plla` for path stability; the primitive swept below is **`PLL`**
(`D96` — this device has no `PLLA`).

Shape: `fuzz/gw5ast138c/shapes/clocking_pll.py`, invoked with
`FUZZ_PLL_AXIS=dyn,odiv1l` — the reuse contract `P1.T23` wrote into that file's
docstring. Two axis kinds were added to that file to express what a single
`#(...)` parameter cannot; both are additive, and
`test_pll_sweep_batches_a_and_b_regenerate_byte_identically` asserts every
batch-A and batch-B point still renders the bytes it was measured from.

Batch: `p1-pll-sweep-c`, **12 oracle runs**, level `E1`, IDE 1.9.12.03 Standard.
Machine-readable attribution: **`sweep-c-138c.json`**.

The blueprint budgeted 14 runs; the owner's cap for a clocking batch is 12, and
the batch is complete at 12 — five `DYN` modes against one baseline, and six
`ODIV1L` divider values. The campaign total is therefore **64**, not 68.

## 1. What was swept

One hard `PLL` pinned to `PLL_L[0]` (tiles `(27,1)`, `(27,2)`, `(27,3)`, ttyps
74/75/76, `shortval[35]`), exactly as batches A and B, at batch B's charge-pump
operating point (`FCLKIN` 100 MHz, `IDIV` 4, `FBDIV` 18, `MDIV` 2 →
`Fpfd` 25 MHz, `FVCO` 900 MHz) so no point of either axis moves the VCO and a
moved bit can only be the swept thing's own.

| axis | swept | values | baseline | points |
|---|---|---|---|---|
| `DYN` | *which* `DYN_*` boolean is `"TRUE"` | `DYN_IDIV_SEL`, `DYN_FBDIV_SEL`, `DYN_MDIV_SEL`, `DYN_ODIV0_SEL`, `DYN_DPA_EN` | none of them | 6 |
| `ODIV1L` | `ODIV1_SEL`, `CLKOUT1` **loaded** | 2, 4, 8, 16, 32, 64 | 8 | 6 |

`DYN_*` are independent booleans, so no single parameter's value set covers
them: the axis's value is the mode itself, and the baseline carries all five
`"FALSE"`. A point therefore still differs from its own baseline in exactly
one key, which is the property attribution rests on
(`test_pll_sweep_batch_c_dyn_axis_turns_on_exactly_one_mode`).

`ODIV1L` is batch B's `ODIV1` axis with `CLKOUT1` driving a second fabric flop
and `ENCLK1` tied high — the shape variant `sweep-b-138c.md` §3.1 asked for.
The second flop feeds the existing `dout`, so the module's **port list** is
byte-identical to every other axis's and a moved bit still cannot be a
connectivity artefact
(`test_pll_sweep_batch_c_odiv1l_axis_loads_clkout1`).

## 2. Attribution — 12 of 12 points

| points | axis | moved bits | tiles | resolves to |
|---|---|---|---|---|
| `dyn_none` | `DYN` | 0 | — | the baseline: no mode, no fuse |
| `dyn_idiv` | `DYN` | 235 | (27,1) (27,2) (27,3) | `A_DYN_IDIV_SEL` (**125**), value 50 — agrees with `P1.T22` |
| `dyn_fbdiv` | `DYN` | 319 | (27,1) (27,2) (27,3) | attribute id **124**, value 50 — **first sighting, unnamed in `pll_attrids`** |
| `dyn_mdiv` | `DYN` | 1 | (27,1) | attribute id **131**, value 50 — **first sighting, unnamed in `pll_attrids`** |
| `dyn_odiv0` | `DYN` | 1 | (27,1) | `A_DYN_ODIV0_SEL` (**132**), value 50 — agrees with `P1.T22` |
| `dyn_dpa` | `DYN` | 1 | (27,3) | `A_DYN_DPA_EN` (**190**), value 50 — first sighting of a *named* id |
| `odiv1l_008` | `ODIV1L` | 0 | — | the axis baseline |
| `odiv1l_002` … `odiv1l_064` (5) | `ODIV1L` | 1 … 3 | (27,1) | `A_ODIV1_SEL` (**115**) alone |

No pump co-mover (`FLDCOUNT`, `KVCO`, `A_ICP_SEL`, `A_LPF_RES_SEL`) moved on
any point of either axis, which is what a pump that depends only on
`(Fpfd, FVCO)` must do when neither axis moves either.

## 3. Findings

1. **`ODIV1_SEL` writes its fuse once `CLKOUT1` is loaded — MEASURED, five
   points.** Batch B measured `A_ODIV1_SEL` (115) written at **none** of six
   divider values with `CLKOUT1` enabled but unconnected, and recorded the
   cause as the missing load. With the load in place the same six values write
   `A_ODIV1_SEL` and nothing else at all five non-baseline points. The vendor
   programs an output divider only for an output that has a consumer;
   `CLKOUT1_EN` alone is not enough. `sweep-b-138c.md` §3.1 is closed.
2. **Attribute ids 124 and 131 are `A_DYN_FBDIV_SEL` and `A_DYN_MDIV_SEL`.**
   Both sat in this device's `.fse` attribute table with **no name**
   (`attrids-138c.tsv` lists 124 as unnamed and hypothesises exactly this
   family). Setting `DYN_FBDIV_SEL "TRUE"` — one parameter, against a baseline
   identical in every other key — moves 319 bits, all of them in
   `shortval[35]` rows keyed by `(124, 50)`; `DYN_MDIV_SEL "TRUE"` moves one
   bit keyed by `(131, 50)`. `pll_attrvals['TRUE'] == 50`, so the attribute is
   the boolean itself, exactly as for the two ids `P1.T22` named.
3. **The `DYN_IDIV`/`DYN_FBDIV` selects are site-wide, the others are not.**
   The two input-side selects move bits in all three tiles of the site (235
   and 319); `DYN_MDIV`/`DYN_ODIV0` move one bit in the anchor tile and
   `DYN_DPA_EN` one bit in the site's third tile. The dynamic input dividers
   are re-encoded across the whole site, which is why they are the expensive
   ones to model.
4. **Open-flow gap (new, recorded not fixed).** `gowin_pack`'s GW5A `PLLA`
   attribute builder is marked `# XXX only static`: it hardcodes
   `A_DYN_DPA_EN`/`A_DYN_ICP_SEL`/`A_DYN_LPF_SEL` to `FALSE` and never reads
   `A_DYN_IDIV_SEL`, `A_DYN_FBDIV_SEL`, `A_DYN_MDIV_SEL` or `A_DYN_ODIV0_SEL`
   from the cell at all, so an open bitstream built from a dynamically
   reconfigured `PLL` silently loses its mode. `E1` cannot see this — it
   compares cells, attributes and placement, never bits — and all twelve rows
   are `E1` `ok`. Decoding both bitstreams of all five `DYN` points confirms
   it: the vendor carries 46 site attributes and the open flow 50, and the one
   missing from the open half is always exactly the mode's own
   (125 / 124 / 131 / 132 / 190). The same decode found two further deltas,
   constant across the axis and so invisible to its own attribution: the open
   flow writes `A_ODIV1_SEL` … `A_ODIV6_SEL` = 120 on disabled outputs, and
   the vendor writes attribute 211 = 2 where the open flow writes nothing.
   The fix belongs to the task that owns `apycula/*.py`; `P1.T42` may not
   change it (blueprint, *Must NOT change*). All of it is recorded in
   `openflow-gap-138c.md` as gap 5, with the ids for `A_DYN_FBDIV_SEL` (124)
   and `A_DYN_MDIV_SEL` (131) that `pll_attrids` still needs.

5. **Batches A and B carry no `mask_sha256`.** The field is `equiv`'s, and
   their open halves aborted before `equiv` ran, so the blueprint's
   "`mask_sha256` identical to batch A's" cannot be checked against a value
   batch A does not have. It is checked against the mask **file** instead —
   `fuzz/gw5ast138c/dontcare.mask`, sha256 `59147bfc…7a1ec0`, which is what
   every batch-C row carries — and against batch A as well if those rows ever
   gain the field (`_assert_mask_is_the_campaign_mask`).

## 4. Runs and artefacts

| item | value |
|---|---|
| batch | `p1-pll-sweep-c`, `BATCH_COMPLETE p1-pll-sweep-c runs=12 ok=12 diff=0 aborted=0` |
| watchdog | `WATCHDOG_ARMED batch=p1-pll-sweep-c stall=5min poll=100s` and `WATCHDOG_COMPLETE … (clean exit)` |
| verdicts | 12/12 `ok` at `E1`, `cells`/`attrs`/`conns` all 0, `decode_check {c1: ok, c2: ok}` — the first PLL batch whose open half completes (`openflow-gap-138c.md`'s four gaps closed by `P1.T41`) |
| per-run cost | 2 min 12 s measured on run 0; 25 min for the batch |
| rows | 12 appended to `evidence/plla/runs.jsonl` |
| oracle-run budget | 12 charged; `clocking-runs.tsv` row `p1-pll-sweep-c` |
| artefacts | `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/sweep-c/<run_id>/` |
| analyser | `gen_sweep_c_138c.py` → `sweep-c-138c.json` |
