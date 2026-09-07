# `AE350_SOC` — evidence summary

`P2.T34` roll-up. Three rows in `runs.jsonl`; ledger `evidence/_budget/
ae350-runs.tsv` (6 of 8 spent on this line of work).

## Run counts and verdict distribution

| run_id | level | verdict | note |
|---|---|---|---|
| `ae350-route-0001` | E0 | aborted | `P2.T22`: routes and packs, but no `ShapeSpec` existed yet for the 149-port vehicle, so only whole-device `--calibration` ran |
| `ae350-row-0001` | E1 | ok | `P2.T20`/`P2.T23`: the row closes -- `shapes/ae350_soc.py`, 0 cells/attrs/conns in the block's band and the `PLL_R[0]` site, `c1` 1780/1780 (1781/1781 on re-measurement, see below), `c2` byte-identical |
| `ae350-soc-s19-hw-0001` | E0 | ok | `P2.T33`: `S19`(hw) sub-criterion, `E0+hw-pending` -- see "Deferred observations" below |

3 runs: 1 `aborted`, 2 `ok`. 0 `diff`, 0 `refused`.

## Artefact paths and sha256

| run_id | field | path | sha256 |
|---|---|---|---|
| `ae350-route-0001` | `vendor_fs` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-tilewires/run/impl/pnr/run.fs` | `2f0c74d259ea8251b280cf11bd1c43eb95a34a384e94da44d7aeccec9ae54441` |
| `ae350-route-0001` | `open_fs` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-open-e0/top.fs` | `b07b3ed496591f44f3436d45dde5dbf0d2ad47596ba0b96eb53cea3df558e315` |
| `ae350-row-0001` | `vendor_fs` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000/run/impl/pnr/run.fs` | `1b032a4b61dc8e0062b9fa88d5a52bf412b51e8c643de42f2eb20b8d355a27d5` |
| `ae350-row-0001` | `open_fs` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000/top.fs` | `6d91d0c816ff01418b20b31432f8c273d237df82404df9e35113a840f729622c` |
| `ae350-row-0001` | `tr` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000/run/impl/pnr/run.tr` | `f94fd4ce1f15267b54627d5a9c1a4198e33445405e0e429bc1aa57923299b2a7` |
| `ae350-row-0001` | `sdf` | `/Users/alex/fine-line-data/open-toolchain-gw5ast/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000/run/impl/pnr/run.sdf` | `9c0d9c3c9989e503db2a0f37d5bf914675c7c2b5bb179179f37fead4ab42c8b7` |
| `ae350-soc-s19-hw-0001` | -- | none: a bookkeeping row, no oracle run of its own | -- |

Every path above was verified to exist and hash-match at roll-up time
(`test_summary_sha256s_resolve`); no `run/` tree under the datastore's
`ae350*` directories is yet older than 24h (all dated 2026-09-07, this
session), so `P2.T34`'s storage-hygiene pass reclaimed **0 bytes** this run
-- the trees are cited by the sha256s above and stay until their 24h mark.

## Deferred observations (Phase 9)

`ae350-soc-s19-hw-0001` (`level: E0`, `verdict: ok`) carries the literal
token `E0+hw-pending` and names both observations `S19`(hw) still owes:

- `BUILD_LOAD` ELF loaded over the separate user-I/O debug TAP
- UART2 transcript

`spec-primitives.md`'s `AE350_SOC` cell records this alongside the row's
own `E1` status (`P2.T33`).

## Structural facts (`V18`, `check_criteria.py --ae350`)

`AE350 ok: 4/4`, and every clause is now decided from the chipdb, from
`gowin_pack` or from a machine-readable field -- none of them from a sentence
this phase wrote.

- bel/port-map present: 416 in / 495 out bits at `(0, 159)`, 884 bound.
- `CLKOUT1 -> CORE_CLK` is a fixed connection: one **fuseless** pip per PLL
  site (`PLL_L[0]` and `PLL_R[0]` alike, `core-clock.md`) into a dedicated
  wire of the anchor cell, and the fabric tap `(0, 87, CLK1)` is recorded but
  bound to nothing. The check fails if either site's edge is missing, if a hop
  costs a bit, or if the port can still reach the tap.
- fuse set **zero, measured** (`fuse-set-138c.md`): 0 unmodelled set bits in
  tile types 224/228 over five AE350 bitstreams and one AE350-free control.
  The earlier "77 bits" were `shortval:LUT`/`CLS*` fuses of ordinary logic;
  `e1-138c.md` S3's intersection argument is superseded.
- wire reconciliation `0/911 wires covered by 637 McuIns/McuOuts entries`,
  with the 911 cross-checked against the live port map.

## Re-measurement after the Phase-2 gestalt gate (`P2.F1`, 0 vendor runs)

The `P2.T23` vehicle was rebuilt through the open flow against the same
preserved vendor bitstream: **`EQUIV E1 ok`**, 0 cells / 0 attrs / 0 conns,
`unexplained_bits` empty, `fuses_over_emitted` empty, `c1` **1781/1781** (the
`AE350_SOC` cell now required and recovered by `gowin_unpack.parse_ae350`),
`c2` byte-identical. Toolchain pair for that run: apycula chipdb
`7f3c64c9...`, himbaechel `chipdb-GW5AST-138C.bin` `4c520c58...`,
`nextpnr-himbaechel` `d400514b...`.
