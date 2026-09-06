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
