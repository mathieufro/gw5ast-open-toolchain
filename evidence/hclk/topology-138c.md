# GW5AST-138C HCLK block table (P1.T04)

The machine-parseable half of the P1.T04 measurement. Full derivation,
calibration, budget and the ASSUMED-vs-MEASURED ruling:
`$OTC/evidence/clocking/hclk-topology.md`. Verifier:
`$OTC/evidence/clocking/verify_topology.py`.

Grid: 109 rows x 182 cols. Blocks: 6. CLKDIV per block: 4. CLKDIV total: 24
(vendor-stated resource limit, `PA2017`).

| hclk_idx | row | col | ttyp | half | side |
|---|---|---|---|---|---|
| 0 | 27 | 0 | 272 | top | left |
| 1 | 27 | 181 | 273 | top | right |
| 2 | 81 | 0 | 275 | bottom | left |
| 3 | 81 | 181 | 276 | bottom | right |
| 4 | 108 | 64 | 274 | bottom | bottom |
| 5 | 108 | 117 | 379 | bottom | bottom |

`half` is the die half the block sits in (`row < 54.5` => top). The measured
partition is **2 top / 4 bottom**; the blueprint's assumed 3/3 is refuted —
see §6 of the full document.

Inter-HCLK bridge cells (table 48 present, **not** blocks, never in
`_gw5a_hclk_locs`): (63,0) ttyp 270, (63,181) ttyp 271, (108,0) ttyp 48,
(108,118) ttyp 266, (108,181) ttyp 49.

Wire numbers: `gw5_hclk_wire_offset = 187`, `gw5_ihclk_wire_num = 38`,
`gw5_get_num_of_hclks = 6`, `hclknames` span needed = 1274.
