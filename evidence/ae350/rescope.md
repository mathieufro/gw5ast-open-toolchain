# `P2.T26` — the re-scoped plan for `P2.T07`-`P2.T37`

Input: `reconciliation.md` (0/911 covered), `slicing-plan.md`
(`EC5-WORK-ORDER` 149 runs vs a cap of 8), and this task's two measurements
recorded in `wire-map-138c.md`.

`P2.T06` offered three options and recommended option 2 — *find the real
connectivity source before spending runs*. **Option 2 wins, and it is now
grounded:** the port map is in `dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts']`,
not in the legacy `McuIns`/`McuOuts` triples, and it reads as noise only because
of an argument transposition at `dat_parser.py:545-546`.

## The one line that changes the phase

The blueprint priced `EC5` at **one vendor run per bus**. Run
`p2t26-tilewires` shows the vendor places and routes **all 149 ports at once in
15 seconds**. So the discovery cost was never 149 runs; and after the parser
fix it is **0 runs**, because the vendor ships the table.

## Task-by-task

| task | verdict | why |
|---|---|---|
| `P2.T07` `fse_create_ae350()` skeleton | **STANDS, amended twice** | The `(0,0)` fallback in the HOW is wrong in its column and right in its row: every port record is in **die row 0**, columns 145-181. Anchor the bel at `(0, 145)`. The `ttyp` 224/228 interface bands hold the block's configuration, not its ports — do not anchor on them. |
| `P2.T08` slice `McuIns`/`McuOuts` into ports | **RE-TARGETED, now trivial** | Same `make_port` code path, different source: `dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts']`, triples `(row, col, wire)` 1-based, exactly as `fse_create_adc` (`chipdb.py:2489-2492`) consumes `Adc25kIns`. The slot-to-bit rule and the per-bit table are already written out in `wire-map-138c.json`, so the task is a read, not a derivation. The task's three tests survive unchanged. |
| **NEW `P2.T08a`** fix the `read_scaledGrid16` call-site transposition | **DONE** | Landed on `ae350/dat-scaledgrid-138c`. The defect was the transposition *and* u16-word bases; one reader, `read_packed_grid16`, replaces 72 call sites. The `Ins` base needed the `CIB_FABRIC_NODE_DELTAS` treatment as predicted (`0x86a0` -> `0x8314`). 0 vendor runs. |
| `P2.T09`-`P2.T13`, `P2.T15` bel / packer / unpacker | **STAND** | Untouched by the source change; `AE350_SOC` sets zero fuses, exactly as EMCU does (`gowin_pack.py:4860`). |
| `P2.T18`, `P2.T19`, `P2.T21`, `P2.T38` PLL / core clock | **STAND** | Unaffected. Note run `p2t26-tilewires` drove all six clock ports from one ordinary fabric clock and the vendor accepted it, so `PLL_R[0].CLKOUT1` is a *reference-design* convention, not a tool-enforced constraint — `P2.T38` should measure that rather than assume it. |
| `P2.T20`-`P2.T23` bare `Emb_TCM` E0/E1 | **STAND, cheaper** | The full 149-port vehicle already builds; `Emb_TCM` is a strict subset. |
| `P2.T24` fuse set | **STANDS** | Expect zero, per EMCU. |
| `P2.T26` this checkpoint | **DONE** (this file) | |
| `P2.T27`-`P2.T31` dual-purpose pins, examples | **STAND** | Independent. |
| `P2.T32`-`P2.T36` evidence, `V14`/`V18`/`V20`, commit shape | **STAND** | |
| **`P2.T37` `EC5` differential discovery** | **VOID as written; replaced** | Its premise — one presence diff per bus, capped at 8, 141 buses to `residual` — is superseded. Replacement: `P2.T37'` = *validate the `.dat` table against one vendor bitstream*. Two runs are already banked (`p2t26-tilewires`, `p2t26-baseline`); `P2.T37'` spends **at most 2 more** to confirm that the decoded triples predict the moved-bit tiles, and writes `discovered-wires.json` from the table, not from a campaign. |
| `P2.T06` `slicing-plan.md` | **SUPERSEDED** in its source column | Every row reads `EC5-discovery`; after `P2.T08a` every row reads `Ae350SocIns/Outs table slice`. The file is a frozen input to `P2.T37` and is not edited — this file supersedes it. |

## Run budget

| | runs |
|---|---|
| cap for this line of work | 8 |
| spent by `P2.T26` | **2** (`p2t26-tilewires`, `p2t26-baseline`) |
| reserved for `P2.T37'` validation | 2 |
| remaining head-room | 4 |

Ledger: `$OTC/evidence/_budget/ae350-runs.tsv`. The `D50` phase box of 90 is
untouched; the clocking ledger closed at 269/290 and is not drawn on.

## What `P2.T08a` collapses (2026-09-07)

| task | new verdict |
|---|---|
| `P2.T08` | Reduced to a table read; the map is written. |
| `P2.T09`-`P2.T13`, `P2.T15` bel / packer / unpacker | Unchanged, but `P2.T09`'s port list now comes from `wire-map-138c.json` instead of being discovered. |
| **`P2.T37'`** validate the table against one vendor bitstream | **VOID, already done, 0 further runs.** The validation `P2.T37'` reserved 2 runs for is in `wire-map-138c.md` §4: 437 of 466 checked output bits name a wire whose pip really changes between `p2t26-tilewires` and `p2t26-baseline`. Nothing is left to buy. `discovered-wires.json` is superseded by `wire-map-138c.json`. |
| **`P2.T14`/`P2.T16`-`P2.T17`** (whatever remained of `EC5` discovery scaffolding) | Fold into `P2.T08`; there is no campaign to scaffold. |
| **NEW `P2.T08b`** the unmapped input bits | **DONE, 0 runs.** Neither guess was right: the bits are not unbound and there is no second table. `0x8314` is a *third* block's table — five of its columns show no changed bit in run `p2t26-tilewires`, which drives all 410 fabric-driven input bits from their own flops. The AE350's input table is at `0x91ea`, row 0 columns 159-180, the same tiles the block drives, over the disjoint `F`/`Q`/`OF` wire class. `read_ae350_soc_ins` now locates it by that geometry instead of addressing a base. 139 of the 142 map; 3 resist. `wire-map-138c.md` §6. |

Run budget after `P2.T08a`: **2 of 8 spent, 6 remaining** — the 2 reserved for
`P2.T37'` are released. `P2.T08b` spends none of them.

`P2.T08b` also invalidates one assumption `P2.T07` inherited: the block does not
read one half of its band and drive the other. It reads and drives the same
tiles, columns 159-180, so `fse_create_ae350()` must not anchor or bound the bel
on a split band. The `(0, 145)` anchor `P2.T26` recommends still stands as the
first column of the measured footprint, but the *port* columns are 159-180.

## Stop rule

If `P2.T08a` lands and the decoded `Ae350SocIns`/`Ae350SocOuts` triples still do
not reproduce the measured footprint (columns 145-181, ttyp 224/228), the row
closes at `E0` on the reduced port set of option 3 — the six clocks, the two
resets and the `Emb_TCM` subset — with the remaining buses named as residual.
An expired box delivers partial evidence, never a blank row.

RESCOPE-VERDICT (rev 3, after P2.T08b): 2 tasks void (P2.T37 and its replacement P2.T37'), 1 re-targeted and reduced to a table read (P2.T08), 1 amended (P2.T07 anchors at row 0 col 145, port columns 159-180, no split band), 1 new cheap task closed (P2.T08b: the input table is at 0x91ea, 139 of the 142 mapped, 3 resist); all others stand. Runs used 2 of 8, 6 remaining.

## Status after `P2.T23` (2026-09-07, `e1-138c.md`)

| task | status |
|---|---|
| `P2.T20` shape | **DONE**, re-targeted: `shapes/ae350_soc.py` is the ShapeSpec for the **149-port** vehicle, not the `Emb_TCM` subset the blueprint wrote it for — the subset is strictly less informative and no cheaper. |
| `P2.T21` vendor oracle run | **DONE, folded into `P2.T23`.** The batch runs `gw_sh` itself, so a separate oracle task has nothing left to do; the four artefacts and the pre-flight are the batch's head gates. The **package caveat is narrowed, not assumed away**: on PG484 the vendor places and routes `AE350_SOC` at `X159Y0` — the only site of its type on the die, so the package cannot move it. Whether the FPG676 reference designs name that same site is still unread; it cannot differ, because there is nowhere else for it to go. |
| `P2.T22`/`P2.T23` | **DONE at `E1`**, `verdict: ok`. |
| `P2.T24` fuse set | **DONE, and it does not go the way `P2.T24` recorded.** Two AE350 designs share **zero** interface-band bits (77 over 9 tiles against 3 at one tile), so no bit marks the block's presence: `get_AE350_SOC_fuses` returns `[]`, as `EMCU` does, and the per-design band is a named gap. 0 further vendor runs. |
| `P2.T25` `AE350_RAM` | **STANDS, and is now cheap.** Its blueprint priced ~10 vendor runs (1 baseline + 1 presence diff + up to 8 bus points); the presence-diff half is void for the same reason `P2.T24` is — a per-design band cannot be read as a fuse set — so `ae350_ram.py` is `ae350_soc.py` plus one `AE350_RAM` instance, and the row needs **1** vendor run, not ten. 4 of 8 spent, 4 remaining. |

RESCOPE-VERDICT (rev 4, after `P2.T23`): `P2.T20` done and re-targeted;
`P2.T21` folded in and its package caveat discharged; `P2.T23` closed at `E1`
with `verdict: ok`; `P2.T24` closed against its own expectation — no
unconditional fuse set exists; `P2.T25` re-priced from ~10 vendor runs to 1.
Runs used 4 of 8.
