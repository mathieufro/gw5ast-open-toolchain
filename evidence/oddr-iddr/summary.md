# ODDR / IDDR on GW5AST-138C

chipdb_sha256: f2f92b0448b7218b969237f150c694039bad9e0d4f0f17dfdbfde5108d0efd6c

The chipdb the phase closed on, recorded here because `V14` and `V12a` both
read it: without this line either gate could pass against an earlier phase's
artefact, since `chipdb_builder`'s default output path is shared by every phase.


## Verdict

All six `oddr-iddr` sweep points reach `verdict: ok` at `E1` (`cells`/`attrs`/`conns`
0/0/0, both decode checks `ok`, no unexplained fuse). Two named gaps (a GW5A gearbox
output-window pin-swap, an IO-tile wire alias) were fixed at 0 extra oracle-run cost. No
IO/IOLOGIC timing arc is modelled for this die, by measurement not omission -- see
L0-IO-ARCS.

## GUARD-STATE & TTYP-ADJUDICATION (`D39`/`P3.T03`, `P3.T04`)

`D39` state 2 landed: the corrected early exit (`if device in {'GW5AST-138C'}: return
bels`) is deleted from `apycula.chipdb.fse_iologic`, so `IOLOGICA`/`IOLOGICB` are
created from `fse[ttyp]['shortval']` keys 21/22 as on every device (`GW5A-25A` gate
`{48, 51, 263, 392, 399}` untouched). `chipdb_sha256: 1c508c92f...` (superseded below);
`HAS_5A_HCLK` present, clocked via Phase-1's FCLK flag.

**47 candidates, 14 accept, 33 reject, 0 disagreements** (`ttyp-adjudication.tsv`, `derive_iologic_ttyps_138c.py`, log `p3-iologic-ttyp.log`). Exclusion set: `{60, 178, 179, 182, 183, 184, 185, 220, 239, 240, 242, 244, 246, 248, 250, 252, 253, 254, 255, 274, 278, 279, 280, 281, 282, 283, 284, 285, 374, 378, 379, 380, 381}`. Derived: a rejected ttyp has no `IOB` bel (post `fill_GW5A_io_bels`) **and** no bonded pin in `PBGA484A`/`PBGA676A`/`FCPBGA676A`. Target package `PBGA484A` has no top-side IO pins: ttyp 242 (155 cells, top edge) alone gave 310 of the 740 orphan bels. Accept side confirmed by placement (`P3.T05`) and `P3.T07`'s 12 vendor runs.

| quantity | before gate | after gate |
|---|---|---|
| `IOLOGICA` | 534 | **164** |
| `IOLOGICB` | 532 | **162** |
| total | 1066 | **326** |
| distinct ttyps | 47 | **14** |

164 `IOLOGICA` = pinned surface: 168 cells carry an `IOB` bel, four being corner types
`{48, 49, 50, 51}` the generic gate already drops.

## NEXTPNR-CHIPDB (`P3.T05`)

Rebuilt from the apicula chipdb above (generator run only). Blueprint's literal `bbasm
--e` is wrong (`--e` selects `#embed`; needs `--le`/`--be` per
`cmake/BBAsm.cmake`/`P0.T16b`).

| artefact | sha256 | bytes |
|---|---|---|
| `.bba` | `a494b58e5722...` | 91,674,955 |
| `.bin` | `9cce739de583...` | 33,569,367 |
| `nextpnr-himbaechel` (unchanged) | `d400514b6f35...` | - |

`chipdb_sha256: 6a776c745d63...` (of `.msgpack.xz`; supersedes `P3.T03` line). Installed
at all three locations; `constids.inc` untouched, so `d400514b` stays the valid partner
(`D101`).

Bel probe (`iddr-boardclk.v` placeholder for `P3.T09`, `IDDR` on `uart_rx` V14/V22
clock, `Q0`/`Q1` on `led[0]`/`led[1]`), exit 0, 0 `^ERROR`: `IOLOGICI` 1/326 used/avail,
`IOLOGICO` 0/326, `IOB` 4/324 -- 326 = apicula's post-gate surface, nothing
lost/invented. `CHIP_HAS_5A_HCLK` flags word = **87937 = 0x15781**, `&0x10000` set. `S3`
guard: GW5A-25A / GW5AT-60B msgpacks (`60f1ba427f...`, `615d4d0349...`) byte-identical
to record -- gate is device-guarded.

## ATTRIBUTE-AUDIT (`P3.T11`)

**2 oracle runs** (task cap), four primitives: one design `ODDR`+`ODDRC`, other `IDDR`+`IDDRC` (`C` variants add `CLEAR`, no parameter). Driver `audit_oddr_iddr_attrs.py`; log `p3-oddr-iddr-audit.log`. HCLK-clocked variant not run, by measurement: `G-FCLK-138C` (`P3.T08`) found no HCLK->FCLK edge, none of 12 vendor bitstreams configures `FCLK*` -- vendor clocks IOLOGIC over `BUFG`/global, as both designs do.

Instrument: `gowin_unpack` surfaces only `MODE=`/`CLKODDRMUX_ECLK=`; audit re-decodes
and computes each side's fuse set via `gowin_pack`'s own path -- the verdict is the fuse
set, not the attribute list. Matched by ball, never `MODE=` (`gowin_unpack.py:806-830`
tells `ODDR`/`ODDRC` apart only by `LSROMUX_0`'s presence, and this die sets
`LSROMUX_0=0` on plain `ODDR` too -- a mislabelling, recorded not worked around).

| primitive | ball | tile | vendor attributes | vendor fuses |
|---|---|---|---|---|
| `ODDR` | `AB16` | `(79,108)A` | `OUTMODE=MODDRX1`, `CLKOMUX=ENABLE`, `LSROMUX_0=0`, `LSRIMUX_0=0` | `(20,59) (21,54) (21,112) (21,113)` |
| `ODDRC` | `AB17` | `(79,108)B` | none decoded (B-half gap, below) | none |
| `IDDR` | `AA15` | `(82,108)A` | `INMODE=IDDRX1`, `CLKIMUX=ENABLE`, `LSRIMUX_0=0`, `LSROMUX_0=0` | `(21,15) (21,104)` |
| `IDDRC` | `W15` | `(71,108)A` | `INMODE=IDDRX1`, `CLKIMUX=ENABLE`, `LSRMUX_LSR=INV`, `LSROMUX_0=0` | `(21,15) (21,49) (21,56) (21,104)` |

`attr-gap.tsv`/`fuse-delta.json`: per-attribute cost, before `P3.T12`'s handler fix.
138C-specific differences:

| attribute | attrid | fuse(s) | vendor vs generic | disposition |
|---|---|---|---|---|
| `GSR` (all) | 5 | `(21,119)` | vendor clears; generic emits `DISGSR` unconditionally with no `GSREN` | **handler** -- emit `GSR` only on explicit `GSREN=TRUE` |
| `LSRMUX_LSR` (`IDDRC`) | 19 | two | vendor `INV`->`(21,56)`, no `LSRIMUX_0`; generic `SIG`->`(21,49)` | **handler** |
| `OUTMODE` | 1 | none | vendor `MODDRX1` vs `gowin_pack` `ODDRX1`, same fuses | **unexplained-justified** (naming) |
| `TSHX`/`LSRIMUX_0`/`LSROMUX_0`/`CLKODDRMUX_ECLK=UNKNOWN` | -- | 0 | zero code of the attribute | **unexplained-justified**; forced by `G-FCLK-138C`, costs nothing |

**Named gap: B half of an IO tile has no IOLOGIC fuse table.** `ODDRC` on `IOB80[B]` decodes nothing: `db.shortval[247]['IOLOGICB']` holds 3 fuse coords against `IOLOGICA`'s 100, none set (the nine bits `ODDR` moves there are `pip`/routing, not IOLOGIC). Same on GW5A-25A (one populated table --676 keys/90 coords-- and one stub --2/2 -- per IO tile) -- a database property. On ttyp 247 IOLOGIC configures on the A half only; every `P3.T12` point lands on an A-half ball (`AB16`, `AA15`), so B half is a stated limit carried into `P3.T13`/`P3.T14`.

## SWEEP (`P3.T12`)

**6 oracle runs** (task cap), `io_basic.py` `POINTS` (`oddr-default`, `oddr-txclk-pol`, `oddr-init`, `iddr-default`, `iddr-q0-init`, `iddr-q1-init`). Log `p3-oddr-iddr.log` (`runs=6 ok=0 diff=6 aborted=0`); rows `runs.jsonl`. Re-derived by `recompare_rows.py` after the fixes below, at no further oracle cost.

Packer now writes exactly the vendor's IOLOGIC fuses, measured at `IOLOGICA` tile 247:

| primitive | vendor fuses | before | after |
|---|---|---|---|
| `ODDR` | `(20,59) (21,54) (21,112) (21,113)` | +`(21,119)` | identical |
| `IDDR` | `(21,15) (21,104)` | +`(21,119)` | identical |
| `IDDRC` | `(21,15) (21,49) (21,56) (21,104)` | +`(21,119)`, -`(21,56)` | identical |

**Three defects uncovered, all fixed here:**

| defect | root cause | fix |
|---|---|---|
| `split_bel_name('IOLOGICAO')` -> `('IOLOGICA', 14)` | generic rule reads trailing capital as A/B letter; IOLOGIC bel name ends in direction | matched to decoded `('IOLOGIC', 0)` |
| `E1` had no path for an IOLOGIC | site is a bitstream address, not `CLS`, so `INS_LOC` couldn't constrain it | joins `CLKDIV2`/`CLKDIV`/`PLL` in `BITSTREAM_ADDRESSED_CELL_TYPES`; closes on `X79Y108/IOLOGICAO` (`X82Y108` input) |
| `io_basic` named no comparison scope | empty tile list read as empty set, `E0` vacuous; whole-die scope unavailable (vendor decodes 138 576 cells vs open's 384, MEASURED) | scope is the two data balls' own cells, `(79,108)`/`(82,108)` |

**The one term not closed:** all six rows `E1`, `c1`/`c2` ok, `cells`/`attrs`=0, `unexplained_bits=[]` (`EVIDENCE ok`), yet every row `verdict: diff` on six `conns` (same keys both sides, identical net partition, different identities) -- context flops placed independently because GowinSynthesis renames the instance (`din_r`->`din_r_s0`) and `equiv.insloc_lines` refuses to constrain an unrecognised name (`gw_sh` aborts `ERROR (CT1135)` otherwise): free placement, admitted at `E0`, not `E1`. **Fix needs runs this task lacks:** drive `D0`/`D1` from two package balls instead of a fabric flop + inverse, no fabric cell, `conns` closes -- six new runs against a cap of six already spent, a priced budget deviation recorded here; packer/decode/`E1` evidence stand either way.

## SWEEP, SECOND PASS (`P3.T12` fix, `D105`)

`D105` authorised six more runs (`p3-oddr-iddr-b.log`, `runs=6 ok=3 diff=3 aborted=0`).
Shape now has **no fabric cell at all**: `ODDR.D0`/`.D1` off two balls, `Q0` drives a
third; `IDDR.D` off its pad, `Q0`/`Q1` drive two balls. Two balls added (`T16`, `W16`,
`T15`, bank 5).

| point | verdict | cells/attrs/conns | c1/c2 |
|---|---|---|---|
| `oddr-default` | ok | 0/0/0 | ok/ok |
| `oddr-txclk-pol` | ok | 0/0/0 | ok/ok |
| `oddr-init` | ok | 0/0/0 | ok/ok |
| `iddr-default` | diff | 0/0/4 | ok/ok |
| `iddr-q0-init` | diff | 0/0/4 | ok/ok |
| `iddr-q1-init` | diff | 0/0/4 | ok/ok |

`ODDR` half closed: `conns` 6->0, `diff`->`ok`.

**IDDR residual is a different, sharper defect.** MEASURED identically on all three points: vendor connects `IOLOGIC(82,108).Q14` to `IOB(79,108).I` (pad carrying `Q0`) and `Q8` to `IOLOGIC.SETN`; open connects `Q8` to the pad, `Q14` to its own net (`Q8`=wire `F0`, `Q14`=`F7`, both flows occupy both wires). `nextpnr` renames `IDDR.Q0`->`Q8`, `Q1`->`Q9` (`pack_iologic.cc:277-281`), so open's pad carries `Q0`, vendor's `Q14` -- the deserialiser's outputs are swapped on one flow, functional not placement. Needs the vendor's fabric-wire->`Q_i` map, decoded free by the **IDES** row (`P3.T14`) over three widths/ten pads; `test_oddr_iddr_rows_e1` carries a strict `xfail`.

## L0-IO-ARCS (`P3.T32`/`P3.T33`, then `P3.T34`)

**No IO/IOLOGIC timing arc emitted, by measurement not omission.** `tm_parser.parse_io` (`.tm` `0x3278`) / `parse_iregoreg` (`0x306c`) return `NoData`, so no arc reaches the chipdb: (1) both blocks are inherited GW2A bytes, byte-identical across GW2A-18/-55, GW2AR-18, GW5A-25A, GW5AT-60B, GW5AST-138C (chunk 0 differs from GW2A-18 in 81 bytes, all at/after `0x3738`, only the IODELAY-tail re-characterised for GW5A); (2) the numbers contradict the vendor's own 138C SDF: `OBUF I->O` is 2.528/2.737 ns vs a block max of 0.819 ns; none of three clock-to-out candidates (1.019/1.213, 0.945/1.289, 0.635/0.831 ns) lands within +-10% of `ODDR CLK->Q` 1.160/1.146 or `IDDR CLK->Q0/Q1` 0.572/0.486. Every vendor arc is reported unmapped rather than compared to an invented model.

Run of record (`P3.T34`, this phase's SDF, `-device_version C`, `max`), exit 0: `L0 ok:
0/0 arcs within +-10%, 0 exceptions listed`; grade `C1/I0 -- derived (1.25 x C2/I1,
P0.T35 -- NOT measured)`; 5 unmapped arcs (`ODDR/dut CLK->Q0/Q1`, three `IBUF`/`OBUF
I->O`). Same `0/0` verdict `P3.T33` recorded against `p3t11/iddr-pair` (12 unmapped
arcs, incl. `IDDR`/`IDDRC CLK->Q0/Q1`, `CLEAR->Q0/Q1`, four `IBUF I->O`) -- empty
because the model publishes no IO arc, not because every arc passed (not a claim the
138C has no IO timing anywhere: `read_tm` stops before chunk 3, Phase 6's question
`S17b`). Contract tests: `test_v12a_io_output_contract`,
`test_v12a_io_exceptions_enumerated`.

## The GW5A gearbox output window, and the wire alias it exposed

Open flow put `IDDR.Q0` on bel pin `Q8` (wire `F0`); vendor takes data out on `F7`
(`Q14`). MEASURED from vendor bitstreams on disk:

| primitive | vendor bel pins | wires | pre-5A map (wrong) |
|---|---|---|---|
| `IDDR`/`IDDRC` | `Q14`-`Q15` | `F7`, `OF0` | `Q8`-`Q9` |
| `IDES4` | `Q8`-`Q11` | `F0`-`F3` | `Q6`-`Q9` |
| `IDES8` | `Q8`-`Q15` | `F0`-`F5`, `F7`, `OF0` | `Q2`-`Q9` |
| `IDES10` | `Q6`-`Q15` | -- | `Q0`-`Q9` |

GW5A IOLOGIC carries 16 fabric outputs (older families: 10); windows are not a constant
shift (`IDDR`/`IDES8`/`IDES10` top-align at `Q15`, `IDES4` does not). `IVIDEO` has no
measured bitstream, keeps the pre-5A window. Landed (`nextpnr`
`reconnect_ides_outs`/`gowin_unpack._iologic_ports_gw5`), re-diffed at **no** oracle-run
cost: `ODDR` points stay `ok`; `IDDR` points go `conns` 4->2, `cells`/`attrs` 0.
Remainder: both flows drive `IOLOGIC.Q14`, but only vendor's is in the `dout` net --
open route `F7 -> EW10 -> ... -> W11` has one hop the tile decode doesn't reconstruct
(`W11` not a pip destination in ttyp 247, nothing joins it to `EW10`), splitting the
net. Named gap: **IO-tile wire alias missing from the 138C chipdb (`EW10`/`W11`, ttyp
247)**, a Phase-1-owned `chipdb.py` question.

Closed at **0 further oracle runs** (`P3.F2`): the alias was missing from
`chipdb.wire2global`, not device data -- a tile's `EW10` is the same metal its eastern
neighbour calls `E111`, western `W111` (`SN10` the vertical pair, `..20` the second wire
of each axis), all pip endpoints in ttyp-247's table and already correlated by
`tracing.source_intertile_wire`, but `wire2global` gave them three different node names,
splitting any net routed over such a wire. `chipdb.intertile_aliases` now maps the eight
length-1 root names onto the two they share; `nextpnr` needed no change.

**Result: all six points `verdict: ok`, `cells`/`attrs`/`conns` 0/0/0, both decode checks ok.** `IDDR` points go `conns` 2->0; `ODDR` points stay `ok`. The row closes at `E1` with nothing open.
