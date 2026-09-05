# GW5AST-138C HCLK topology — MEASURED (P1.T04)

Task: `blueprints/P1-clocking.md` P1.T04. Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`. Oracle: Gowin IDE **1.9.12.03
Standard, licensed** (`edu-provisional: false`). Grid: **109 rows x 182 cols**.
Consumed by P1.T05-P1.T08 (and P1.T14-T16); the 25A comparison column is the
baseline those tasks must not port blindly.

Two independent instruments agree, and each was calibrated against the 25A
before being trusted:

* **I1 — `.fse` table 48.** The HCLK cells are the cells whose *own* `wire`
  table carries table 48 (`apycula/chipdb.py:1509-1515`). Classifier: a cell
  with table 48, >= 90 rows in it, HCLK->GCLK gate sources `{25,27,28,29}`
  present, and **no** inter-HCLK (`>= 187`) source in the first band.
  *Calibration on GW5A-25A*: yields exactly **4** cells
  `{(0,64), (1,0), (35,91), (36,27)}` against the maintainer's
  `_gw5a_hclk_locs = {0:(0,64), 1:(36,27), 2:(1,0), 3:(34,91)}` — count 4/4,
  positions 3/4 exact, the fourth off by one row (35 vs 34, see *Open point*).
* **I2 — vendor presence diff.** The maintainer's own method: build a baseline
  with the primitive absent and builds with N instances present, then diff the
  bitstreams tile by tile (`fuzz/gw5ast138c/harness/attribute.py`
  `presence_diff`). Sweeping N = 1, 4, 8, 12, 16, 20, 24 CLKDIV lights up
  **exactly one new cell per group of four**, and the six cells it lights are
  exactly I1's six.

## 1. The six HCLK blocks (MEASURED)

`hclk_idx` below is the **recommended** numbering for
`_gw5a_hclk_locs['GW5AST-138C']`: sorted by `(row, col)`. The index is free —
it only scales apicula's synthetic wire names (`srcid + idx * 187`), the fuses
come from each cell's own table 48 — but it must then be used consistently by
T05-T08. The vendor's own allocation order is recorded separately in §3.

| hclk_idx | row | col | `.fse` ttyp | table-48 rows | die half (row < 54.5) | side | vendor fill order |
|---|---|---|---|---|---|---|---|
| 0 | 27 | 0 | 272 | 159 | top | left | 6th |
| 1 | 27 | 181 | 273 | 159 | top | right | 2nd |
| 2 | 81 | 0 | 275 | 165 | bottom | left | 5th |
| 3 | 81 | 181 | 276 | 165 | bottom | right | 3rd |
| 4 | 108 | 64 | 274 | 165 | bottom | bottom | 1st |
| 5 | 108 | 117 | 379 | 165 | bottom | bottom | 4th |

The six are mirror-symmetric about the die centre: the left/right pairs sit at
rows 27 and 81 (27 + 81 = 108 = rows - 1), the bottom pair at cols 64 and 117
(64 + 117 = 181 = cols - 1). **There is no HCLK block on the top edge** (no
cell in row 0 carries table 48), which is the sharpest structural difference
from the 25A.

## 2. Bel capacity (MEASURED, vendor-stated)

| Fact | Value | How measured |
|---|---|---|
| CLKDIV bels on the whole device | **24** | `ERROR (PA2017) : The number(25) of CLKDIV in the design exceeds the resource limit(24) of current device` (run `clkdiv25`) — 24 place cleanly (run `clkdiv24`) |
| HCLK blocks | **6** | 24 CLKDIV / 4 per block, and the presence diff lights exactly 6 distinct cells |
| CLKDIV per block | **4** | each +4 CLKDIV lights exactly one new cell (§3) |
| CLKDIV2 bels | NOT MEASURED | the vendor checks the CLKDIV limit first and stops; run `chain25` (25 CLKDIV2 -> 25 CLKDIV) reported PA2017 for CLKDIV only |

This 24 is an independent, vendor-authoritative confirmation of
`gw5_get_num_of_hclks(device) -> 6` (`apycula/chipdb.py:1229-1232`), which
until now was an untested `return 6` for every non-25A device.

## 3. The presence-diff staircase (MEASURED)

Bits that moved versus the `base` build (no CLKDIV), per HCLK cell. Every
other tile that moves is either constant across the whole sweep (the design's
own IO/logic) or fabric routing; **no seventh HCLK cell ever appears.**

| N CLKDIV | (27,0) | (27,181) | (81,0) | (81,181) | (108,64) | (108,117) |
|---|---|---|---|---|---|---|
| 1  | 0 | 0 | 0 | 0 | 20 | 0 |
| 4  | 0 | 0 | 0 | 0 | 71 | 0 |
| 8  | 0 | 62 | 0 | 0 | 79 | 0 |
| 12 | 0 | 62 | 0 | 70 | 79 | 0 |
| 16 | 0 | 62 | 0 | 70 | 81 | 70 |
| 20 | 0 | 70 | 64 | 70 | 81 | 70 |
| 24 | 64 | 68 | 66 | 84 | 81 | 70 |

Two further table-48 cells move by a constant **4 bits** from N=16/N=20 on —
`(108,118)` (ttyp 266) and `(108,0)` (ttyp 48). Both are 8-row table-48 cells,
not blocks: they carry only inter-HCLK (`>= 187`) wires, i.e. they are
inter-HCLK bridge cells, and the 4 bits are the bridge being switched on when
more than one block is in use. They must **not** be added to `_gw5a_hclk_locs`.

## 4. All eleven table-48 cells (MEASURED, from the `.fse`)

Six are blocks (§1); five are inter-HCLK bridge cells (8 rows each, only
`>= 187` wires). `hi_src` / `hi_dst` are the inter-HCLK wire numbers the cell's
table 48 mentions — T05 and T08 consume these directly.

| row | col | ttyp | rows | role | hi_src | hi_dst |
|---|---|---|---|---|---|---|
| 27 | 0 | 272 | 159 | **block 0** | 327-332 | 339,340 |
| 27 | 181 | 273 | 159 | **block 1** | 199-204 | 211,212 |
| 63 | 0 | 270 | 8 | bridge | 315-322 | 323-326 |
| 63 | 181 | 271 | 8 | bridge | 187-194 | 195-198 |
| 81 | 0 | 275 | 165 | **block 2** | 295-300, 333-338 | 307,308,341,342 |
| 81 | 181 | 276 | 165 | **block 3** | 205-210, 231-236 | 213,214,243,244 |
| 108 | 0 | 48 | 8 | bridge | 283-290 | 291-294 |
| 108 | 64 | 274 | 165 | **block 4** | 269-274, 301-306 | 277,278,309,310 |
| 108 | 117 | 379 | 165 | **block 5** | 237-242, 263-268 | 245,246,275,276 |
| 108 | 118 | 266 | 8 | bridge | 251-258 | 259-262 |
| 108 | 181 | 49 | 8 | bridge | 219-226 | 227-230 |

## 5. Wire numbers T05/T06/T08 consume (MEASURED)

| Symbol | 138C value | 25A value | Derivation |
|---|---|---|---|
| `gw5_hclk_wire_offset` | **187** | 187 | already present in `chipdb.py:1223-1224`; confirmed — no table-48 *intra*-HCLK source is >= 187 on either device |
| `gw5_ihclk_wire_num` (`chipdb.py:1226-1227`, **F23** KeyError) | **38** | 65 | the inter-HCLK band is `range(187, 187 + 4*n)`. Max inter-HCLK **source** over all table-48 cells is 338 on the 138C and 446 on the 25A. `187 + 4*38 - 1 = 338` exactly; `187 + 4*65 - 1 = 446` exactly. The 25A case reproduces the maintainer's 65 with no residue, so the derivation is calibrated, not fitted. |
| `gw5_get_num_of_hclks` | **6** (already returns 6) | 4 | vendor PA2017 limit 24 / 4 per block |
| `hclknames` index span needed | `6*187 + 4*38 = 1274` | `6*187 + 4*65 = 1382` | `gw5_make_hclk_pips` names inter-HCLK wires `hclknames[srcid + 5*hclk_off]`, so the table must reach `5*187 + 338 = 1273` |

## 6. ASSUMED vs MEASURED — read this before writing T05-T08

| Claim | Status | Note |
|---|---|---|
| 6 HCLK blocks on the 138C | **MEASURED** | two independent instruments (§1, §2) |
| Block positions in §1 | **MEASURED** | presence diff pins the fuses to those exact tiles |
| 4 CLKDIV per block, 24 total | **MEASURED** | vendor PA2017 + the §3 staircase |
| `gw5_ihclk_wire_num = 38` | **MEASURED** (derivation calibrated on the 25A) | not proven by a bitstream; T05 must keep the `.fse`-derived form, not a literal |
| "6 blocks x 2 **halves**, 3 top / 3 bottom" (roadmap `L234-239`, P1.T04 *Tests first*) | **ASSUMED — and refuted as stated** | By die row midpoint the six blocks split **2 top / 4 bottom**, not 3/3 (§1). Two blocks sit on the bottom *edge*, where the natural split is left/right, not top/bottom. The check in `verify_topology.py` asserts the **measured** 2/4 partition and records the 3/3 expectation as refuted. |
| "2 halves" == 2 CLKDIV *sections* per block (the pre-5A `SECT0`/`SECT1` trick, `chipdb.py:2009-2013`) | **ASSUMED, not measured** | On GW5A apicula does **not** pretend two sections: `gw5_add_hclk_bels` creates 4 real CLKDIV + 4 CLKDIV2 per block. The wire pairing in that function (even `i` from `HCLK_BUF_BO`, odd `i` from `CLKDIV2_I`) hints at 2 sections of 2 wires, but nothing here measures it. |
| Which fabric/IO cells each block *serves* (the `edges` table, IOLOGIC affiliation) | **NOT MEASURED** | needs the OSER4-per-side probe; IOLOGIC on the 138C is Phase 3's (`D39` state (1) forbids IOLOGIC bels here). T07/Phase 3 owns it. Do not invent an `edges` table from the 25A's. |
| CLKDIV2 device limit | **NOT MEASURED** | §2 |
| `clknames_5ast138c` HCLK entries | **ASSUMED 4-block** | `wirenames.py:1002-1009` defines `HCLK0..HCLK3_BANK_OUT{0,1}` only, and `hclknames_5ast138c` fills `HCLK_UNK` over `range(2, 701)` with `HCLK_TO_GCLK`/`HCLK_GCLK` for blocks 0-3 only (`:1020-1032`). Both are 25A carry-overs and must be extended to blocks 4 and 5 and to index 1274 (§5) — append-only. |
| 25A `_gw5a_hclk_locs[3] = (34,91)` vs instrument I1's `(35,91)` | **open point, 25A only** | Both cells carry table 48. The 138C is unaffected: its six blocks are confirmed by the presence diff, which the 25A entry never was in-tree. Flag it upstream rather than silently "fixing" the 25A. |

## 7. Vendor rules measured along the way (bonus, for T14-T16 and Phase 3)

* `CLKDIV2.CLKOUT` **cannot** drive ordinary fabric logic:
  `ERROR (CK2060) : The connection between instance 'ce0' and instance
  'dout_d_s4' is incorrect`. It must drive `CLKDIV.HCLKIN`, IOLOGIC `FCLK`, or
  a PLL — matching `doc/hclk.md`. Three probe runs were spent discovering this;
  a CLKDIV2 shape must chain into a CLKDIV.
* `CLKDIV2` takes **no** `DIV_MODE` parameter
  (`$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:13122`).
* 24 CLKDIV place and route in ~40 s; the netlist-level resource check refuses
  in ~3 s, so a capacity probe is nearly free.

## 8. Reproduction

```sh
cd $FL_WT/apicula
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
$FL/vendor/venv/bin/python $OTC/evidence/clocking/probe_hclk.py \
    --out-root $DATASTORE/batch/p1t04 \
    --log      $OTC/evidence/_runs/p1-hclk-probe.log \
    --ledger   $OTC/evidence/clocking/oracle-runs.jsonl \
    --result   $OTC/evidence/clocking/probe-result.json
$FL/vendor/venv/bin/python $OTC/evidence/clocking/verify_topology.py
```

Artefacts: `$OTC/evidence/_runs/p1-hclk-probe.{log,watchdog.log,stdout.log,pid}`,
`$OTC/evidence/clocking/{oracle-runs.jsonl,probe-result.json,probe-fs-sha256.txt}`.
The `.fs` bitstreams (8 x 34 MB) are listed with their sha256 in
`probe-fs-sha256.txt` and were deleted after the diff (`V20` storage hygiene,
boot volume near full).

## 9. Oracle budget (D62)

**14 vendor runs** charged to P1.T04 (blueprint allocation: 14):
1 exploratory `clkdiv24`, 12 in the detached batch `p1-hclk-probe`
(`base`, `clkdiv01/04/08/12/16/20/24/25`, `clkdiv2_24`, `clkdiv2_25`,
`both24`), and 1 `chain25`. Every run is one JSONL row in
`$OTC/evidence/clocking/oracle-runs.jsonl` (P1.T03's
`$OTC/evidence/_budget/clocking-runs.tsv` did not exist when this task ran).
Four runs came back `refused`; a refusal is a measurement (§2, §7), not a hole.
