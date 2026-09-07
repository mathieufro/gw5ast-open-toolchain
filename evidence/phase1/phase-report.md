# Phase 1 — Clocking: phase report

Closed 2026-09-07 on `epic/gw5ast138c` (apicula `ab350d4`, nextpnr `7dd337bb`)
and `open-toolchain` `main`. 221 oracle runs of a 290-run box. The one full
gate per phase (`C12`) is green in all three repos; `blueprints/P1-clocking.md`
§Validation is in `validation.md` beside this file.

Phase goal, as the roadmap states it: *a real, open-toolchain clock on the
138C*. It exists and it is proven at `E1` end to end — one design, both flows,
placement-identical: board clock → `DHCE` → HCLK block 5 lane 0 → `CLKDIV`
`DIV_MODE=4` → `DQCE` on the quadrant spine → fabric, with `PLL_L[0]` running
beside it.

---

## 1. Exit criteria

| criterion | verdict |
|---|---|
| `S7` — the device's PLL primitive on 138C | **REACHED** (named gaps below) |
| `S8` — HCLK / CLKDIV / CLKDIV2 on 138C | **REACHED** (`CLKDIV2` at `E0` by construction) |
| `S9` — DHCE / DQCE / DCS | **NOT REACHED** — `DHCE` and `DQCE` closed, `DCS` does not route |

### `S7` — the device's PLL primitive on 138C: **REACHED**, with named gaps

> "All 12 PLLs (DS1239E Table 1-1) have slots and bels; `get_permitted_pll_freqs`
> is implemented for `GW5AST_138C` … as the full documented five-tuple
> `(800., 1000., 5.079, 1300., 650.)`; apicula issue #427 (FVCO) is fixed with a
> regression test; the swept configuration set is **E1**-equivalent."

| clause | evidence |
|---|---|
| 12 slots and bels | `test_plla_bel_count_138c_is_12` (unit suite, validation §5); sites measured one by one in `evidence/plla/sites-138c.md`, bijection `PLL_L/R/B[0..3]` ↔ anchors from 12 oracle runs |
| the five-tuple | `test_permitted_pll_freqs_138c_five_tuple`; derived from DS1239E Table 3-18 in `P1.T20` |
| #427 fixed + regression | `test_pll_fvco_issue427_regression`; root cause was the 25A ES entry solved with rPLL algebra (no MDIV, wrong VCO direction), split into `plla_freqs`/`solve_plla` (`P1.T21`) |
| swept set `E1` | `evidence/plla/runs.jsonl`, 27 `ok` rows; `p1-pll-e1-clocking_pll-0000` is `E1`, cells/attrs/conns 0, `c1`/`c2` ok; sweeps A-D cover `IDIV`, `FBDIV`, `MDIV`, `ODIV0`, `ODIV1`, the five `DYN_*` modes and all 12 sites |
| the primitive name | `D96`: the cell is `PLL`, not `PLLA` — the vendor refuses `PLLA` on this die (`RP0008`) |

Beyond the criterion, because no document publishes it: the charge pump was
**measured and fitted** (`KVCO=7`, `FLDCOUNT=(⌊Fpfd/30⌋+1)·16`,
`ICP = round(a[R]·Ndiv)·10`), 45/45 points reproduced.

**Named gaps.** `Fpfd` above 50 MHz is unmeasured (the vendor refuses
`FCLKIN` 650 MHz, `PA2078`). `A_ODIV1_SEL` (115) writes **only when `CLKOUT1`
is loaded** — `CLKOUT1_EN` alone is not enough, so an unloaded second output
silently carries no divider. A `PLL` output **cannot reach an HCLK lane** in
the model, and `PLL_B[*]` outputs reach **no fabric flop at all** (both
MEASURED in `P1.T40`) — the E2E therefore runs the PLL beside the clock tree,
not through it. `examples/gw5a/pll/GW5AST-138C.vh` lands at **100 MHz**
`CLKOUT0` (FVCO 800), not the roadmap's headline 200 MHz: 200 MHz is
reachable arithmetic on this part but was not measured, so it is not claimed
(`A9`).

### `S8` — HCLK / CLKDIV / CLKDIV2 on 138C: **REACHED**, one half structurally at `E0`

> "`HAS_5A_HCLK` is set …; the 6-block, two-half topology is implemented …;
> `_gw5a_hclk_locs` and `gw5_ihclk_wire_num` carry 138C entries so no
> `KeyError` path remains; nextpnr creates CLKDIV/CLKDIV2 bels and HCLK→FCLK
> pips; the swept set is **E1**-equivalent."

| clause | evidence |
|---|---|
| `HAS_5A_HCLK` | `P1.T09`; `chip_flags & 0x10000 != 0` |
| 6 blocks, two halves | measured, not ported: `(27,0) (27,181) (81,0) (81,181) (108,64) (108,117)`, **2 top / 4 bottom** — the blueprint's assumed 3/3 is **refuted** (`P1.T04`); 165 nodes and 906 fuse-bearing HCLK pips per block after `P1.T08b` (the shipped code produced **0**) |
| no `KeyError` | validation §2: `gw5_ihclk_wire_num('GW5AST-138C')` → 38, `_gw5a_hclk_locs['GW5AST-138C']` → 6 |
| nextpnr bels + pips | `P1.T10` (constids `HCLK40-43`/`HCLK50-53`, table-driven `postRoute` for N blocks), `P1.T11` places a CLKDIV **and** a CLKDIV2; `check_hclk_6block.py` is a gate step |
| swept set `E1` | `CLKDIV`: 10/10 `E1` rows over `DIV_MODE` 1…8 + baseline, 0/0/0, no unexplained bits |
| the row that closes the network | the E2E, `E1`, below |

**`CLKDIV2` closes at `E0`, and the reason is structural, not a shortfall**
(`D103`): CLKDIV2 writes **no fuse at all** — its signature is the *absent*
`HCLK_BUF_BO` select bit per lane plus the chained CLKDIV `DIV=2` bit — so
`gowin_unpack` cannot recover it and `E1` is unattainable by construction
(`EC9`). 7 rows, each pinned to a `(lane, RESETN)` point.

**Named gap.** Blocks **0 and 1** share one SPINE row, so the
block↔lane bijection was measured for blocks 2/3/4/5 only; the two remaining
blocks need a placement handle the oracle does not expose.

### `S9` — DHCE / DQCE / DCS: **NOT REACHED** (two of three halves closed)

> "DHCE is implemented for the GW5A family …; DQCE's 138C tile-type
> assumptions are re-derived …; **DQCE and DCS are each created for all four
> quadrants** with a 138C-traced port table … All three are **E1**-equivalent.
> *Measure:* **quadrant count == 4 for both DQCE and DCS**; evidence rows for
> the three."

| primitive | state | evidence |
|---|---|---|
| `DHCE` | **`E1`**, lanes 0-2 | greenfield for the whole GW5A family (`D97`: the primitive is `DHCE`, not `DHCEN`); 24 bels = 6 blocks × 4; site index **=** HCLK lane index; the gate is one bit, the output-enable of the lane entry mux; `evidence/dhcen/` |
| `DQCE` | **`E0`, closed** | `p1t29-dqce-e1d`, both quadrants, `EQUIV E0 ok`, 0/0/0, `c1`/`c2` ok, 0 unexplained bits, mask unchanged |
| `DCS` | **not closed** | output side fixed, input side a measured gap; no `runs.jsonl` |

The criterion cannot be met **as written**, and the reason is a measurement,
not a shortfall: the shipped 138C chipdb built **zero** DQCE and **zero** DCS
(`fse_create_clocks` hands this device to `fse_create_5a138_clocks`, which
returns before both builders), and when they were built it turned out the die
has **two** quadrants, not four — only 2 of its 6 clock-bridge cells carry a
spine multiplexer. `12 DQCE` (six at (54,93) gating `SPINE8..13`, six at
(54,88) gating `SPINE16..21`) and `4 DCS` (`P26*`→`SPINE14`, `P27*`→`SPINE15`,
`P36*`→`SPINE22`, `P37*`→`SPINE23`) are what exists, proven by capacity runs:
`n = 12` occupies exactly those twelve multiplexers and `n = 13` does not
place. "Quadrant count == 4" would have attached quadrant 3 to cell (54,89),
which has no spine mux in it. `A1` amends the measure.

**`DQCE` is `E1`-unattainable** for the same reason as `CLKDIV`: it has no CLS
address, its site is the router's choice, so neither flow exports a placement
constraint (`EC9`).

---

## 2. Named gaps carried out of this phase

Each is a measurement with a next step, not an unknown.

1. **DCS input side.** The `P{26,27,36,37}{A..D}` input multiplexers are fed
   only by the bridge cells' `PCLK*` / `*MDCLK*` / `*BDCLK*` wires, and
   **nothing in the 138C database drives any of them** (`PCLKB0` is a pip
   destination in 0 cells; its node is the two bridge cells and nothing else),
   while the vendor's own bitstream selects `P26A-D <- BLMDCLK1`. Closing it
   needs a campaign that measures where those wires come from — a device
   measurement, not a router rule. `evidence/dcs/openflow-gap-138c.md`.
2. **DCS `SELFORCE` / `CLKSEL`: UNVERIFIED.** No vendor bitstream in the
   campaign routes an external net into either bridge cell for them, so the
   model carries the pre-5A wire names only, enough that co-located DCS
   differ. A dynamically-driven `CLKSEL` on this die is not modelled.
3. **DHCE lane 3.** Its HCLK entry is the fabric wire `LSR2`, and
   `route_dhcen_net` refuses a partly-global net, so lanes 0-2 close `E1` and
   lane 3 does not. Its fuse is measured on the vendor side.
4. **No `PLL` → HCLK path**, and **`PLL_B[*]` outputs reach no fabric flop**
   (`P1.T40`). Both are database facts, measured while building the E2E.
5. **Four independent global clock nets trip `router1.cc:347`** — the E2E
   design is at the ceiling of what the router will take on this die.
6. **`ODIV1` needs a loaded output.** `A_ODIV1_SEL` is written only when
   `CLKOUT1` has a consumer; `CLKOUT1_EN` alone leaves the divider unset.
7. **HCLK blocks 0 and 1** have no measured block↔lane bijection (they share
   one SPINE row).

---

## 3. Deviations, as amendment lines for `spec.md`

`A1`-`A9` are owed to `spec.md` (and the two satellites named); they are the
orchestrator's to apply, exactly as `P0.T39`'s `A1`-`A16` were.

- **`A1`** — `S9`'s measure "**quadrant count == 4** for both DQCE and DCS" is
  **refuted by measurement**: the `GW5AST-138C` die has **two** clock
  quadrants (2 of 6 bridge cells carry a spine mux), 12 DQCE and 4 DCS.
  Restate as "every quadrant the die has, derived from the device tables, with
  the count itself recorded" — a hardcoded 4 would model a quadrant that does
  not exist.
- **`A2`** — `S9`'s "All three are **E1**-equivalent" is unreachable for
  `DQCE`: it has no CLS address, so no placement constraint exists for `E1` to
  assert (`EC9`), exactly as for `CLKDIV`. Restate as `E1` where a CLS address
  exists, `E0` + recorded reason otherwise.
- **`A3`** — `S9` is **not reached**: `DCS`'s open flow does not route (gap 1
  above). The DHCE and DQCE halves are reached.
- **`A4`** — `spec-harness.md` §6 / the Validation step-7 expectation that
  every slug's `runs.jsonl` holds **0** `aborted` rows conflicts with the
  campaign shape: a vendor-only measurement run (site tracing, the attrid map,
  a structural placement proof) has no open half and `aborted` is its correct,
  reason-carrying verdict. 77 such rows exist and `check_evidence.py` accepts
  them. Restate as "no `aborted` row without a reason in `notes`".
- **`A5`** — `evidence/_budget/clocking-checkpoint.md` is read by three
  Validation steps (`## Checkpoint 145` by 11, `## Family regression` by 6,
  the `NO-DATA` reference by 4) and by `P1.T38` (`## Landed`), but no task
  wrote any of them; they were written at the phase close. The blueprint
  should name the file's required sections where it names the checkpoint.
- **`A6`** — Validation step 1's invocation passes `--chipdb` and
  `--evidence`, which `check_criteria.py` has never had (evidence dir is
  positional; the tool never reads a chipdb). The chipdb-side assertions
  `V14` describes live in `tests/test_gw5ast138c_clocking.py`.
- **`A7`** — `V20`'s `git -C $FL check-ignore <path under $OTC>` cannot work:
  `$OTC` is a submodule and git refuses. The form is `git -C $OTC
  check-ignore -q evidence/…`.
- **`A8`** — Validation step 10 greps one glob for `WATCHDOG_ARMED` and
  `BATCH_COMPLETE`; they live in two files (`<batch>.watchdog.log` and
  `<batch>.log`). Counted per batch id across the pair.
- **`A9`** — the roadmap's Phase-1 headline says "a real, open-toolchain
  **200 MHz** clock". What is measured and shipped in
  `examples/gw5a/pll/GW5AST-138C.vh` is **100 MHz** `CLKOUT0` (FVCO 800 MHz,
  mid-band), vendor-verified on all 12 sites. Restate the headline as the
  measured operating point, or add a measured 200 MHz point in a later phase.

Also carried, already recorded in the blueprint's close section and repeated
here so `spec.md` gets them: `D96` (the cell is `PLL`, not `PLLA`) and `D97`
(`DHCE`, not `DHCEN`) rename the two headline primitives; the evidence slugs
`plla` and `dhcen` keep their names for path stability.

---

## 4. The gate

One full gate per phase, foreground, in each repo (`C12`). It was **red three
times** and each red was fixed forward, never worked around:

| red | cause | fix |
|---|---|---|
| apicula fast | `test_pll_attrids_138c_reconciled`: ids 124/131 were listed as nameless in `attrids-138c.tsv` after `P1.T42` named them | artefact refreshed (`in_both` 174→176, `fse_id_with_no_name` 18→16) and the test's "only new ids" assertion widened to the four measured names |
| apicula heavy | the two `test_gen` tests asserted a three-file generator output; `gen.run` has written `top-open.cst` since the CLKDIV row | tests updated to the four-file contract |
| apicula heavy | `test_clkdiv_routes_138c` aborted in nextpnr (`idstring_idx_to_str` assertion): the pinned `$DATASTORE/chipdb/p1t08d` `.bin` predates a constids change | `.bin` regenerated from this tree; it came out **byte-identical to the installed pair** (`0a413537…`), which is also a determinism proof |
| nextpnr | `APICULA_ROOT` pointed at a per-task worktree that no longer exists | repointed at the sibling checkout; the marker-label bug behind it (`repo` taken from the checkout directory, so worktree gates were filed as `integ-*`) fixed in all three `pre-push` hooks |
| open-toolchain | `evidence/dqce/summary.md` and `evidence/dcs/summary.md` lacked the required `## Sweep` heading | both written with the real axes |

Final, at the tips this phase closes on: apicula `3c22067`
`GATE full: ok, 2 checks` (349 passed / 5 skipped / 1 xfail fast in 24.3 s;
49 passed / 1 xfail heavy in 550.0 s; 629 s wall), nextpnr `7dd337bb`
`GATE full: ok` (5 checks — the two HCLK checks, arch-gen determinism and the
three DCS-spine checks — 46 s), open-toolchain `1ebd0f0`
`GATE full: ok, 3 checks` (78 tool tests,
`EVIDENCE ok: 159 rows, 34 pending, 0 blank, 0 missing artifacts`,
`CRITERIA ok: 14/14`, 12 s). `tools/gate_status.py` exits 0 with every
repo's newest marker `PASS`.

Two tooling defects were found by running the gate and fixed with guards:
`gate_status.py` judged **every** marker ever written, so one red run from an
earlier phase would keep the tool red forever (now: newest per repo, older
`SUPERSEDED`, a killed run `DEAD`), and the batch watchdog called four
completed batches dead because the completion marker lands after the pid does
(now: a ten-second exit grace that re-reads the log).

---

## 5. Reproduction

```sh
# preamble: spec.md §12, GOWINHOME = the Standard install, both DYLD_* set
export FL=/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84
export OTC=$FL/open-toolchain
export PIPE=/Users/alex/fine-line/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84
source /Users/alex/fine-line/vendor/venv/bin/activate

# the one full gate, per repo
cd $FL/apicula        && GATE_SCOPE=full make gate
cd $FL/nextpnr        && GATE_SCOPE=full make gate
cd $FL/open-toolchain && GATE_SCOPE=full make gate && python tools/gate_status.py

# the phase's structural criteria and its evidence
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence \
    --rows "PLL,HCLK block,CLKDIV,CLKDIV2,DHCE,DQCE,DCS"
python $OTC/tools/check_evidence.py $PIPE/spec-primitives.md $OTC/evidence \
    --slug plla --slug hclk --slug clkdiv --slug clkdiv2 --slug dhcen \
    --slug dqce --slug dcs

# the E2E, re-run from scratch (one vendor + one open build, ~4 min)
cd $FL/apicula && python -m fuzz.gw5ast138c.harness \
    --shape clocking_e2e --level E1 --batch-id p1-e2e-repro \
    --design-dir /Users/alex/fine-line-data/open-toolchain-gw5ast/batch/p1-e2e-repro

# the DQCE row, both quadrants
cd $FL/apicula && python -m fuzz.gw5ast138c.harness \
    --shape clocking_dqce --level E1 --batch-id p1-dqce-repro \
    --design-dir /Users/alex/fine-line-data/open-toolchain-gw5ast/batch/p1-dqce-repro
```

Installed pair used by every row in this phase: `nextpnr-himbaechel`
`cfc97099…`, `chipdb-GW5AST-138C.bin` `0a413537…`,
`apycula/GW5AST-138C.msgpack.xz` `8bb0932e…`.

---

# Second pass, 2026-09-07 (`P1.T38`)

The phase closes here. The first pass above landed the branches and ran the
gate; `P1.F1`-`P1.F4` then paid off the Phase-1 gestalt (`impl/gestalt-p1.md`)
and the `C15` gaps. This section says where the three exit criteria stand on
the pair the phase actually lands on, what is still open, and what it cost.

## 1. Exit criteria, second pass

### `S7` — the 138C PLL: **REACHED**

Unchanged from the first pass and strengthened by `P1.F3`. 12 bels; the
five-tuple `(800., 1000., 5.079, 1300., 650.)`; the charge pump measured and
fitted (45/45 points) and now **refusing** what it never measured
(`PllPumpUnmeasured`, `P1.F1`/gestalt `B5`); one PLL design at `EQUIV E1 ok`,
0/0/0, `c1`/`c2` ok; the `DYN_*` selects encoded from the cell. Both `P1.T40`
output gaps closed by `P1.F3`: `PLL_L[0].CLKOUT0` drives an HCLK lane
(`p1f3-a`) and a bottom-edge site clocks fabric (`p1f3-b`), each `EQUIV E1 ok`
with 0 unexplained bits.

### `S8` — HCLK / CLKDIV / CLKDIV2: **REACHED**

Six HCLK blocks, 2 top / 4 bottom, `gw5_ihclk_wire_num` 38, `HAS_5A_HCLK`
set, no `KeyError` path left. `CLKDIV` `E1` over nine `DIV_MODE` values.
`CLKDIV2` `E0+hw-pending` by construction (`EC9`, no fuse to recover), and the
recovery rule now compares the **lane** (`P1.F1`/gestalt `B3`), so a `CLKDIV`
left at its `DIV_MODE=2` default on another lane no longer recovers a
`CLKDIV2` for free. The `HCLK block` row is closed by the E2E rows, which now
live in `evidence/hclk/` where its Evidence cell points (`P1.F1`/gestalt
`B1a`). Four independent global clock nets route (`p1f3-c`).

### `S9` — DHCE / DQCE / DCS: **NOT REACHED** (two of three halves closed)

* **DHCE — closed.** All four lanes at `E1` (`p1f3-d`, 0/0/0, `c1`/`c2` ok).
  Lane 3's `LSR2` fabric entry is carried per block in the chipdb and
  `is_relaxed_sink` lifts the global filter for exactly those sinks. The gate
  fuse of a `DHCEN_USED` placeholder is now asserted in `c1`
  (`P1.F4`/gestalt `B4`).
* **DQCE — closed at `E0`.** Both quadrants, `p1t29-dqce-e1d`, `EQUIV E0 ok`,
  0/0/0, `c1`/`c2` ok. `E1` is structurally unattainable (`EC9`: a DQCE has no
  CLS address).
* **DCS — closes as `refused:<named error>`** (`A12`,
  `evidence/dcs/refusal-138c.md`), which is a terminal status DONE-STD admits
  but `S9` does not. `P1.F4`'s `reject_untraced_dcs_control` refuses every
  design that drives `CLKSEL`/`SELFORCE` — every design that uses a DCS for
  what a DCS is — and that is exactly the design `P1.F2` closed at `E0`.
  Re-run on the landing pair, all three sweep points: `p1t38c-dcs`,
  `refused=3`, packer's exact text in `notes`, vendor `.fs` beside each. The
  guard is right and stays: `E0`/`E1` mask routing (`D32`) and the
  `CLKSEL`/`SELFORCE` fuses are pip fuses, so the equivalence check could not
  see the unverified part.

`check_criteria.py --phase 1` is `CRITERIA ok: 9/9`, exit 0 — the DONE-STD
roll-up. `S9` is a stronger claim than DONE-STD and it is **not** met.

## 2. Gaps carried out of this phase

| gap | blocks `S9`? | why |
|---|---|---|
| `SELFORCE` / `CLKSEL[0..3]` **unverified** on the 138C | **yes** | No vendor bitstream in either campaign routes an external net into a bridge cell for them, so the model carries pre-5A wire names. `S9`'s words are "all three are `E1`-equivalent"; a row that closes `refused:<error>` is not equivalent to anything, so this gap is what keeps `S9` NOT REACHED. Closing it needs one campaign: a vendor design that drives `CLKSEL` dynamically, traced (`input-side-138c.md` §6). |
| `PCLK*` half of the DCS input multiplexer **driverless** | **no** | `get_clock_ins` builds the entries; `fse_create_5a138_clocks` never turns them into nodes. No bitstream in either campaign selects a `PCLK*` source, so nothing measured depends on it and no `S9` clause names it. A named, unexercised gap — it rides along with the `CLKSEL` campaign. |
| blocks 0/1 share one SPINE row | no | no block↔lane bijection measured for that pair; `S8` does not ask for one. |
| eleven of twelve PLL sites reach the plane through a logic-to-clock gate | no | measured and recorded (`hclk-entry-138c.md`); `S7` asks for a working PLL, which it has. |
| `Fpfd` above 50 MHz unmeasured | no | now a **named refusal** rather than a silent extrapolation (`B5`). |
| `C4` residues #3-#9 (hidden constants) | no | recorded follow-ups for the upstream PR, not phase criteria. |

## 3. Deviations, as amendment lines for `spec.md`

`A12` — the `DCS` row's terminal status is `refused:<error>`, not `E0`;
`P1.F2` and `P1.F4` were mutually inconsistent and the refusal wins.
`A13` — a named packer refusal was recorded as `aborted`, with the packer's
words discarded; `PackRefused` + `REFUSED:`/exit 3 + `openflow.named_refusal`
+ the harness verdict, 4 red-verified tests.
`A14` — the installed pair's three halves do not move together: `P1.F4`'s
chipdb keys moved the msgpack (`6e95b906…` → `315c02d8…`) while the `.bin`
came out byte-identical (`0206b922…`), because `gowin_arch_gen.py` does not
consume them. Provenance must record all three sha256s.
`A15` — `V7`'s "0 `aborted` rows" is settled by `A4`: 77 rows, 0 without a
reason, 76 vendor-only, 1 superseded by `P1.F3`. No defect.
`A16` — Validation step 8's script assumes every row carries `mask_sha256`;
only equivalence rows do (99 of 209). Measured over those: one distinct value,
equal to the file's own sha256.

All five are written into `spec.md` `## Amendments`.

## 4. The gate, second pass

Red twice — both because `P1.F3` landed after the first pass's gate — and
fixed forward, then green in one run:

| red | cause | fix |
|---|---|---|
| apicula heavy | `test_clkdiv_routes_138c`, nextpnr exit `-11`: the pinned `p1t08d` `.bin` predates this pair's constids | repinned to the pair's `.bin` (`0206b922…`) |
| open-toolchain fast | `test_dhcen_row.py` asserted 4 `clocking_dhce` rows and "lane 3 is `aborted`"; `P1.F3` closed lane 3 and added a second sweep | assertion scoped to the closing batch `p1f3-d`, lane 3 required `ok`/`E1`, the pre-fix rows kept |

Green: apicula `GATE full: ok, 2 checks` (372 passed / 6 skipped / 1 xfail
fast in 32.7 s; 53 passed / 1 xfail heavy in 414.2 s; 466 s wall), nextpnr
`GATE full: ok` (5 checks, 41 s), open-toolchain `GATE full: ok, 3 checks`
(84 tool tests; `EVIDENCE ok: 174 rows, 0 pending, 0 blank, 0 missing
artifacts`; `CRITERIA ok`; 9 s). `tools/gate_status.py` exits 0.

## 5. Reproduction, second pass

```sh
export FL=/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84
export OTC=$FL/open-toolchain
export PIPE=/Users/alex/fine-line/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84
export DATASTORE=/Users/alex/fine-line-data/open-toolchain-gw5ast
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib
export DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
source /Users/alex/fine-line/vendor/venv/bin/activate

# the pair, from the epic tips (apicula b31f05d, nextpnr 0882cd4c)
cd $FL/nextpnr && cmake --build build -j8
cd $FL/apicula && python -m apycula.chipdb_builder GW5AST-138C
PYTHONPATH=$FL/apicula python \
  $FL/nextpnr/himbaechel/uarch/gowin/gowin_arch_gen.py -d GW5AST-138C \
  -o $FL/nextpnr/build/bba-gw5ast138c/chipdb-GW5AST-138C.bba
$FL/nextpnr/build/bba/bbasm --le \
  $FL/nextpnr/build/bba-gw5ast138c/chipdb-GW5AST-138C.bba \
  $DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin
cp $FL/nextpnr/build/nextpnr-himbaechel $DATASTORE/toolchains/nextpnr/bin/
cp $FL/apicula/apycula/GW5AST-138C.msgpack.xz $DATASTORE/chipdb/std/
cp $DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin $DATASTORE/chipdb/p1t08d/

# the DCS refusal, all three sweep points (4 vendor runs incl. the pilot)
cd $FL/apicula && python -m fuzz.gw5ast138c.harness \
    --shape clocking_dcs --level E0 --batch-id p1t38c-dcs-repro \
    --design-dir $DATASTORE/batch/p1t38c-dcs-repro

# the one full gate per repo
cd $FL/apicula        && GATE_SCOPE=full make gate
cd $FL/nextpnr        && GATE_SCOPE=full make gate
cd $FL/open-toolchain && GATE_SCOPE=full make gate && python tools/gate_status.py

# the phase's criteria
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 1
```

Pair every row in this section was measured on: `nextpnr-himbaechel`
`f029437eb33f356176f6854e0da978a08bee80d211c097be1ff8947059fe587a`,
`chipdb-GW5AST-138C.bin`
`0206b922d5e08e025eb3ab7728bdfa135930d299faed9986a3f12c93d4d82819`,
`apycula/GW5AST-138C.msgpack.xz`
`315c02d8e260a80072afee536d31bb175d2a9fd91dd8dac25e3f80c9a8e1673e`.

## 6. Runs

**248** vendor-oracle runs cumulative against the `D62` box of 290 — 244 at the
first pass, 4 added here (`p1t38c-dcs-q1` 1, `p1t38c-dcs` 3), all `dcs`, all
`refused`. `evidence/_budget/clocking-runs.tsv`,
`evidence/_budget/clocking-checkpoint.md` `## Second pass`.
