# Phase 1 (clocking) — Validation

`blueprints/P1-clocking.md` §Validation, run at the phase close on
`epic/gw5ast138c` (apicula `ab350d4`, nextpnr `7dd337bb`, open-toolchain `main`),
Standard 1.9.12.03, `installs_available: 1`. Every command below was run
verbatim except where an **Amended** note says otherwise and why; each
amendment is also an `A`-line in `phase-report.md`.

Preamble: `spec.md` §12 (`GOWINHOME` Standard, both `DYLD_*`, `$FL` the
worktree, `$OTC` the submodule, the `vendor/venv`). One deviation, standing
since Phase 0: the venv is `/Users/alex/fine-line/vendor/venv`, not
`$FL/vendor/venv`.

| step | criterion | exit | verdict |
|---|---|---|---|
| 1 | `V14` structural criteria (`S7`,`S8`,`S9`) | 1 | **FAIL** (6/7, `DCS` unmet — the real state) |
| 2 | the `KeyError` traps | 0 | PASS |
| 3 | `V16` named refusal | 0 | PASS |
| 4 | `V12a --classes pll` | 0 | PASS (recorded absence) |
| 5 | the phase's unit suite | 0 | PASS |
| 6 | `S3` family regression | 0 | PASS |
| 7 | evidence admissibility | 0 | PASS on the tool, **FAIL as written** on the `aborted` grep |
| 8 | mask integrity | 0 | PASS |
| 9 | `V20` storage hygiene | 0 | PASS (amended path form) |
| 10 | watchdog evidence | 0 | PASS (amended file split; 4 false deaths found and fixed) |
| 11 | budget box | 0 | PASS |
| E2E | one design, both flows, `E1` | 0 | PASS (`P1.T40`, cited not re-run) |

---

## 1. `V14` — the phase's structural criteria

**Amended.** The blueprint's invocation passes `--chipdb` and `--evidence`;
`check_criteria.py` as `P0.T31` delivered it takes the evidence directory
**positionally** and has no `--chipdb` flag at all (its docstring says so:
"There is no `--chipdb` flag: this tool never touches a chipdb"). The chipdb
assertions the step describes (PLL bel count 12, six HCLK blocks, DQCE/DCS
quadrant counts) live in the unit suite, step 5. Row ids also follow `D96`/`D97`:
`PLL`, not `PLLA`; `DHCE`, not `DHCEN`.

```sh
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence \
    --rows "PLL,HCLK block,CLKDIV,CLKDIV2,DHCE,DQCE,DCS"
```

```
clause-d: deferred to Phase 7 (D65)
CRITERIA ok: 6/7
CRITERIA FAIL: unmet rows: DCS
```

exit 1. **FAIL, and the failure is the truth**: `DCS` does not meet DONE-STD
because its open flow does not route (input side, named gap — see the phase
report). The other six rows are satisfied. Two of the six only became so
during this validation: `DQCE` had **no** `runs.jsonl` at all and `HCLK block`
had no row with a real decode check — see §Fixes below.

## 2. The `KeyError` traps, directly

```
ihclk 38
locs 6
```

exit 0. **PASS** — an integer > 0 and 6, where both lines raised `KeyError`
before this phase (`F23`).

## 3. `V16` — the `D39` state-(1) named refusal

`cd $FL/apicula && python -m pytest tests -k "unsupported_error" -q`

```
1 passed, 424 deselected in 0.19s
```

exit 0. **PASS** — the selected test is
`tests/test_gw5ast138c_clocking.py::test_iologic_before_hclk_unsupported_error_138c`,
which runs against the synthetic no-HCLK fixture, not the live chipdb.

## 4. `V12a --classes pll` — the PLL arc slice

**Satisfied by the recorded-absence branch the step itself defines**, not by
the `check_timing_l0.py` invocation: `parse_pll` recorded `NO-DATA:`.

```sh
grep -c '^NO-DATA:' $OTC/evidence/plla/timing-l0-pll.md   # -> 1
```

exit 0, and `$OTC/evidence/_budget/clocking-checkpoint.md` now names it in
both `## Checkpoint 145` and `## Timing`. **PASS.** The absence is measured:
the `.tm` publishes no PLL group for this die (chunks 0-2 carry a GW2A-18
rPLL block naming outputs the Arora-V PLL does not have) and the vendor SDF
emits every `CLKIN->CLKOUTn` IOPATH as `0.000`.

## 5. The phase's own unit suite

`cd $FL/apicula && python -m pytest tests/test_gw5ast138c_clocking.py -q`

```
25 passed, 2 xfailed in 52.13s
```

exit 0. **PASS** — `0 failed`. This is where the `V14` chipdb assertions
actually run: `test_plla_bel_count_138c_is_12`,
`test_gw5_add_hclk_bels_138c_block_and_wire_counts`,
`test_dqce_quadrant_count_138c_is_4`, `test_dcs_quadrant_count_138c_is_4`,
`test_permitted_pll_freqs_138c_five_tuple`, `test_pll_fvco_issue427_regression`.
The two `xfail`s are `P1.T08c`'s measured refutations, declared as expected
failures with their measurement in the reason string:
`test_clknames_138c_has_16_bdhclk` (this die has no sixteen-wire `BDHCLK`
band) and `test_hclk_to_clk_gates_fire_138c` (the HCLK-block → clock-mux hop
is fuseless here, so it is a node, not a gate pip).

## 6. `S3` family regression — three builds per available install

The Standard loop only; `GOWINHOME_STD` is the only install on this box
(`C9` removed Education), so `installs_available: 1` and the step asserts
`3 x 1` sha256s.

```
GW5AST-138C  8bb0932efc776ff2961d5f7a590774ec9f229a9670d82208bfec808da9e39886
GW5A-25A     5ad9184d5ae2ece33277d9003f3b94b215a616b93949ebb0d43139be10abe4d2
GW5AT-60B    615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8
```

exit 0, **no `FAIL` line**, three sha256s. **PASS.** `GW5AT-60B` is
unchanged from `P0.T40`. `GW5AST-138C` reproduces the msgpack the installed
`.bin` pair was built from, byte for byte. `GW5A-25A` **moved** from
`6311219d…` and the step requires that to be explained: the two chipdbs were
loaded and diffed field by field — the only difference is one **added** key,
`primitive: 'PLLA'`, in each of the six PLL `extra_func` entries (`D96`: the
cell type is data now, not a device gate). Recorded in
`clocking-checkpoint.md` `## Family regression`.

## 7. Evidence admissibility across the seven rows

```
RUNS: 6 files, 165 rows, 165 valid
EVIDENCE ok: 159 rows, 1 pending, 0 blank, 0 missing artifacts
0 admissibility findings
```

exit 0 — **PASS** on the contract line (the `1 pending` is the `dcs` slug,
which has no `runs.jsonl` because its row does not close).

**FAIL as written** on the second command: `grep -c '"verdict": "aborted"'`
returns 74 (`plla`), 2 (`hclk`), 1 (`dhcen`), not 0. Those rows are not
unfinished runs: they are **vendor-only measurement runs** (site tracing, the
attrid map, the `P1.T11` structural placement proofs) where the open half
could not run yet, and each carries its reason in `notes`. `check_evidence.py`
accepts them. The blueprint's "0 aborted" expectation predates the campaign
shape and is owed an amendment (`A4`). The `E0`-row half of the step holds:
every `E0` row has a non-empty `notes`, which is what `check_evidence.py`
itself asserts.

## 8. Mask integrity

```
59147bfc633e10c5c1f4875bef6cf0cf9b76f8d58868ffc084f8c252557a1ec0  fuzz/gw5ast138c/dontcare.mask
distinct mask_sha256: 1
```

exit 0. **PASS** — one distinct value across every `runs.jsonl` in the tree,
equal to the file's own sha256. The mask was not widened to make a diff
disappear.

## 9. `V20` — storage hygiene

**Amended**: `git -C $FL check-ignore <path under $OTC>` cannot work — `$OTC`
is a submodule and git refuses with `fatal: Pathspec … is in submodule`. The
scoped form is `git -C $OTC check-ignore -q evidence/_runs/x.fs` (`spec.md`
§12 says exactly this about submodule-scoped commands).

```
OK-evidence-gitignore
OK-manifests
OK-no-binaries
```

exit 0. **PASS.**

## 10. Watchdog evidence

**Amended**: `WATCHDOG_ARMED` is written to `<batch>.watchdog.log` and
`BATCH_COMPLETE` to `<batch>.log`, so the step's single glob cannot see both;
counted per batch id across the pair instead.

Every one of the 30 detached Phase-1 batches has exactly one `BATCH_COMPLETE`
and exactly one `WATCHDOG_ARMED`. Foreground steps (`p1t26-*` builds,
`p1-entry`, `p1t14-chipdb`) have neither by construction.

Four `WATCHDOG_STALL`/`WATCHDOG_DEAD` lines appear and the step requires each
to be paired with a completed re-run. They are better than that — they are
**false**, and the defect is now fixed:

| batch | line | truth |
|---|---|---|
| `p1-hclk-probe` | `WATCHDOG_DEAD` 20:22:58 | its own `BATCH_COMPLETE` is at 20:22:55 |
| `p1t29-dce` | `WATCHDOG_DEAD` 21:08:33 | `BATCH_COMPLETE` at 21:08:32 |
| `p1t31-dcs` | `WATCHDOG_DEAD` 21:10:05 | `BATCH_COMPLETE` at 21:10:03 |
| `p1t14-trial3` | `WATCHDOG_STALL` 11:39:19 | genuine stall, followed by `WATCHDOG_COMPLETE` 11:47:06 — the pairing the step asks for |

Root cause: the completion marker is a batch's **last** write and can land
after its pid is gone; the watchdog's one-second courtesy sleep was too
short. Fixed with a ten-second exit grace that re-reads the log each second
(`watchdog.sh`, apicula `ab350d4`), with
`test_batch_watchdog_waits_for_a_late_completion_marker` as the guard.
`p1t29-nextpnr-build` is not a batch (its marker is `NEXTPNR_BUILD_COMPLETE`);
its two `DEAD` lines are the same race on a marker the watchdog does not know.

**PASS**, amended.

## 11. Budget box

```
p1t29-dqce-e1d	dqce	2	221	…
grep -c '^## Checkpoint 145' -> 1
```

exit 0. **PASS** — final `cumulative` **221** ≤ 290, and the checkpoint
section exists (it did not before this validation; written now with the
per-slug split, `A5`).

## E2E — cited, not re-run

`P1.T40`'s batch is the phase's E2E and it is not re-run here (`C14`: the
orchestrator does not repeat a landed measurement).

```
BATCH_COMPLETE p1t40-e2e runs=1 ok=1 diff=0 aborted=0
EQUIV E1 ok
```

Row `p1t40-e2e-clocking_e2e-0000`, promoted into `$OTC/evidence/hclk/runs.jsonl`
during this validation: `level: "E1"`, `verdict: "ok"`,
`diff_count {cells: 0, attrs: 0, conns: 0}`, `decode_check {c1: ok, c2: ok}`,
`unexplained_bits []`, chipdb `0a413537…` — the installed pair. The design is
clk → DHCE → HCLK block 5 lane 0 → CLKDIV `DIV=4` → DQCE spine → fabric, with
`PLL_L[0]` at the `P1.T39` operating point. 18/18 cells.

---

## Fixes made during this validation

The standing order applies at the phase close as much as inside a task; five
things were red and were fixed forward rather than reported around.

1. **`DQCE` had no evidence row.** `evidence/dqce/summary.md` quoted an
   `EQUIV E0 ok … c1=ok c2=ok` block that **no committed row backed**: the
   only recorded run, `p1t29-dqce-e1c`, is `verdict=diff, c1=mismatch`, taken
   before the two `equiv.py` decode fixes the summary itself describes landed.
   Re-run at the phase close on the current pair as `p1t29-dqce-e1d`: 2 runs
   (quadrants `q1` and `q2`), `BATCH_COMPLETE p1t29-dqce-e1d runs=2 ok=2
   diff=0 aborted=0`, both promoted into `evidence/dqce/runs.jsonl`. The claim
   and the evidence now agree.
2. **`HCLK block` had no row with a decode check.** The `P1.T40` E2E row was
   sitting in `_runs/p1t40-e2e.rows.jsonl` and had never been promoted into
   the slug (the Phase-0 known defect: promotion is a manual step). Promoted.
3. **The checkpoint file was three sections short.** `## Checkpoint 145`
   (`V11`), `## Family regression` (`V6`) and the `NO-DATA` reference (`V4`)
   did not exist; `## Landed` (`P1.T38`) did not either. All four written.
4. **Four false watchdog deaths** — see step 10.
5. **The gate was red three times** before it was green; each fix is its own
   commit. See `phase-report.md` `## The gate`.

---

# Second pass, 2026-09-07 (`P1.T38`)

Re-run in full on the pair the phase lands on — apicula `b31f05d`
(`epic/gw5ast138c`, `P1.F1`-`P1.F4` merged), nextpnr `0882cd4c`,
open-toolchain `main` — after the `C15` fixes. Nothing above is rewritten;
this section records what the same eleven steps say now.

**The pair.** Rebuilt from those tips because `P1.F4` changed chipdb keys:

| half | sha256 | moved? |
|---|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `315c02d8…` | yes, from `6e95b906…` |
| `chipdb-GW5AST-138C.bin` | `0206b922…` | **no** — byte-identical |
| `nextpnr-himbaechel` | `f029437e…` | yes (rebuilt from `0882cd4c`) |

The `.bin` not moving while the msgpack did is itself the measurement:
`gowin_arch_gen.py` does not consume `control_wires_traced` or the
clock-plane halves table, so the two halves of the "pair" do not move
together and provenance must record all three sha256s (`A14`).

## The DCS confirmation run — F4 **did** disturb it

The step this pass was asked to run first was "the existing DCS design through
the new pair, to confirm `P1.F4`'s `control_wires_traced` key and refusal did
not disturb it". **It disturbed it, and the disturbance is correct.**

```
BATCH_COMPLETE p1t38c-dcs-q1 runs=1 ok=0 diff=0 aborted=1
Exception: DCS CLKSEL0, CLKSEL1, CLKSEL2, CLKSEL3, SELFORCE is driven on a
device whose DCS control wires have never been traced …
```

`P1.F4`'s `reject_untraced_dcs_control` refuses every design that drives
`CLKSEL`/`SELFORCE` — which is every design the `clocking_dcs` shape builds,
and therefore exactly the three sweep points `P1.F2` closed at `E0`. The full
re-run confirms it on all three:

```
BATCH_COMPLETE p1t38c-dcs runs=3 ok=0 diff=0 aborted=3
BATCH_SKIPPED  batch=p1t38c-dcs n=0 refused=3
```

The refusal is kept, not weakened, and the row's status becomes
`refused:<named error>` (`A12`, `evidence/dcs/refusal-138c.md`): `E0`/`E1`
compare cells, attributes and connectivity after the don't-care mask and the
`CLKSEL`/`SELFORCE` routing is pip fuses, never a verdict term (`D32`) — so
the equivalence check was structurally unable to see the unverified part. The
vendor half of each run completed and left its `.fs`, which is the oracle
artefact `D30` requires beside a refusal.

Two defects were found and fixed while doing it (`A13`): `gowin_pack` raised a
bare `Exception` for a refusal, and the harness recorded any non-zero open
flow as `aborted` with only a returncode map — so a deliverable was thrown
away and a refusal was indistinguishable from a crash. Now
`gowin_pack.PackRefused` → `REFUSED: <text>` on stderr → exit `3`,
`openflow.named_refusal` reads it back, and the row carries
`verdict: "refused"` with the exact words. Four red-verified tests in
`tests/test_pack_refusal_is_a_verdict.py`.

## The one full gate per repo

Foreground, once, then once more after fixing forward. **Red twice**, both
caused by `P1.F3` landing after the first pass's gate:

| red | cause | fix |
|---|---|---|
| apicula heavy | `test_clkdiv_routes_138c`: nextpnr exit `-11` (SIGSEGV) — the pinned `$DATASTORE/chipdb/p1t08d/.bin` predates this pair's constids | repinned to the pair's own `.bin` (`0206b922…`); passes in 18 s |
| open-toolchain fast | `test_dhcen_row.py::test_dhcen_row_closes` asserted 4 `clocking_dhce` rows and "lane 3 is `aborted`" — `P1.F3` closed lane 3 at `E1` and added a second four-lane sweep, so the slug holds 8 | assertion scoped to the closing batch (`p1f3-d`), lane 3 required `ok`/`E1`; `p1t27-dhce-e1b` kept as the pre-fix record |

Green, second run:

```
apicula          GATE full: ok, 2 checks   372 passed / 6 skipped / 1 xfail fast (32.7 s)
                                           53 passed / 1 xfail heavy (414.2 s)   wall 466 s
nextpnr          GATE full: ok             5 checks (hclk-6block 2/2, arch-gen determinism,
                                           the DCS-spine checks)                 wall  41 s
open-toolchain   GATE full: ok, 3 checks   84 tool tests; EVIDENCE ok: 174 rows, 0 pending,
                                           0 blank, 0 missing artifacts; CRITERIA ok       wall   9 s
tools/gate_status.py                       exit 0, every repo's newest marker PASS
```

## The eleven steps

| step | criterion | exit | first pass | second pass |
|---|---|---|---|---|
| 1 | `V14` structural criteria | 0 | FAIL (6/7) | **PASS — `CRITERIA ok: 7/7`**, and `--phase 1` is **9/9** |
| 2 | the `KeyError` traps | 0 | PASS | PASS (`ihclk 38`, `locs 6`) |
| 3 | `V16` named refusal | 0 | PASS | PASS (1 passed, 453 deselected) |
| 4 | `V12a --classes pll` | 0 | PASS | PASS (recorded absence, `NO-DATA` = 1, checkpoint names it) |
| 5 | the phase's unit suite | 0 | PASS | PASS (25 passed, 2 xfailed, 42.3 s) |
| 6 | `S3` family regression | 0 | PASS | PASS, one sha256 moved and is explained below |
| 7 | evidence admissibility | 0 | PASS on the tool, FAIL as written | **PASS on both halves** under `A4`'s wording — see below |
| 8 | mask integrity | 0 | PASS | PASS (`distinct mask_sha256: 1`, equal to the file) |
| 9 | `V20` storage hygiene | 0 | PASS | PASS (three `OK-` lines) |
| 10 | watchdog evidence | 0 | PASS, amended | PASS, amended — every exception enumerated below |
| 11 | budget box | 0 | PASS | PASS (`cumulative 244` ≤ 290; checkpoint present) |
| E2E | one design, both flows, `E1` | 0 | PASS (cited) | PASS (`p1f3-e2e`, 18/18, `EQUIV E1 ok`; cited, not re-run) |

### Step 1, in full

```
$ python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence \
      --rows "PLL,HCLK block,CLKDIV,CLKDIV2,DHCE,DQCE,DCS"
clause-d: deferred to Phase 7 (D65)
CRITERIA ok: 7/7                                                    # exit 0

$ python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 1
PHASE-REPORT phase1/phase-report.md: 2 REACHED, 2 backed, 0 unlinked, 0 unbacked
clause-d: deferred to Phase 7 (D65)
CRITERIA ok: 9/9                                                    # exit 0
```

`DCS` is the row that moved, and it moved to `refused:<named error>` — a
terminal status DONE-STD admits with clauses (b) and (d) waived, backed by
three `refused` evidence rows carrying the packer's words, nine unit tests
(`test_gw5ast138c_dcs_control_wires.py` ×5,
`test_pack_refusal_is_a_verdict.py` ×4) and the vendor `.fs` of each run. It
did **not** move by being made to pass: `S9` still says all three of DHCE,
DQCE and DCS are equivalence-closed, and `S9` is **NOT REACHED**.

### Step 6, and the 25A sha256 that moved

```
GW5AST-138C  315c02d8e260a80072afee536d31bb175d2a9fd91dd8dac25e3f80c9a8e1673e
GW5A-25A     60f1ba427f964feab3048f5dca82dc075acf9374a456476919202626d1335564
GW5AT-60B    615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8
```

No `FAIL` line; three sha256s (`installs_available: 1`). `GW5AST-138C`
reproduces the msgpack the installed `.bin` pair was built from, byte for
byte. `GW5AT-60B` is unchanged from `P0.T40` and the first pass. `GW5A-25A`
moved from `5ad9184d…` and the step requires that to be explained — the two
chipdbs were loaded and diffed field by field. **One field differs,
`extra_func`, and every difference is an *added* key; no key is removed and no
value changes:**

* `extra_func[*]['pll']['primitive']` on all six PLL entries (`D96`: the cell
  type is data now, not a device gate) — already explained at the first pass;
* `extra_func[*]['dcs'][*]['control_wires_traced'] = True` on all four 25A DCS
  (`P1.F4`, `C4#2`). `True` is the right value for the 25A: its DCS control
  wires *are* hand-traced (`gw5_dcs_inputs`), which is why the 138C refusal
  does not touch it.

### Step 7, and the `aborted` grep — resolved honestly

```
python $OTC/tools/check_evidence.py … --slug plla … --slug dcs
RUNS: 7 files, 180 rows, 180 valid
EVIDENCE ok: 174 rows, 0 pending, 0 blank, 0 missing artifacts       # exit 0
```

The blueprint's second command expects `grep -c '"verdict": "aborted"'` to
return `0` per file. It returns 74 (`plla`), 2 (`hclk`), 1 (`dhcen`) = **77**.
The first pass called this "FAIL as written" and owed an amendment; that
amendment is `A4`, and the question this pass was asked is which of the two
readings is true. Measured, over every row in the tree:

* **0** `aborted` rows have an empty `notes`. All 77 carry a reason.
* **76** are vendor-only campaign rows: `P1.T19` site tracing (12), the
  `P1.T22` attrid/attrval map (12), the `P1.T23`/`P1.T41` PLL sweeps whose
  open half had no PLL model yet (48), the `P1.T11` structural placement
  proofs (2), and two more of the same shape. Each states the vendor result it
  carries; the open half could not run, which is the measurement, not a
  failure of it.
* **1** is a real open-flow failure: `p1t27-dhce-e1b-clocking_dhce-0003`,
  DHCE lane 3, `nextpnr` exit 125. It was **closed** by `P1.F3` —
  `p1f3-d-clocking_dhce-0003` is `E1`, `ok` — and is kept as the pre-fix
  record. A superseded record, not an open defect.

**Verdict: exempt, not a defect**, on `spec.md` `A4`'s wording ("no `aborted`
row **without a reason in `notes`**"), which supersedes the blueprint's
literal "0". Recorded as `A15`. `V7` **PASSES**.

The step's own script has a separate defect worth its amendment: it indexes
`row['mask_sha256']` unconditionally, and only rows produced by an
equivalence comparison carry that field (99 of 209 do; the other 110 are
chipdb builds, PLL traces, calibration and timing rows). Counted over the rows
that have it: **`distinct mask_sha256: 1`**, equal to the file's own sha256 —
step 8 passes and the mask was not widened (`A16`).

### Step 10, every exception enumerated

39 detached batches have a watchdog log. Exceptions, each explained:

| batch | shape of the exception | truth |
|---|---|---|
| `p1t29-nextpnr-build`, `t33-calibration`, `t33-recovery`, `t34-calib` | no `BATCH_COMPLETE` | not batches — their markers are `NEXTPNR_BUILD_COMPLETE` and the Phase-0 calibration equivalents |
| `p1-dhcen-trace-1` | no `BATCH_COMPLETE` for its own id | the trace campaign writes one marker for the whole set: `BATCH_COMPLETE p1-dhcen-trace runs=9 ok=8 diff=0 aborted=1` |
| `p1t15-clkdiv2-e1`, `t34-calib` | `WATCHDOG_ARMED` more than once | resumed batches — the watchdog is armed once per launch, which is the contract |
| `p1-hclk-probe`, `p1t29-dce`, `p1t31-dcs` | `WATCHDOG_DEAD` | the three **false** deaths the first pass diagnosed and fixed with the ten-second exit grace; each has its own `BATCH_COMPLETE` seconds earlier |
| `p1t14-trial3` | `WATCHDOG_STALL` | genuine, and paired with `WATCHDOG_COMPLETE` — the pairing the step asks for |
| `p1f2-dcs-e0b` | `WATCHDOG_STALL` | genuine (the `sel4` run took 6 min against a 5 min stall threshold) and paired: `WATCHDOG_COMPLETE … saw BATCH_COMPLETE (clean exit)` two seconds later |

No unexplained stall line. **PASS**, amended as at the first pass (`A8`).

## Amendments this pass owes `spec.md`

`A12` (the `DCS` row closes `refused:<error>`), `A13` (a named refusal is a
verdict, not an abort), `A14` (the pair's three halves do not move together),
`A15` (`V7` is settled by `A4`; no defect), `A16` (step 8's script assumes
every row carries `mask_sha256`). All five are written into `spec.md`
`## Amendments`.
