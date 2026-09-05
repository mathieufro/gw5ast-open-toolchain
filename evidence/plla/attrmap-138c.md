# GW5AST-138C `PLL` attrid/attrval map (`P1.T22`)

The slug stays `plla` for path stability; the primitive named in every row
below is **`PLL`** (`D96` -- this device has no `PLLA`).

## 1. What was measured

Batch `p1-pll-attrmap`, shape `fuzz/gw5ast138c/shapes/clocking_pll_attrmap.py`,
**12 oracle runs**, level `E1`, IDE 1.9.12.03 Standard.

One hard `PLL` pinned to `PLL_L[0]` in every run (`INS_LOC "dut_pll"
PLL_L[0]`), so the site's three tiles -- `(row 27, col 1/2/3)`, ttyps
`74/75/76`, `shortval[35]` -- are the whole comparison scope. Exactly **one**
`#(...)` parameter differs from the baseline in each run; the port list is
byte-identical across all twelve, so a moved bit cannot be a connectivity
artefact.

Baseline, inside every bound of the `P1.T20` five-tuple and DS1239E Table
3-18's `FPFDMIN 19` / `FPFDMAX 81.25`:

    FCLKIN 100 MHz, IDIV_SEL 2, FBDIV_SEL 2, MDIV_SEL 13, ODIV0_SEL 8
    Fpfd 50 MHz -> Fclkfb 100 MHz -> FVCO 1300 MHz -> CLKOUT0 162.5 MHz

The baseline deliberately sits at `FVCOMAX`: the VCO band is only a factor of
two wide, so a mid-band baseline would make every single integer divider step
illegal in one direction.

## 2. The census (no oracle needed)

`logicinfo['PLL']` of the shipped 138C `.fse` against `apycula/attrids.py`'s
`pll_attrids`, the three counts `P1.T22` asks for:

| count | before this task | after |
|---|---|---|
| ids present in both | 172 | **174** |
| ids in the `.fse` with no name | 20 | **18** |
| names with no `.fse` id | 20 | **20** |

`logicinfo['PLL']` has **2531** rows and **192** distinct attribute ids on the
138C, against 2514 rows / 175 ids on the 25A. The two tables are **not**
identical, so the 138C's attribute space is a real superset of the 25A's in
17 ids -- but it lives in exactly the same id namespace (`0..213`) that
`pll_attrids` addresses, which is the thing `P1.T22` set out to confirm.

The 20 **names with no `.fse` id** are all rPLL-era names (`IDIV`, `ODIV`,
`INSEL`, `PHASE`, `SDIV`, `LPR`, `ICPSEL`, `GMC*`, ...). They are unused on
this device rather than colliding with it: none of their ids appears in the
138C table, so there is no PR #423-class rename hazard here. Nothing was
renamed, reordered or renumbered.

Per-tile id census (all twelve sites): `attrids-138c.tsv`.

## 3. The attribution (12 oracle runs)

Every moved bit was looked up in its tile's `shortval[35]` table; the positive
attrvals of every matching row were mapped back through `logicinfo['PLL']` to
`(attr_id, value)` and through `pll_attrids` to a name.

| point | parameter changed | moved bits | resolves to | verified |
|---|---|---|---|---|
| `p00_baseline` | -- (reference) | 0 | -- | -- |
| `p01_idiv3` | `IDIV_SEL` 2 -> 3 | 2 | `A_IDIV_SEL` (109) | yes |
| `p02_idiv4` | `IDIV_SEL` 2 -> 4 | 2 | `A_IDIV_SEL` (109), `FLDCOUNT` (16) | yes |
| `p03_fbdiv1` | `FBDIV_SEL` 2 -> 1 | 4 | `A_FBDIV_SEL` (110), `A_ICP_SEL` (111) | yes |
| `p04_mdiv7` | `MDIV_SEL` 13 -> 7 | 4 | `A_MDIV_SEL` (113), `A_ICP_SEL` (111) | yes |
| `p05_mdiv10` | `MDIV_SEL` 13 -> 10 | 5 | `A_MDIV_SEL` (113), `A_ICP_SEL` (111) | yes |
| `p06_odiv0_4` | `ODIV0_SEL` 8 -> 4 | 1 | `A_ODIV0_SEL` (114) | yes |
| `p07_odiv0_16` | `ODIV0_SEL` 8 -> 16 | 1 | `A_ODIV0_SEL` (114) | yes |
| `p08_odiv0_64` | `ODIV0_SEL` 8 -> 64 | 3 | `A_ODIV0_SEL` (114) | yes |
| `p09_dyn_idiv` | `DYN_IDIV_SEL` -> `TRUE` | 235 | attr **125**, val 50 -- **no name** | yes (new name) |
| `p10_dyn_odiv0` | `DYN_ODIV0_SEL` -> `TRUE` | 1 | attr **132**, val 50 -- **no name** | yes (new name) |
| `p11_clkout1_en` | `CLKOUT1_EN` -> `TRUE` | 1 | `A_CLKOUT1_EN` (154) | yes |

**11 of 11 non-baseline points attributed**; 9 of them land on an attribute
`pll_attrids` already names, 2 on ids it did not.

The co-movers are not noise and are not failures: `FLDCOUNT` and `A_ICP_SEL`
are the charge-pump/loop-filter attributes that the vendor recomputes *because*
the VCO moved (`get_pll_pump`'s `fref`/`fvco` inputs), so a divider change that
also moves them is the expected shape. Only `p01`, `p06`, `p07`, `p08`, `p11`
change a divider without crossing a pump threshold, and those move the one
attribute and nothing else.

## 4. Verified `(attr, value) -> fuses` rows

Full bit lists (per tile, `set` and `cleared`) are in `attrmap-138c.json`,
field `runs[].moved`. The attribute-level summary:

| attr id | name | tile | value observed | evidence |
|---|---|---|---|---|
| 16 | `FLDCOUNT` | 27,1 | 16..240 step 32 | `p02` |
| 109 | `A_IDIV_SEL` | 27,1 | 1..63 | `p01`, `p02` |
| 110 | `A_FBDIV_SEL` | 27,1 | 1..63 odd | `p03` |
| 111 | `A_ICP_SEL` | 27,1 | 20..640 | `p03`, `p04`, `p05` |
| 113 | `A_MDIV_SEL` | 27,1 | 1..127 | `p04`, `p05` |
| 114 | `A_ODIV0_SEL` | 27,1 | 1..124 | `p06`, `p07`, `p08` |
| 125 | `A_DYN_IDIV_SEL` **(new)** | 27,1 | 50 = `TRUE` | `p09` |
| 132 | `A_DYN_ODIV0_SEL` **(new)** | 27,1 | 50 = `TRUE` | `p10` |
| 154 | `A_CLKOUT1_EN` | 27,2 | 50 = `TRUE` | `p11` |

Two names were appended to `apycula/attrids.py` -- **append only**, no
existing entry renamed, renumbered or reordered:

    'A_DYN_IDIV_SEL':  125,
    'A_DYN_ODIV0_SEL': 132,

## 5. Findings, named rather than ignored

1. **18 `.fse` attribute ids still have no name.** Every one is listed in
   `attrids-138c.tsv` with a `reason` column. Five (107, 108, 206, 210, 211)
   are unnamed on the **25A too** -- a pre-existing `pll_attrids` gap, not a
   138C matter. Thirteen (124, 131, 133-138, 141, 144, 147, 150, 205) exist
   only on the 138C. Twelve of those thirteen carry the single boolean value
   50 (`TRUE`) and sit adjacent to the two ids this task *measured* to be
   `A_DYN_IDIV_SEL` / `A_DYN_ODIV0_SEL`, so "the rest of the `DYN_*_SEL`
   family that the 25A `PLLA` has no ports for (`D96`)" is the obvious
   hypothesis -- recorded as a hypothesis, **not** appended to `attrids.py`,
   because it is not measured. 205 (value 49) has no hypothesis at all.
2. **`GW5AST_138C` still has no `get_pll_freq_R` / `get_pll_coeffs`**, so
   `get_pll_pump` would raise on a 138C `PLL`. Those are loop-filter constants
   with no datasheet source; `A_ICP_SEL` and `FLDCOUNT` values observed here
   (§4) are the derivation path, and they belong to the task that lands
   `get_PLL_fuses`.
3. **`get_pll_slot_fuses` still addresses pseudo-ttyp 1024**, which does not
   exist on this device (`P1.T17`). The fuses measured here are ordinary tile
   fuses of the site's three tiles.

## 6. Runs and artefacts

| item | value |
|---|---|
| batch | `p1-pll-attrmap`, `runs=12 ok=0 diff=0 aborted=12`, `WATCHDOG_COMPLETE` |
| verdict `aborted` | the **open** half only; the vendor half completed and produced `run.fs` in all 12 |
| artefacts | `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/attrmap/<run_id>/` (1.4 GB, retained -- every row in `runs.jsonl` points at a live path with its sha256, `D99`) |
| rows | 12 appended to `evidence/plla/runs.jsonl` (24 total in this slug) |
| oracle-run budget | 12 charged; cumulative **53** of 290 |
| chipdb | `GW5AST-138C.msgpack.xz` `b2a9d409...` -- rebuilt from `clocking/plla-138c` and byte-identical to the hash `P1.T18`-`T20` recorded |
| analyser | `gen_attrmap_138c.py` (census + attribution), output `attrmap-138c.json` |
