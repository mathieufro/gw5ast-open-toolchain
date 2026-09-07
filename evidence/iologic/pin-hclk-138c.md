# GW5AST-138C pin → bank → HCLK block (P3.T06)

Machine-readable table: `evidence/iologic/pin-hclk-138c.json`.
Generator: `tools/derive_pin_hclk_138c.py` (`--check` fails on a stale
artefact). Tests: `tools/tests/test_pin_hclk_138c.py`.

Device `GW5AST-138C`, package `PBGA484A`, part `GW5AST-LV138PG484AC1/I0`,
die 109 rows × 182 cols. **297 I/O balls**, all mapped.

## DISPATCH-STATE

`FOUND: (2) — Phase 1 already routed 138C into the guard.`

`apycula/chipdb.py:2326` reads `if device in {'GW5A-25A', 'GW5AST-138C'}:` and
`:2327` already calls `gw5_make_pin_to_hclk(dev, device)` with the two-argument
signature, off a module-level `_gw5_pin_to_hclk` dict (`:1555`) that today
holds the 25A entry only. So the blueprint's escape clause applies: the
inserted guarded call and the signature change of `P3.T06`'s "two-line dispatch
edit" are **already landed** and this task is table work only. The 25A entry is
untouched, byte for byte:

    {'row': 36, 'col': 11, 'wire': 'F5', 'hclk_idx': 1, 'hclk_wire_idx': 311}

## What each column is derived from

| Column | Source | Mark |
|---|---|---|
| `ball`, `site`, `cfg`, `diff`, `true_lvds`, `dqs` | `IDE/data/device/GW5AST-138C/PBGA484A.json` `PIN_DATA[*]` (the file `apycula.pindef` reads) | DAT-DERIVED |
| `bank` | `GW5AST-138C.dat` `compat_dict['Bank'][{T,B,L,R}{A,B}][n]` — the same table `chipdb.pin_bank` is built from — **cross-checked** against `PBGA484A.json` `BANK` | DAT-DERIVED |
| `row`, `col` | the site name's 1-based index minus one, on the die edge its letter names, against the `.fse` grid dims | DAT-DERIVED |
| `iologic` | `.fse` `shortval` table 21 (`A` half) / 22 (`B` half) of the cell's tile type, with `chipdb.fse_iologic`'s corner exclusion `{48,49,50,51}` | FSE-DERIVED |
| `hclk_block` | nearest block on the same die edge (`BLOCK_RULE = NEAREST_BLOCK_ON_SIDE`) over `P1.T04`'s measured block table | **ASSUMED** |
| `hclk_lanes` | all four `CLKDIV` lanes of that block | **ASSUMED** |

The bank cross-check is the strongest single result here: **297/297 balls agree
between the `.dat` bank table and the package pinout JSON**, two independently
shipped files. A disagreement raises rather than being resolved by preference.

## Why the block column is ASSUMED and not measured

No shipped table on this device relates an I/O cell to an HCLK block.
`chipdb.gw5_create_hclk_iol_pip` returns `False` for `GW5AST-138C`, so
`dev.io2hclk` is empty for it, and the 25A precedent that would be generalised
is a hand-written per-side rule (`chipdb.py:1296-1306`), not device data.
`P3.T07` is the task that measures reachability; until then every block cell of
this table is a hypothesis for it to confirm or refute.

`pin_to_hclk_entries` — the list shaped like `chipdb._gw5_pin_to_hclk`'s
values, which the chipdb consumes directly — is therefore **empty**. An entry
needs a fabric wire name and an `hclknames` index per pin and neither is
derivable from the device files; putting a guessed one there would add an
unmeasured node to the routing graph. The 48 candidate balls sit beside it
under `clock_pin_candidates`.

## Corroboration of the block rule (not evidence, but it would have failed)

1. **No bank is split across two blocks.** bank → block is a clean function:

   | bank | 2 | 3 | 4 | 5 | 6 | 7 | 10 |
   |---|---|---|---|---|---|---|---|
   | block | 1 | 3 | 5 | 4 | 2 | 0 | 5 |

   Banks 6 and 7 are the DDR banks (`D20c`, `D54`) and sit on the left edge,
   on blocks 2 and 0. Bank 10 (12 balls) shares block 5 with bank 4.

2. **The dedicated clock balls bracket their block's cell.** The 48 balls whose
   pinout `CFG` names an `SGCLK`/`MGCLK` role are placed by the die layout, not
   by this rule, and every one of them lands **≤ 5 cells** from the block the
   rule assigns it — e.g. block 4 at `(108,64)` collects `IOB60/62/66/68`, and
   block 5 at `(108,117)` collects `IOB114/116/120/122`.

## Geometry

* I/O on three edges only: left 100 balls, right 100, bottom 97. The `.dat`
  `TA`/`TB` bank columns are `-1` for all 184 entries, so **this device exposes
  no top-edge I/O** and the two top blocks (0 at `(27,0)`, 1 at `(27,181)`) are
  reached from the left and right edges, matching `P1.T04`'s 2-top/4-bottom
  partition.
* 293 of 297 balls have an IOLOGIC. The four that do not are `IOL1A`,
  `IOL109A`, `IOR1A`, `IOR109A` — the corner cells `chipdb.fse_iologic`
  excludes.

## Board-relevant rows (Tang Mega 138K + NEO dock)

| net | ball | site | bank | cell | block | note |
|---|---|---|---|---|---|---|
| `sys_clk` | V22 | IOB104B | 4 | (108,103) | 5 | `EMCCLK` config role |
| `RGMII_GTXCLK` | F20 | IOR33B | 2 | (32,181) | 1 | `CLKTEST_R0` |
| `RGMII_TXD[0..3]` | D21/E21/D22/E22 | IOR51B/51A/49B/49A | 2 | (50,181)/(50,181)/(48,181)/(48,181) | 1 | |
| `RGMII_TXEN` | F21 | IOR55A | 2 | (54,181) | 1 | |
| `RGMII_RST_N` | W20 | IOB122B | 4 | (108,121) | 5 | `MGCLKC_5` |
| `PHY_CLK` | V19 | IOB114B | 4 | (108,113) | 5 | `SGCLKC_4` |

The whole RGMII TX group is bank 2 on block 1; the PHY clock and reset are
bank 4 on block 5. The dock exposes no RGMII **RX** pins in
`08_Misc/tang_mega_138K_pins.cst` — the RX half of `S10` has to be pinned from
the schematic before it can be swept, which is `P3.T07`'s input, not this
table's.
