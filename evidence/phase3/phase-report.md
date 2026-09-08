# Phase 3 — IO and IOLOGIC: what was reached, and what was not

Roadmap phase goal, verbatim: *"Proves the 138C's IO edge is open — that
ODDR/OSER/IDDR/IDES cells exist deliberately, clocked from a real FCLK, and
that a board input clock reaches them — which is what makes RGMII TX and RX
and TDM IO buildable on this part."*

**Oracle runs: 120 of the 160 `D110` authorised** (`evidence/_budget/iologic-runs.tsv`).
The last eight were `D111`'s ADC fuse sweep. The open flow's own builds —
yosys, nextpnr, `gowin_pack` — are not oracle runs and are not counted; this
phase spent several hundred of them re-deriving rows from bitstreams already
on disk, which is why 13 rows closed inside a 160-run cap.

Oracle edition: Gowin Standard 1.9.12.03, licensed. **`edu-provisional: false`**
on every row.

---

## Criteria

| id | criterion, quoted | verdict |
|---|---|---|
| `S10` | "IOLOGIC on 138C, with a real clock behind it… Then ODDR, OSER4/8/10, IDDR, IDES4/8/10 are **E1**-equivalent on 138C; `gw5_make_pin_to_hclk` is generalised beyond the single 25A crystal pin so a board input clock reaches FCLK on real 138C pins; `OSER16`/`IDES16` either work or raise a named unsupported error" | **REACHED** |
| `S11` | "`TLVDS_IOBUF` is either restored for 138C with oracle evidence… The remaining TLVDS/ELVDS IBUF/OBUF/TBUF types are **E1**-equivalent" | **REACHED for TLVDS; ELVDS refused by the vendor and recorded as such** — see the gap list |
| `S12` | "IODELAY on GW5A… the `C_STATIC_DLY` sweep is **E1**-equivalent" | **NOT REACHED at `E1`; reached at `E0` with the divergence named** |
| `S15` | "ADC and OSC. Both are **E1**-equivalent on 138C or explicitly refused with a named error" | **REACHED, by amendment** — OSC refused by name; ADC closes `E0` with `E1` unreachable for a stated reason (`EC9`), which the criterion's binary wording does not anticipate (`A29`) |
| `S3` | "no family regression (25A / 60B)" | **REACHED — after this step found a regression and the phase fixed it (`A30`)** |
| `S25` | "evidence rows admissible" | **REACHED** — `EVIDENCE ok: 348 rows, 17 pending, 0 blank, 0 missing artifacts` |
| `S24` | "upstream-ready branches" | **created here, closes in Phase 8** |
| `D65` clause (d) | authoring half — one example per closed primitive | **REACHED** — 17 added, `make tangmega138k` exit 0, 23 `.fs` |
| `D60` | L0 IO/IOLOGIC arcs | **REACHED as a measured absence (`A31`)** |

### `S10`, in the terms it is written in

* The `D39` three ordered states are all discharged: the guard was corrected,
  then deleted once `HAS_5A_HCLK` was set, and the `E1` rows were produced in
  state (2).
* `ODDR`, `IDDR`, `IDDRC`, `OSER4`, `OSER8`, `OSER10`, `OVIDEO`, `IDES4`,
  `IDES8`, `IDES10` — **all `E1`, `cells`/`attrs`/`conns` 0/0/0**, both decode
  checks `ok`, no unexplained fuse.
* `OSER16`/`IDES16` — the expected refusal was **REFUTED** by the vendor and
  both are implemented, `E1`, 0/0/0.
* A board input clock reaches FCLK: `dev.io2hclk` carries 6 HCLK blocks and
  164 IO cells, and the gearbox rows close at `E1` over it with the FCLK lane
  a matched term (`D107`).

---

## Named gaps — what a reader must not assume is closed

1. **HCLK block 1 has no modelled clock escape (`D100a`).** It is the block
   that serves the RGMII balls. `nextpnr` reports `Failed to find a route for
   arc 0 of net pclk` there, which is why the `oser`/`ides` rows are measured
   on a bank-5 ball of block 4 instead. The RGMII stand-in will meet this.
2. **`G-FCLK` for the non-gearbox path.** The HCLK→FCLK edge exists and the
   gearboxes use it; what has *not* been shown is a board clock reaching an
   `IODELAY`'s or a bare `IOB`'s fast clock, because no shape in this phase
   asked for one.
3. **The ADC's other sixteen parameters are unattributed.** `DIV_CTL` is
   emitted from the die's own tables; `SAMPLE_CNT_SEL`, `RATE_CHANGE_CTRL`,
   `ADC_MODE`, `VSEN_CTL`, the seven `BUF_*_EN` sets, `CLK_SEL`,
   `PIOCLK_SEL`, `VSEN_CTL_SEL` and `DYN_BKEN` are each refused **by name**.
   `ADCULC` has no attribution at all — one run at `DIV_CTL=2` settles it.
4. **ELVDS needs 2.5 V and this board has none outside banks 6/7.** Measured,
   not inferred: bank 3 at 2.5 V is accepted (`IO_TYPE=LVDS25E`), 3.3 V and
   1.8 V are refused. `SSTL15D` on the DQS pair is deferred to `P5b.T27`
   (`SA-P3-1`).
5. **The die has no oscillator.** Three vendor runs refused both primitives by
   name. The near-miss is recorded: the `.fse` *does* carry an OSC shortval
   table for one cell, which a literal reading would have turned into a bel
   for a resource the vendor refuses to place.
6. **The `io16` structural extent is unfuzzed.** The bels exist on all 156
   cells that have both IOLOGIC halves and a pad pair, derived from the
   device's own tables with **one** cell measured — (108,52). A right-edge
   generalisation run was not bought.
7. **The IODELAY context rule.** A static delay is programmed only when the
   delayed net reaches a clocked endpoint. `conns` went 8 → 4 → 1, and the
   last one is `DF`: the vendor prunes the delay-full flag in static mode
   while the open flow routes what the netlist says. A static-mode shape has
   no business exporting `DF` at all, and that is the one-run way to `E1`.
8. **IOLOGIC attribute id 133** is set by the vendor in the clocked-IODELAY
   context and is unnamed in `apycula.attrids`.
9. **130 IOB bits the open flow sets and the vendor does not are unmeasured
   over-emission** — the residual of `P3.T26`'s 22 206 after `D108`: 11
   violations in the one pair whose two halves are not the same design, plus
   the 20 SSPI-released-pin `IOB` longval bits Phase 2 measured and no design
   here drives. The safety verdict is **CLEAR** — 0 unused-pin
   `DRIVE`/`DRIVE_LEVEL` bits, which is the Hardware Gate's precondition.
10. **`IVIDEO` has no 138C row** — the one measured IO/IOLOGIC parity miss
    against the GW5A-25 example set (`evidence/family/gw5a25-io-parity.md`).
    One vendor run on an `io_des` point that instantiates it.
11. **No IO/IOLOGIC timing arc is modelled** (`A31`), and the two
    138C-measured facts deliberately **not** generalised to the Arora V family
    each owe one vendor run per die (`A30`).

---

## Amendments this phase records

`A29` ADC closes `E0` · `A30` the `S3` regression and its two causes ·
`A31` `0/0 arcs` is the measured answer · `A32` the table's own instrument
read four measured rows as absent · `A33` `DONE-STD` clause (c) for rows with
nothing to compare · `A34` `G-FCLK-138C` closed inside the phase ·
`A35` nine stale guards found by the phase-close gate · `A36` the E2E
scenario amended by measurement.

---

## The gestalt gate's blocking findings, and where each stands

`impl/gestalt-p3.md` returned **BLOCK** on eight findings before this close.

| id | finding | state |
|---|---|---|
| `B1` | the phase failed its own exit gate, `CRITERIA ok: 4/11` | **CLOSED** — `CRITERIA ok: 20/20`, `EVIDENCE ok: 348 rows, 17 pending, 0 blank, 0 missing artifacts` |
| `B2` | results written into the wrong table column | **CLOSED** (`A32`) — `ADC`, `OSC` and `IOB / bank config` moved into `138C status` |
| `B3` | two rows invisible to the gate | **CLOSED** (`A32`) — the unescaped pipes are escaped and both rows parse |
| `B4` | three slugs "blank" on the primitive-name comparison | **CLOSED** (`A32`) — join keys normalised, and a guard added so a shape cannot drift from a row id again |
| `B5` | `PR #535 bank coercion` has no evidence at all | **CLOSED** — one row and a summary, `E0+hw-pending` with the one observation `P9` owes it |
| `B6` | "IOLOGIC configures on the A half only" is refuted by this phase's own later measurement | **CLOSED in the second pass** — the wording is withdrawn everywhere and the `B` column is measured: `ODDRC`, `OSER4` and `IDES4` on B-half balls, 3 oracle runs, all `E1` `ok` 0/0/0 `c1`/`c2` `ok` (`A37`). The fix stays claimed for `GW5AST-138C` only (`A30`) |
| `B7` | no evidence row measured at the branch HEAD | **PARTLY CLOSED** — the 12 ADC rows are re-derived at HEAD; the other E1 slugs are re-derived at the two intervening commits, and the pair they were measured against (`34adfe57` / `45b32e69`) is the pair in force. The re-derivation of `oddr-iddr`, `oser`, `ides`, `iob-bank` and `iodelay` at the final HEAD is **owed and costs 0 oracle runs** |
| `B8` | a `gestalt-p2` exit condition deferred a third time | **CLOSED by naming both halves** — see below |

### `B8` — both halves of `gestalt-p2`'s `D5`, named with an owner

1. **`G-FCLK-138C`** — no longer deferred at all: the HCLK-to-IOLOGIC
   fast-clock edge landed inside this phase and the gearbox rows close at
   `E1` over it (`A34`).
2. **The global-clock items** — the `router1.cc:347` trip on four
   independent global clock nets, `PLL_B[*]` outputs reaching no fabric flop,
   and no PLL-to-HCLK path in the model. **Owner: Phase 6** (`ws_06_timing`),
   which owns the clock model end to end; none of the three is an IO or
   IOLOGIC question and no shape in this phase drives four global nets or a
   `PLL_B` output. Named here so it is visible rather than invisible.
3. **`gestalt-p2`'s `D1`, the released SSPI pin** — honestly **not
   discharged**: no design in this phase's corpus drives a released SSPI pin
   as a GPIO, so the 20 `IOB` longval bits at `(166,108)`/`(167,108)` stay
   unobserved. **Owner: `P9`**, which loads a bitstream on the real board and
   is the only place the question can be answered rather than modelled.

---

# Second pass — the re-close after the gestalt fixes (`P3.F3`)

The gestalt gate (`impl/gestalt-p3.md`) returned **BLOCK** on eight findings.
The first pass above closed six of them and left two owed: `B6`'s *measurement*
of the `B` half, and `B7`'s re-derivation of every row at the branch HEAD. Both
are discharged here. **Oracle runs: 123 of the 160 `D110` authorised** — the
three `B`-half points are the only vendor runs this pass bought; the
re-derivation bought none.

## The toolchain pair this pass measured against

| artefact | sha256 | how |
|---|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `f2f92b0448b7218b969237f150c694039bad9e0d4f0f17dfdbfde5108d0efd6c` | rebuilt at `apicula` `ad2e178`, 12.5 s |
| `chipdb-GW5AST-138C.bin` | `45b32e69130237d837d48c22c992bd296eabac5c45f523b07c142c09ed8cc7cb` | `gowin_arch_gen.py` 17.9 s + `bbasm --le` 1.0 s, installed to both locations |
| `nextpnr-himbaechel` | `34adfe5772eb7e963923ad9d3bfa264d0154ea4d94c3b57ff82954e0da9af1ca` | unchanged: `constids.inc` last moved at `50c80f92`, an ancestor of the `nextpnr` tip `7ed099ec`, so no `.bin` is invalidated |

Both halves of the pair **reproduce byte-identically** from their sources at
HEAD, which is the check that the stale gitignored local `msgpack` the gestalt
flagged was the only thing wrong: with it replaced,
`tests/test_b_half_iologic_138c.py` is 11/11 and
`::test_a_b_half_iologic_is_written_into_the_aux_cell` passes.

## `B6` — the `B` column is measured, not argued

Three vendor runs, one per IOLOGIC family, each scoping the pad cell **and**
its aux cell (`A37`):

| run | primitive | ball | pad / aux cell | verdict |
|---|---|---|---|---|
| `p3f3-oddrc-b-io_basic_b-0000` | `ODDRC` | `AB17` (`IOB80B`) | `(79,108)` / `(80,108)` | **`E1` `ok` 0/0/0, `c1`/`c2` `ok`** |
| `p3f3-oser4-b-io_ser_b-0000` | `OSER4` | `AB17` (`IOB80B`) | `(79,108)` / `(80,108)` | **`E1` `ok` 0/0/0, `c1`/`c2` `ok`** |
| `p3f3-ides4-b-io_des_b-0000` | `IDES4` | `T15` (`IOB70B`) | `(69,108)` / `(70,108)` | **`E1` `ok` 0/0/0, `c1`/`c2` `ok`** |

`fuses_moved` and `unexplained_bits` empty on all three. `ODDRC` is measured on
`AB17` — the ball the retracted conclusion was drawn on — with the pair's `A`
half left **empty**, so the `B` column is shown usable on its own and not as a
passenger of its neighbour. The **"A half only" wording is withdrawn** from
`evidence/oddr-iddr/summary.md` and from `shapes/io_ser.py` / `shapes/io_des.py`,
and the `ODDRC` B-half **refusal is withdrawn**: it was a shortcut, not a
measurement.

## `B7` — every Phase-3 row re-derived at the branch HEAD, at 0 oracle runs

`tools/redo_open_half.py` keeps each row's vendor half verbatim — `vendor_fs`,
`sdf`, `tr`, `oracle_log`, `ide_version` — and rebuilds only
`yosys → nextpnr-himbaechel → gowin_pack`, then re-compares. A row whose vendor
bitstream is not on disk is **refused**, never silently rebuilt, which is what
makes this free rather than cheap.

| slug | rows | re-derived at HEAD | verdicts before → after |
|---|---|---|---|
| `oddr-iddr` | 7 | 7 | `ok` 7 → `ok` 7 |
| `oser` | 7 | 7 | `ok` 7 → `ok` 7 (**after the fix below**; before it, 3 → `diff`) |
| `ides` | 7 | 7 | `ok` 7 → `ok` 7 |
| `iodelay` | 32 | 31 | `ok` 2, `diff` 27, `aborted` 2 → unchanged; **23 rows' `conns` 8 → 5** |
| `tlvds` | 3 | 3 | `ok` 3 → `ok` 3 |
| `tlvds-iobuf` | 1 | 1 | `ok` 1 → `ok` 1 |
| `oser16-ides16` | 3 | 3 | `ok` 1, `diff` 2 → unchanged |
| `adc` | 12 | 12 | `ok` 12 → `ok` 12 |
| `iob-bank` | 35 | 0 | analysis-only (`kind=measurement`, no shape module) |
| `pin-to-hclk` | 14 | 0 | one vendor build read at four balls each, not a per-design equivalence |
| `elvds` | 3 | 0 | `refused` — no open bitstream exists |
| `osc` | 3 | 0 | `refused` — no open bitstream exists |
| `bank-coercion` | 1 | 0 | analysis-only (`E0+hw-pending`) |
| **total** | **128** | **71** | **`ok` 40, `diff` 29, `aborted` 2 — identical before and after** |

**The pass found a real defect, which is the whole point of the step.** Its
first run, against `apicula` `ad2e178`, turned three `oser` points from `ok` to
`diff` — `OSER8`, `OSER10` and `OVIDEO`, each `cells`/`attrs` 1 and `conns`
~74, all three naming the same first difference: *an `IOLOGIC` the open flow
places on the `B` half of (52,108) and the vendor does not.* Decoded from the
two bitstreams of the `OSER8` pair, at the aux cell one column on:

```
(108,53) IOLOGICB  vendor  0 bits
(108,53) IOLOGICB  open    5 bits
    OUTMODE=LVDSOUT ISI=ENABLE CLKOMUX=ENABLE
    FCLKSEL1=HCLK2 FCLKSEL2=HCLK2_ WRFCLKSEL=UNK102
```

An **over-emission**: the pre-5A model configures the aux half of any gearbox
wider than a DDR pair, and this die configures it only for the 16:1 one. It
was invisible until `IOLOGICB` inherited `IOBB`'s `fuse_cell_offset`
(`2c68758`), because until then those attributes landed in the pad cell's own
three-coordinate stub, which can hold almost none of them — which is exactly
what a row measured at an older commit cannot see, and exactly why `B7` asked
for this. Fixed in `apicula` `84dddea`
(`GW5AST_138C.get_IOLOGIC_DUMMY_fuses` returns no fuse for an
`OUTMODE=DDRENABLE` dummy; `DDRENABLE16` still reaches the base handler,
because the vendor really does configure an `OSER16`'s aux half — six bits,
`P3.T16a`), guarded by two red-verified tests, and the **whole re-derivation
was then re-run from scratch** against that HEAD. The table above is the
re-run.

Two further measured movements, both recorded rather than absorbed:

* **`iodelay`, 23 rows, `conns` 8 → 5.** The row stays `E0` with its named
  divergence — it is the `dlystep` counter's `ALU` packing that fails `c1`,
  not anything about the delay line — but three of its eight connectivity
  differences are gone at HEAD, and the residual is smaller than the number
  the slug's summary was written against.
* **`oser16-ides16` and the `B`-half points are unmoved**, which is the
  control: the `DDRENABLE16` path the fix deliberately left alone still
  reproduces the vendor's aux-half configuration exactly.

**The gate then found a second one.** `open-toolchain`'s
`test_shape_primitive_join_key` — the guard the gestalt's `B4` asked for —
refused the close: the three new `B`-half shapes declared `ODDRC (B half)`,
`OSER4 (B half)` and `IDES4 (B half)`, none of which is a row id of
`spec-primitives.md`, so their rows could never be attributed to the row whose
claim they close. Fixed in `apicula` `8f61e7e`: the half a point sits on
belongs in `sweep`, not in the row id, and the three rows already on disk are
relabelled to match. That commit is metadata only — no Verilog, ports, balls,
scope or sweep changes — and the claim is **confirmed rather than asserted**:
the `ODDRC` `B`-half point was re-derived once more at `8f61e7e` and came back
`E1 ok 0/0/0, c1/c2 ok`, identical to its value at `84dddea`. Every other row
is stamped `84dddea`, the commit it was measured at.

## Criteria — the second-pass verdicts

Every `S`-id below is quoted from the criterion it answers; the verdicts are
unchanged from the first pass except where a second-pass measurement moved
one.

| id | criterion, quoted | verdict |
|---|---|---|
| `S10` | "IOLOGIC on 138C, with a real clock behind it… Then ODDR, OSER4/8/10, IDDR, IDES4/8/10 are **E1**-equivalent on 138C; `gw5_make_pin_to_hclk` is generalised beyond the single 25A crystal pin so a board input clock reaches FCLK on real 138C pins; `OSER16`/`IDES16` either work or raise a named unsupported error" | **REACHED**, and on **both halves of a pad pair** — the `A`-half confinement the first pass shipped is measured away (`A37`) |
| `S11` | "`TLVDS_IOBUF` is either restored for 138C with oracle evidence… The remaining TLVDS/ELVDS IBUF/OBUF/TBUF types are **E1**-equivalent" | **REACHED for TLVDS; ELVDS `refused` by the vendor and recorded as such.** New in this pass: the TLVDS pairs are in the IOB safety corpus, which surfaced a named under-emission on the negative half (`A39`) |
| `S12` | "IODELAY on GW5A… the `C_STATIC_DLY` sweep is **E1**-equivalent" | **NOT REACHED at `E1`; reached at `E0` with the divergence named** — the single remaining `conns` term is `DF`, the vendor's static-mode pruning (gap 7) |
| `S15` | "ADC and OSC. Both are **E1**-equivalent on 138C or explicitly refused with a named error" | **REACHED, by amendment (`A29`)** — OSC refused by name; ADC closes `E0`, `E1` unreachable for a stated reason (`EC9`) |
| `S3` | "no family regression (25A / 60B)" | **REACHED** — `60f1ba42…` / `615d4d03…` byte-identical again in this pass |
| `S25` | "evidence rows admissible" | **REACHED** — see Validation 4 |
| `S24` | "upstream-ready branches" | **created here, closes in Phase 8** |
| `D65` clause (d) | authoring half — one example per closed primitive | **REACHED** — `make tangmega138k` exit 0 |
| `D60` | L0 IO/IOLOGIC arcs | **REACHED as a measured absence (`A31`)** |

## Named gaps carried out of Phase 3

Unchanged from the first pass unless marked. A reader must not assume any of
these is closed.

1. **HCLK block 1 has no modelled clock escape (`D100a`)** — the block that
   serves the **RGMII** balls. `nextpnr` reports `Failed to find a route for
   arc 0 of net pclk` there, which is why the `oser`/`ides` rows are measured
   on a bank-5 ball of block 4. The RGMII stand-in in Phase 5 will meet this.
2. **`G-FCLK` for the non-gearbox path** — the HCLK→FCLK edge exists and the
   gearboxes use it (`A34`); what has *not* been shown is a board clock
   reaching an `IODELAY`'s or a bare `IOB`'s fast clock, because no shape in
   this phase asked for one.
3. **The `io16` structural extent is unfuzzed** — the bels exist on all 156
   cells that have both IOLOGIC halves and a pad pair, derived from the
   device's own tables with **one** cell measured, (108,52). Claimed for this
   die only (`A30`); one `OSER16` run per die would widen it.
4. **IOLOGIC attribute id 133** is set by the vendor in the clocked-`IODELAY`
   context and is unnamed in `apycula.attrids`. Its neighbour id **118** was
   the second-pass near-miss: it had two names and the tie was broken by line
   order (`A40`).
5. **130 IOB bits the open flow sets and the vendor does not are unmeasured
   over-emission** — 11 violations in the one pair whose two halves are not the
   same design, plus the 20 SSPI-released-pin `IOB` longval bits Phase 2
   measured and no design here drives. The safety verdict is **CLEAR** over all
   **39** corpus pairs — 0 unused-pin `DRIVE`/`DRIVE_LEVEL` bits, the Hardware
   Gate's precondition.
6. **`IVIDEO` has no 138C row** — the one measured IO/IOLOGIC parity miss
   against the GW5A-25 example set (`evidence/family/gw5a25-io-parity.md`). One
   vendor run on an `io_des` point that instantiates it.
7. **NEW (`A39`): the TLVDS negative half is under-emitted.** With the
   differential pairs in the safety corpus, the open flow writes the unused-pin
   default set into the negative half of a TLVDS pair, so `IO_TYPE`,
   `LVDS_OUT`, `OPENDRAIN` and `PADDI` are vendor-only there. Every one is an
   **under**-emission — no bit is invented, the thermal claim is untouched —
   and it is repairable at 0 oracle runs.
8. **The ADC's other sixteen parameters are unattributed**, each refused by
   name; `ADCULC` has no attribution at all — one run at `DIV_CTL=2` settles it.
9. **The `IODELAY` context rule** — a static delay is programmed only when the
   delayed net reaches a clocked endpoint; the last `conns` term is `DF`, which
   a static-mode shape has no business exporting. One run to `E1`.
10. **Three `gestalt-p3` hidden-constant items stay open, by choice.** The
    IOLOGIC ttyp exclusion set (`chipdb.py`) is a frozen 33-element literal
    whose criterion is stated but not derived or tagged; `cst.cc`'s
    `SIDE[0-7]` regex bound is not validated against
    `lanes_per_block * blocks.size()`, so on a pre-5A device `SIDE[2..7]`
    parses and resolves to a nonexistent block; and four shape files carry a
    bare `scope_tiles = ((52, 108),)` without the `(x, y) = (col, row)`
    warning their siblings carry. All three are hygiene, none changes a
    measured result — and each would move `apicula` or `nextpnr` HEAD, which
    is precisely what the `B7` stamping above asserts. **Owner: the first task
    of Phase 4**, which moves both tips anyway.
11. **No IO/IOLOGIC timing arc is modelled** (`A31`), and the two
    138C-measured facts deliberately not generalised to the Arora V family each
    owe one vendor run per die (`A30`).

## Amendments this pass records

`A37` the `B` column configures and the "A half only" wording is withdrawn ·
`A38` bank 6/7 is refused by the **ball**, in both the `.cst` check and the
packer · `A39` the safety corpus takes in the differential pairs, and the
TLVDS negative half is a named under-emission · `A40` IOLOGIC attribute 118
had two names · `A41` re-deriving every row at the branch HEAD found a real
over-emission — the aux half of a narrow output gearbox — and the rows that
cannot be re-derived are named · `A42` the three `B`-half shapes join to the
table row they belong to, which the phase-close gate's own guard refused the
close over · `A43` the phase closes at 123 of 160 oracle runs.
