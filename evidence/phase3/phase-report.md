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
