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
| `P2.T07` `fse_create_ae350()` skeleton | **STANDS, amended** | The `(0,0)` fallback in the HOW is now wrong: the footprint is measured at columns 145-181. Anchor the bel in that band, not at `(0,0)`. |
| `P2.T08` slice `McuIns`/`McuOuts` into ports | **RE-TARGETED** | Same `make_port` code path, different source: `dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts']`, triples `(row, col, wire)` 1-based, exactly as `fse_create_adc` (`chipdb.py:2489-2492`) consumes `Adc25kIns`. The task's three tests survive unchanged. |
| **NEW `P2.T08a`** fix the `read_scaledGrid16` call-site transposition | **BLOCKING PREDECESSOR** | `dat_parser.py` is frozen in Phase 2, so this lands in its owning phase under the standing order. Fixes `Ae350SocIns/Outs` **and** every `Mipi*`, `Gtrl12*`, `*DdrDll*`, `Cmsera*`, `Adc*RC*` entry at `:525-546` and `:601-650`, all of which read noise today. Needs the `CIB_FABRIC_NODE_DELTAS` treatment for the `Ins` delta, which is stale. 0 vendor runs. |
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

## Stop rule

If `P2.T08a` lands and the decoded `Ae350SocIns`/`Ae350SocOuts` triples still do
not reproduce the measured footprint (columns 145-181, ttyp 224/228), the row
closes at `E0` on the reduced port set of option 3 — the six clocks, the two
resets and the `Emb_TCM` subset — with the remaining buses named as residual.
An expired box delivers partial evidence, never a blank row.

RESCOPE-VERDICT: 1 task void (P2.T37), 1 task re-targeted (P2.T08), 1 new blocking predecessor (P2.T08a, in dat_parser's owning phase), 1 amended (P2.T07); all others stand. Runs used 2 of 8.
