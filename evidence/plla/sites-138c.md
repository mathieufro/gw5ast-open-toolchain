# P1.T17 — GW5AST-138C PLL sites, enumerated from the shipped vendor tables

**Status: MEASURED** (except where a row says ASSUMED).
**Updated by `P1.T19`** (§8): every site is now `traced`, the two §3 ASSUMED
items are settled, and the vendor cell type is `PLL`, not `PLLA`.
Source files: `$GOWINHOME/IDE/share/device/GW5AST-138C/GW5AST-138C.{fse,dat}`,
Gowin IDE **1.9.12.03 Standard** (`GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA`).
Comparison device: `GW5A-25A` from the same install.
Machine-readable form: **`sites-138c.json`** beside this file (the form `P1.T18` reads).
Attribute-id dump: **`attrids-138c.tsv`**.
Regenerate: `GOWINHOME=... $FL/vendor/venv/bin/python evidence/plla/gen_sites_138c.py`
(the generator is committed beside its output); the enumeration rule is stated in §2.

---

## 1. Headline

| Question | Answer | Kind |
|---|---|---|
| PLLs on the device | **12** (DS1239E Table 1-1 `Phase Locked Loop (PLLs) 12`; Figure 2-1 and Figure 2-10 draw 4 left + 4 right + 4 bottom) | vendor doc |
| PLL sites found in the shipped `.fse` | **12** | MEASURED |
| Sites the `.dat` **names** | **0** | MEASURED |
| Sites needing tracing (`P1.T19`) | **12** — all traced, see §8 | MEASURED |
| PLL slots (`fse_create_slot_plls`'s mechanism) on 138C | **none exist** — the `.fse` carries **no pseudo-ttyp ≥ 1024** at all and **no `drpfuse` header table** | MEASURED |

---

## 2. How the sites were found (the enumeration rule)

`chipdb.py` `_known_tables[35] == 'PLL'`: a tile whose `.fse` `shortval` carries table **35**
carries PLL configuration fuses. On the 25A that table lives once, in the **slot** pseudo-ttyp
**1024** (2440 rows), and `chipdb.py:1188-1191` reads it through `drpfuse_lookup` because
`ttyp >= 1024`. On the 138C there is no pseudo-ttyp and no `drpfuse` table, and table 35
instead appears in **ordinary grid tiles**: 23 ttyps carry it, of which 11 ttyps carry a
*large* table (685-968 rows) and the rest carry 1 or 4 rows (HCLK-block and edge tiles —
ttyps 272/273/275/276 are the six-block HCLK ttyps measured in `P1.T04`).

Rule applied: **a PLL site = a maximal run of horizontally adjacent grid tiles whose ttyp
carries `shortval` table 35 with ≥ 100 rows.** That rule yields exactly **12** runs, every one
of them **three tiles wide**, with an identical `(804|808, 968, 685)` row-count signature —
2457 (or 2461) table rows per site against the 25A slot's 2440. The count, the 3-tile shape and
the left/right/bottom distribution all match DS1239E independently of the datasheet.

Parse integrity (so "absent" is not "mis-read"): `GW5AST-138C.fse` parses to **exactly EOF**
(30,829,508 bytes read, 0 trailing bytes), so the absence of pseudo-ttyp 1024 is a measurement,
not a truncation.

---

## 3. The 12 sites

`row`/`col` are chipdb grid coordinates (grid is 109 rows × 182 cols). `(row, col)` is the
**anchor** tile = the lowest-column tile of the 3-tile run. `slot_idx` is `n/a`: this device has
no slots (§2). `source` values: `fse` = position measured from the shipped `.fse`;
`dat` = named by a `.dat` port table; `traced` = resolved by vendor-run tracing;
`unknown` = not resolved. `ports` says where the port wiring must still come from.

| pll_idx | side | slot_idx | (row, col) | tiles (row, col, ttyp, table-35 rows) | source | ports |
|---|---|---|---|---|---|---|
| 0 | L | n/a | (27, 1) | (27,1,74,804) (27,2,75,968) (27,3,76,685) | traced | 23 in / 8 out (T19) |
| 1 | R | n/a | (27, 177) | (27,177,77,804) (27,178,78,968) (27,179,79,685) | traced | 23 in / 8 out (T19) |
| 2 | L | n/a | (45, 0) | (45,0,268,808) (45,1,75,968) (45,2,76,685) | traced | 23 in / 8 out (T19) |
| 3 | R | n/a | (45, 178) | (45,178,77,804) (45,179,78,968) (45,180,79,685) | traced | 23 in / 8 out (T19) |
| 4 | L | n/a | (63, 0) | (63,0,270,808) (63,1,75,968) (63,2,76,685) | traced | 23 in / 8 out (T19) |
| 5 | R | n/a | (63, 178) | (63,178,77,804) (63,179,78,968) (63,180,79,685) | traced | 23 in / 8 out (T19) |
| 6 | L | n/a | (81, 1) | (81,1,74,804) (81,2,75,968) (81,3,76,685) | traced | 23 in / 8 out (T19) |
| 7 | R | n/a | (81, 177) | (81,177,77,804) (81,178,78,968) (81,179,79,685) | traced | 23 in / 8 out (T19) |
| 8 | B | n/a | (108, 28) | (108,28,182,804) (108,29,183,968) (108,30,184,685) | traced | 23 in / 8 out (T19) |
| 9 | B | n/a | (108, 32) | (108,32,182,804) (108,33,183,968) (108,34,184,685) | traced | 23 in / 8 out (T19) |
| 10 | B | n/a | (108, 146) | (108,146,182,804) (108,147,183,968) (108,148,184,685) | traced | 23 in / 8 out (T19) |
| 11 | B | n/a | (108, 150) | (108,150,182,804) (108,151,183,968) (108,152,184,685) | traced | 23 in / 8 out (T19) |

Counts: `source == "traced"` **12**, `source == "dat"` **0**, `source == "fse"` **0**,
`source == "unknown"` **0**. Sides: 4 L / 4 R / 4 B — the DS1239E Figure 2-1 layout.

**ASSUMED (not measured here), for `P1.T18`/`P1.T19` to settle:**
- that the **anchor** tile (lowest column of the run) is the right cell to hang the `PLLA` bel
  and the `extra_func['pll']` record on. The three tiles are one PLL; which one the vendor
  treats as the instance location is a `P1.T19` `INS_LOC` trace, not a table fact;
- that `pll_idx` order (row-major over the anchors, as tabulated) matches the vendor's
  `PLL_L[n]`/`PLL_R[n]`/`PLL_B[n]` site naming. `P1.T19`'s `INS_LOC` probes fix the mapping.

---

## 4. What the `.dat` does and does not name — and the T19 trace list

`GW5AST-138C.dat` parses cleanly (`F15`/`F18`); the PLL tables are present but **empty of site
information**:

| `.dat` table | 138C | 25A | verdict |
|---|---|---|---|
| `PllLTIns/Outs`, `PllLBIns/Outs`, `PllRTIns/Outs`, `PllRBIns/Outs` (`dat_parser.py:515-522`) | all rows `0xffff` — **0 populated** in all 8 tables | 36 / 32 populated rows in each | 138C names **no** site |
| `gw5aStuff['PllIn']` (216) / `PllInDlt` | 131 of 216 entries populated; **23 of the 35 `_plla_inputs` present** | 35 of 35 present | old-style, position-relative |
| `gw5aStuff['PllOut']` (32) / `PllOutDlt` | 8 of 32 populated; **8 of the 16 `_plla_outputs` present** | 16 of 16 present | old-style, position-relative |
| `portmap['PllIn' 36 / 'PllOut' 5 / 'PllClkin' 6 / SpecPll0/1 Ins 108 / Outs 15 / Clkin 18]` | shapes as **F16** predicts; only `PllClkin` (6) is non-empty, the rest are all-`-1` | identical (also all-`-1` except `PllClkin`) | 1/2-series legacy fields, carry nothing for GW5 |

The `.dat` ports that are **missing on 138C but present on 25A** are exactly the MDIO/DRP
block — inputs `MDCLK, MDOPC0-1, MDAINC, MDWDI0-7` (12) and outputs `MDRDO0-7` (8). Consistent
with §2: the 138C PLL has no DRP path, so the vendor tables carry no MDIO ports for it.

**`P1.T19` trace list (the deliverable this task owes T19):**
1. all **12** sites — port wire names for the `_plla_inputs`/`_plla_outputs` set, since no named
   table exists (the old-style `PllIn/PllInDlt` pair gives *relative* wires only, and covers
   just 23/35 inputs and 8/16 outputs);
2. the **bel anchor** tile of each 3-tile run (§3 ASSUMED);
3. the vendor site name ↔ `pll_idx` mapping via `INS_LOC`.

That is 12 sites to trace, not the 6-7 the blueprint anticipated — see §6.

---

## 5. Attribute ids (`attrids-138c.tsv`)

`attrids-138c.tsv` has **37 data rows**: 36 rows = the 12 sites × 3 tiles, one row per tile
(`device, site_idx, side, row, col, ttyp, table_id, table_rows, distinct_attr_ids,
attr_id_min, attr_id_max`), plus **1** row for the 25A slot pseudo-ttyp 1024 reference.

| device | table | rows | distinct attr ids |
|---|---|---|---|
| GW5AST-138C, per site (3 tiles unioned) | `shortval[35]` in 3 grid tiles | **2457** (sites 0,1,3,5,6,7,8,9,10,11) / **2461** (sites 2, 4) | **2433** / **2437** |
| GW5A-25A | `shortval[35]` in pseudo-ttyp **1024** | **2440** | **2416** |

**Correction to the blueprint's "192".** 192 is `len(apycula.attrids.pll_attrids)` — the size of
apicula's *symbolic* PLL attribute-name table, not the `.fse` table's attribute-id count. The
25A `.fse` PLL table carries **2416** distinct attribute ids (max id 2512), and the 138C
per-site union carries **2433-2437** (both measured above). Both numbers are recorded here as
numbers, as `P1.T17`'s done-condition requires: `192` (attrids.py), `2416` (25A `.fse`),
`2433`/`2437` (138C `.fse`, per site).

---

## 6. Comparison with the 25A enumeration the existing code performs

`fse_create_slot_plls` (`chipdb.py:2288-2291`) is gated `if device not in {"GW5A-25A"}: return`
and then walks a hardcoded 6-entry literal:

| 25A entry | (row, col) | slot_idx | io_table |
|---|---|---|---|
| PllLB | (27, 0) | 6 | `PllLB` |
| PllRB | (27, 91) | 2 | `PllRB` |
| PllLT | (0, 0) | 5 | `PllLT` |
| PllRT | (0, 91) | 3 | `PllRT` |
| — | (0, 45) | 4 | `old_style` |
| — | (36, 45) | 8 | `old_style` |

Structural differences that `P1.T18` must absorb — the 138C is **not** a bigger 25A:

1. **No slots.** 25A: PLL fuses in pseudo-ttyp 1024, read through `drpfuse_lookup`
   (`chipdb.py:1191`), addressed by `slot_idx` via `gowin_pack.get_pll_slot_fuses(av)` →
   `get_shortval_fuses(db, 1024, av, 'PLL')`. 138C: **no pseudo-ttyp, no `drpfuse` header
   table**; the fuses are ordinary `shortval[ttyp]['PLL']` entries in three grid tiles per site.
   A `_gw5a_pll_slots` table keyed by `(row, col, slot_idx, io_table)` therefore does not by
   itself make 138C work: `slot_idx` has no meaning here, and the packer's
   `get_pll_slot_fuses`/`set_pll_slot_fuses` path needs a per-device branch. **This is a
   coordination note for `P1.T18` and for the `gowin_pack.GW5AST_138C` fuse handlers.**
2. **No named `.dat` port tables** (§4) — every 138C entry is `old_style`-shaped at best, and
   even the old-style table is partial (23/35 in, 8/16 out).
3. **One tile per PLL on 25A, three per PLL on 138C** — the bel/`extra_func` anchor is a new
   decision (§3 ASSUMED).
4. **Count and geometry:** 6 sites (2 top, 2 bottom-ish, 2 mid-column) on 25A vs 12 sites
   (4 L, 4 R, 4 B, none top) on 138C.

**Blueprint expectations refuted by this measurement** (recorded, per the standing order, rather
than papered over):
- *"`dat_parser.py` names at most 5-6 sites … the `.dat` names 5-6 of the 12"* → the 138C `.dat`
  names **0**. Consequently `P1.T17`'s specified test bound `5 <= dat_count <= 6` is
  unsatisfiable; the shipped test asserts the measured `dat_count == 0` and this refutation.
- *"6-7 unresolved sites, 14 oracle runs"* (`P1.T19`) → **12** sites need port tracing;
  positions, however, are already measured here, so T19's probes can be *placement-confirming*
  rather than placement-searching. T19 should re-price its run budget.
- *"the `.fse` shortval pseudo-ttyp 1024 `'PLL'` table … for 138C"* → there is no pseudo-ttyp
  1024 on 138C; the equivalent data is in-grid (§2).

---

## 7. Reproduction

```sh
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
$FL/vendor/venv/bin/python -m pytest $OTC/tools/tests/test_plla_sites.py -q
```

The two tests (`P1.T17`): `test_plla_sites_artifact_counts` (this artefact: 12 rows, the
source-column counts, the attrid TSV row count and the recorded numbers) and
`test_plla_25a_enumeration_unchanged` (pins the six 25A entries of `fse_create_slot_plls`
byte-for-byte, so `P1.T18`'s move into `_gw5a_pll_slots` is provably identity-preserving for
the 25A).

No apicula code was changed by this task.

---

## 8. `P1.T19` — the trace (MEASURED, 13 oracle runs)

**Method.** One vendor project per site: a single hard PLL pinned by
`INS_LOC "dut_pll" PLL_<side>[<n>];`, compiled through the oracle
(`fuzz/gw5ast138c/shapes/clocking_pll_trace.py`, batch `pll-trace-pilot2`).
Each run's `run/impl/pnr/run.fs` is decoded to per-tile bitmaps
(`bslib.read_bitstream` -> `chipdb.tile_bitmap`) and the bits are counted in
each of §3's twelve candidate three-tile groups
(`evidence/plla/gen_trace_138c.py`, output `runs/trace-138c.json`).

The discrimination is total, not statistical: with one PLL in the design the
constrained site's three tiles carry ~120 bits each and eleven of the twelve
groups are **all-zero**, so no baseline run and no cross-run subtraction is
needed. That is why the trace cost 12 runs and not the blueprint's 14.

### 8.1 The mapping — a bijection, measured

| vendor site | anchor `(row, col)` | tiles | bits per tile | side |
|---|---|---|---|---|
| `PLL_L[0]` | (27, 1)   | (27,1) (27,2) (27,3)       | 122 / 126 / 126 | L |
| `PLL_L[1]` | (45, 0)   | (45,0) (45,1) (45,2)       | 123 / 125 / 127 | L |
| `PLL_L[2]` | (63, 0)   | (63,0) (63,1) (63,2)       | 123 / 125 / 127 | L |
| `PLL_L[3]` | (81, 1)   | (81,1) (81,2) (81,3)       | 122 / 126 / 126 | L |
| `PLL_R[0]` | (27, 177) | (27,177) (27,178) (27,179) | 122 / 126 / 130 | R |
| `PLL_R[1]` | (45, 178) | (45,178) (45,179) (45,180) | 123 / 125 / 126 | R |
| `PLL_R[2]` | (63, 178) | (63,178) (63,179) (63,180) | 123 / 125 / 126 | R |
| `PLL_R[3]` | (81, 177) | (81,177) (81,178) (81,179) | 122 / 126 / 130 | R |
| `PLL_B[0]` | (108, 28) | (108,28) (108,29) (108,30) | 106 / 121 / 147 | B |
| `PLL_B[1]` | (108, 32) | (108,32) (108,33) (108,34) | 108 / 121 / 147 | B |
| `PLL_B[2]` | (108, 146)| (108,146) (108,147) (108,148) | 102 / 121 / 142 | B |
| `PLL_B[3]` | (108, 150)| (108,150) (108,151) (108,152) | 104 / 121 / 142 | B |

Twelve distinct anchors for twelve distinct site names: the mapping is a
**bijection**, and `slot_idx` in `chipdb._gw5a_pll_slots['GW5AST-138C']` is now
the vendor site index (`L[0..3]` -> 0..3, `R[0..3]` -> 4..7, `B[0..3]` -> 8..11)
rather than P1.T17's assumed row-major numbering. The two happen to agree on
the left/right *ordering* (top to bottom) and the bottom ordering (left to
right); that agreement is now measured rather than assumed.

**Both §3 ASSUMED items are settled:**

1. the **anchor** — the lowest-column tile of the run — is the right cell to
   hang the bel on: it is the tile the constrained site lights up, in all
   twelve runs;
2. the `pll_idx` order matches the vendor's `PLL_L/R/B[n]` naming, as above.

**One honest imperfection.** `PLL_B[0]` also sets 8/4/0 bits in `PLL_B[1]`'s
group, and `PLL_B[2]` sets 5/4/0 bits in `PLL_B[3]`'s — the adjacent bottom
pairs share something (most plausibly a shared clock-output mux), 12 bits
against 374. The primary group is never in doubt; the shared bits are recorded
here rather than thresholded away, and belong to whoever models the bottom PLL
clock outputs.

### 8.2 Blueprint expectation refuted: the cell type is `PLL`, not `PLLA`

The first oracle run (`pll-trace-pilot`, a `PLLA` instantiation) was refused:

```
ERROR (RP0008) : There is no PLLA resource in current device, please change device
```

That refusal is a measurement, and it corroborates `UG306-1.0.1E` Table 5-11
("PLLA Device Supported"), which lists **GW5A-25 and nothing else**. Rerunning
the identical design with the `PLL` primitive (`prim_sim.v:13333`) placed and
routed cleanly on every one of the twelve sites.

The two primitives differ in a way that matches this device's `.dat` exactly:

| | `PLLA` (`prim_sim.v:15202`) | `PLL` (`prim_sim.v:13333`) |
|---|---|---|
| MDIO/DRP ports | `MDCLK`, `MDOPC`, `MDAINC`, `MDWDI`, `MDRDO` | **none** |
| dynamic dividers | none | `ENCLK0-6`, `FBDSEL`, `IDSEL`, `MDSEL`, `MDSEL_FRAC`, `ODSEL0-6`, `DT0-3`, `ICPSEL`, `LPFRES`, `LPFCAP` |
| 138C `.dat` agrees? | no — every MDIO row is `-1` | **yes** |

This is the same finding as §2's "no DRP slots" seen from the vendor's side:
the 138C hard PLL has no mini-DRP, so it is not a `PLLA`.

### 8.3 What is still open (named, not papered over)

* **The dynamic-divider port wires.** `chipdb._plla_inputs`/`_plla_outputs`
  index 23 inputs and 8 outputs that `PLL` and `PLLA` share, and those are the
  ports `P1.T18` builds. The other ~108 populated `PllIn` rows are `PLL`'s
  `ENCLKn`/`FBDSEL`/`IDSEL`/`MDSEL`/`ODSELn`/`DTn` ports at indices apicula
  has **no table for**. Recovering them is a per-port trace of ~50 signals, not
  a 12-run placement sweep, and it is not needed for the bels this phase owes.
* **Packing.** `gowin_pack.get_pll_slot_fuses`/`set_pll_slot_fuses` still
  address fuses through `drpfuse_lookup` on pseudo-ttyp 1024, which does not
  exist on this device (§2). A 138C PLL needs a per-device branch onto the
  ordinary `shortval[ttyp]['PLL']` tiles named in §8.1.

### 8.4 Reproduction

```sh
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export OTC_EVIDENCE=$OTC/evidence PYTHONPATH=<apicula worktree>
python -m fuzz.gw5ast138c.harness --design-dir $DATASTORE/batch/pll-trace \
    --shape clocking_pll_trace --batch-id pll-trace-pilot2 --level E1 \
    --detach --expected-minutes 90
python evidence/plla/gen_trace_138c.py $DATASTORE/batch/pll-trace \
    evidence/plla/runs/trace-138c.json
```

Batch log `evidence/_runs/pll-trace-pilot2.log` ends
`BATCH_COMPLETE pll-trace-pilot2 runs=11 ok=0 diff=0 aborted=11` (run `0000`
was the earlier single-point run of the same batch id and was resumed past).
Every verdict is `aborted` because the **open** half of each run has no PLL bel
in the installed nextpnr `.bin` yet; the **vendor** half — the half this task
measures — completed and produced `run.fs` in all twelve.
