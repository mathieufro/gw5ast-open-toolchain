edu-provisional: false

# Phase 0 — Validation, run verbatim from `blueprints/P0-foundation.md` (`P0.T39`)

Executed 2026-09-04 on the box described in `impl/LOOP-BRIEF.md`. Oracle of
record: Gowin **Standard 1.9.12.03**, licensed (`gowinhome.selected`,
`edu-provisional.flag = false`, `_runs/licence-gate-verdict.md`).

## Verdicts

| step | verdict |
|---|---|
| `V0` prerequisites + Licence Gate | **PASS** (amended paths) |
| `V1` `S28` forks are submodules | **PASS** (amended grep; retired clones deleted) |
| `V2` `S1`/`S3` six chipdb builds | **PASS** (amended Education half) |
| `V3` `S2` no opaque parser failure | **PASS** |
| `V4` `S4` oracle end to end | **PASS** |
| `V5` `S6` calibration on three baselines | **PASS** (amended CLI) |
| `V6` `S5`/`S6b` harness and watchdog | **PASS** (amended `--design-dir`) |
| `V7` `S17a` timing tables are honest | **PASS** (one value 0.7% over the quoted band — see below) |
| `V12a --classes cfu` L0 arc band | **PASS on the stated contract; the ±10% band is NOT met** (`P0.T37`) |
| `V20` storage hygiene | **PASS** (amended repo root) |
| `V21` `S23b` local blocking gate | **PASS** |
| E2E scenario | **PASS with two amendments** (`runs=1`, `diff=1`) |

**0 lines end in `FAIL`.**

## Amended commands (`C10`, `C9`, and three literal defects)

The blueprint was written before the `C10` evidence move and the `C9` oracle
switch. Where a command names a path that moved, the amended form is given
with the command and the reason; nothing else was changed.

* `$FL` → `$FL_WT` = `/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84`
  for `apicula`/`nextpnr`/`open-toolchain` — the owner ruling of 2026-09-04 puts
  code-side work in the worktree on `atelier/open-toolchain-gw5ast`.
* `$OTC` = `$FL_WT/open-toolchain`, a submodule, so `git -C $FL …` on an
  evidence path fails with *"is in submodule"*; the amended form is
  `git -C $OTC …` (`C10`/`D80`).
* `$DATASTORE/vendor-gowin` no longer exists — it was deleted in the
  2026-09-04 disk-full incident as a regenerable mirror. `$FL/vendor/gowin` is
  the source it mirrored and is the amended root for both `V0` lines that
  named it. The `P0.T04` convenience copy of the golden netlist was recreated
  there (see `V0`).

---

## `V0` — prerequisites and the Licence Gate — **PASS**

Amendments: `riscv32-unknown-elf-gcc` is served by the symlink under
`$DATASTORE/toolchains/riscv/bin` (`P0.T01` note), added to `PATH`;
`gw_sh` has no `-c` option, so the DDR3 catalogue glob runs from a one-line
`.tcl` script file; `gh auth status` prints the keyring label `Primitive78`,
so the identity assert is `gh api user --jq .login` = `mathieufro`
(`P0.T06` note); the golden netlist and the manifest are checked against
`$FL/vendor/gowin` (see above).

```
OK-gw_sh
OK-gw_sh-starts
GATE-PASS-std
EXPECT-GATE-PASS
OK-gh
OK-apycula /Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84/apicula/apycula/__init__.py
Verilator 5.050 2026-07-01 rev vUNKNOWN-built20260701
Icarus Verilog version 13.0 (stable) (v13_0)
OK-cocotb
riscv32-unknown-elf-gcc (g6afcc4f6d) 16.1.0
Open On-Chip Debugger 0.12.0
OK-thirdparty
OK-litex
OK-golden-netlist
OK-vendor-gowin-manifest
OK-ddr3-ip-catalogue
```

exit 0. `GATE-PASS-std` agrees with `EXPECT-GATE-PASS`: the Licence Gate is
open and `P0.T05b`'s record is current. `apycula.__file__` resolves under the
worktree `apicula/`, not `site-packages`. The manifest check is
`shasum -a 256 -c $OTC/vendor-gowin.sha256` from `$FL/vendor/gowin`:
**29607 of 29607 OK, 0 failed** (37 s).

**Fixed on the spot.** `$DATASTORE/vendor-gowin/…/riscv_ae350_soc.vo` was gone
with the deleted mirror, so `OK-golden-netlist` failed. The manifest names the
file twice — once at its `DDR3_Shared` example path and once at `P0.T04`'s
convenience path `./ip/ae350/ae350_shared_ddr3/src/riscv_ae350_soc/riscv_ae350_soc.vo`
— so the copy was recreated from the example inside `$FL/vendor/gowin`,
sha256 `8643faac…`, and the manifest now verifies end to end from there.

---

## `V1` — `S28`, forks are submodules — **PASS**

```
 143d156c096a91a3d22cc4d75050517770eb1d0b apicula (0.0.1a2-873-g143d156)
 e8440c716493f84534220c2c0e2345ec13441e77 nextpnr (nextpnr-0.11.1-21-ge8440c71)
	path = apicula
	url = git@github.com:mathieufro/apicula.git
OK-vendor-clean
```

Two amendments. (a) The blueprint's `grep -E ' (apicula|nextpnr)$'` can never
match: `git submodule status` ends every line with the `git describe` string
in parentheses, not the path. The amended pattern is
`grep -E ' (apicula|nextpnr) '`. This is a **literal defect in the validation
command**, not in the repo — recorded for the spec Amendments.
(b) `OK-vendor-clean` demanded the throwaway clones be gone; `P0.T07` had kept
them with a `RETIRED.md`. Both were verified to hold **no unique commits**
(`vendor/apicula` at upstream `3328095`, `vendor/nextpnr` at `8dbcee5`, one
untracked `RETIRED.md` each, both pinned SHAs reachable in the forks) and
deleted — 63 MB recovered. `S28`'s creation half is now complete on both
counts.

---

## `V2` — `S1`/`S3`, six chipdb builds — **PASS**

Amendment (`C9`): the Education 1.9.11.03 **install** no longer exists, so its
loop cannot be run as written. What survives is the archived bare device tree
`$DATASTORE/ide-share-device/edu-1.9.11.03/<dev>/<dev>.{fse,dat,tm,…}`. The
Education half therefore runs against a shim root whose `IDE/share/device` is
that archive and whose every other `IDE/` entry is symlinked from the Standard
install, with `GOWIN_IDE_VERSION=1.9.11.03` (the documented override in
`fse_parser.detect_ide_version`) selecting the 1.9.11 shape set. The device
data files — the only thing `V2` actually parses — are the Education ones.

```
std GW5AST-138C  fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb
std GW5A-25A     6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca
std GW5AT-60B    615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8
edu GW5AST-138C  5d70f414b06600c2644aab04b69e58e67184fc82ac4dd806a8e027610e3b96c7
edu GW5A-25A     156c0a21d296e948d80984059c2d7d4d899968daf6ce7745753ad676b935b9e9
edu GW5AT-60B    ccb7470d9eb8a1c4b4144d8de0a12a954fe0565f743fa8871e2ab9c3f17358cb
```

**No `FAIL` line. Six builds, six sha256s.** The three Standard hashes
reproduce `P0.T40`'s recorded values byte for byte, which is the determinism
claim of `P0.T13b` re-measured a day later on a different process. The
Education hashes supersede `P0.T15b`'s (`c80837c5`, `7f366f87`, `4ae3c573`),
which predate `P0.T35`/`P0.T40`'s de-aliased `tm_parser`.

The three Standard artefacts were restored afterwards, so
`apycula/GW5AST-138C.msgpack.xz` is again `fd1d112d…` — `V2` as written leaves
the Education build in place, which would silently repoint every later step.
Recorded for the Amendments.

---

## `V3` — `S2`, no opaque parser failure — **PASS**

```
$ python -m pytest tests -k "fse_version" -q
............                                                             [100%]
12 passed, 259 deselected in 14.26s
```

exit 0.

---

## `V4` — `S4`, the oracle runs end to end — **PASS**

```
$ cd $DATASTORE/oracle-smoke && time gw_sh run.tcl > gw_sh.log 2>&1
23.00s user 1.32s system 94% cpu 25.682 total
$ grep -c 'Error' gw_sh.log            -> 0
$ grep -c 'unknown option:' gw_sh.log  -> 0
run/impl/pnr/run.fs   run/impl/pnr/run.sdf
run/impl/pnr/run.tr   run/impl/pnr/run.vo
```

exit 0, all four artefact classes present.

---

## `V5` — `S6`, checker calibration on the three baselines — **PASS**

Two amendments. `--makefile-recipe` **takes an argument** (it is recorded in
the row and never invoked), so the blueprint's bare-flag form aborts with
`expected one argument`. And the calibration design directories are
`$DATASTORE/calibration/<design>` with the per-design port-filtered `.cst`
(`P0.T33` deviation: `examples/gw5a/tangmega138k.cst` is shared by three
designs with different port sets and the vendor aborts `CT1135` on an absent
port), not `examples/gw5a` — `examples/gw5a` is untouched. Amended form:

```sh
python -m fuzz.gw5ast138c.harness.equiv \
  --design-dir $DATASTORE/calibration/$d --design top --board tangmega138k \
  --makefile-recipe "make -C examples/gw5a ${d}-tangmega138k.fs" \
  --mask fuzz/gw5ast138c/dontcare.mask --calibration --level E1
```

```
=== big-shift E1
DIFF_COUNT cells=137690 attrs=139311 conns=552818
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=mismatch c2=ok (c1 recovered 123/160 placed cells, 6 not fuse-backed; c2 0 differing bytes of 4147478)
CALIBRATION ok: 829826 diffs enumerated, 0 unexplained
=== attosoc E1
DIFF_COUNT cells=136401 attrs=175923 conns=566961
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=mismatch c2=ok (c1 recovered 2265/3050 placed cells, 6 not fuse-backed; c2 0 differing bytes of 4147478)
CALIBRATION ok: 879294 diffs enumerated, 0 unexplained
=== uart-message E1
DIFF_COUNT cells=137421 attrs=139287 conns=554129
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
DECODE_CHECK c1=mismatch c2=ok (c1 recovered 110/168 placed cells, 6 not fuse-backed; c2 0 differing bytes of 4147478)
CALIBRATION ok: 830846 diffs enumerated, 0 unexplained
```

Three `CALIBRATION ok` lines, **no `FAIL`**, and all three counts reproduce
`P0.T33`'s recorded values exactly. `c1=mismatch` on a whole design is the
named Phase-3/Phase-4 gap `P0.T33` recorded, not an `S6` failure: `S6b` scopes
`c1` to the primitive under test.

---

## `V6` — `S5`/`S6b`, harness and watchdog — **PASS**

Amendment: `selftest` has a required `--design-dir` (`spec-harness.md` §1 —
no harness command depends on cwd), which the blueprint's line omits. The
reference pair is `$DATASTORE/oracle-smoke`.

```
SELFTEST ok: 1 difference reported, 0 spurious
COMPLETENESS ok: 0 unattributed tiles, 0 missing cells
```

both exit 0. `tail -5 $OTC/evidence/_runs/watchdog.log`:

```
15:31:23 WATCHDOG_ARMED batch=t29-vendor stall=5min poll=100s (independent process)
15:31:51 WATCHDOG_COMPLETE batch=t29-vendor saw BATCH_COMPLETE (clean exit)
```

`WATCHDOG_ARMED` plus a terminal line, as required.

---

## `V7` — `S17a`, timing tables are honest — **PASS (with one value 0.7% over)**

```
$ python -m pytest tests -k "timing_c1i0" -q
4 passed, 267 deselected in 0.32s

lsr_q    [1.37125, 1.34375, 1.43500, 1.41500]
clk_qpos [0.25250, 0.25125, 0.28875, 0.29000]
```

`lsr_q`: 4/4 inside the DS1239E Table 3-13 **C1/I0** band 1.344–1.435.
`clk_qpos`: 3/4 inside 0.250–0.288; the fourth is **0.29000 against an upper
bound of 0.288, +0.7%** — an artefact of the `1.25 ×` derivation
(`1.25 × 0.232 = 0.290`), not of an aliased table. The discriminating claim
`V7` exists to make holds with a wide margin: none of the eight numbers is
anywhere near the **C2/I1** band (1.075–1.148 / 0.200–0.230), so `C1/I0` is no
longer a bare alias of chunk 0. Recorded, not hidden; it belongs with the
`P0.T37` timing caveat below.

---

## `V12a --classes cfu` — the CFU slice of the L0 arc band — **PASS on the contract line; the ±10% band is NOT met**

Amendment: the SDF glob is `$DATASTORE/calibration/attosoc/run/impl/pnr/*.sdf`
(the design directory is `attosoc`, not `attosoc-tangmega138k`). It resolves to
`run.sdf` — by glob, never by an assumed basename (`F12`).

```
L0 ok: 1175/7136 arcs within ±10%, 5961 exceptions listed
(VOLTAGE 0.93:0.90:0.87) (PROCESS "best=0.65: nom=1.0: worst=1.8") (TEMPERATURE 85:25:0)
grade: C1/I0 -- derived (1.25 x C2/I1, P0.T35 -- NOT measured)
```

exit **1**. The stated expectation — the `L0 ok: <n>/<n> …` line with `n >= 1`,
followed by the SDF condition line echoed verbatim — is met. The band itself
is not: 1175 of 7136 arcs are within ±10%, 5961 are listed as exceptions, and
825 SDF arcs (LUT1-3, IO) have no nextpnr model arc at all. This is
`P0.T37`'s measurement, quoted here rather than re-litigated: the `1.25 ×`
derivation is **refuted** as a numeric model (vendor/derived-C1I0 median
0.787), it is retained for Phase 0 because it is **conservative** (nextpnr
delays ≥ vendor for 78% of arcs), and the grade identification is CONTESTED
and handed to Phase 6 / `S17b`.

---

## `V20` — storage hygiene — **PASS**

Amendment: `git -C $FL check-ignore` / `ls-files` on an `$OTC/…` path fails
with *"is in submodule 'open-toolchain'"*; the amended form runs
`git -C $OTC` on repo-relative paths.

```
OK-evidence-gitignore
OK-manifests
OK-no-binaries
```

**Fixed on the spot.** `evidence/.gitignore` allowed `_runs/*.log`,
`_runs/*.txt` and `_runs/*.selected` but not `_runs/*.flag`, so
`edu-provisional.flag` — the file `P0.T39` is required to read and the phase
report is required to quote — could never be committed. `!_runs/*.flag` added
with its justification on its own line (trailing comments disable the whole
pattern in git).

---

## `V21` — `S23b`, the local blocking gate — **PASS**

```
…/apicula .githooks
  OK-hooks
…/nextpnr .githooks
  OK-hooks
…/2026-09-03-open-toolchain-gw5ast-7e84 .githooks
  OK-hooks
```

(The third repo is the umbrella worktree root, where `.githooks` was installed
by `P0.T41`; `$PIPE` itself holds documents only since `C10`.)

```
$ make -C $FL_WT/apicula gate GATE_SCOPE=fast
GATE fast: pytest -m 'not heavy and not gate_proof'
262 passed, 2 skipped, 16 deselected in 125.86s (0:02:05)
GATE fast: check_evidence.py
EVIDENCE ok: 0 rows, 40 pending, 0 blank, 0 missing artifacts
0 admissibility findings
GATE fast: check_criteria.py --phase 0
CRITERIA ok: 0/0
GATE fast: ok, 3 checks
                                          -> rc=0, OK-gate-fast-green

$ make -C $FL_WT/apicula gate GATE_SCOPE=bogus
GATE bogus: unknown GATE_SCOPE (legal: fast full all)
make: *** [gate] Error 1                  -> rc=2, OK-gate-rejects-bogus-scope
```

### `V21` continued — `tests/test_gate_blocks.py`

Run detached (it makes real commits and each one runs the whole fast gate in
the foreground, so the suite is minutes-long by construction — it is one of
the 11 `heavy` tests `P0.T43` marked, and is excluded from the auto scopes by
the `gate_proof` marker).

```
$ python -m pytest tests/test_gate_blocks.py -q
.....                                                                    [100%]
5 passed in 7878.50s (2:11:18)
```

All five: a failing commit is refused with `HEAD` unmoved; a green commit
lands (the negative control); with `core.hooksPath` unset the red commit lands
(the meta-assertion that the test is sensitive to the hook, not to the
mutation); a failing push is refused with the remote ref unmoved; a green push
lands. The 2h11 is two full-scope pushes (`GATE_SCOPE=full`, heavy pytest each)
plus three fast-scope commits — the cost is the point: the gate really runs in
the foreground and really blocks. **No remote CI run was triggered by any of
it** (`C8`).

---

## E2E scenario — **PASS with two amendments**

Full record and the six conditions: `evidence/e2e-p0/summary.md`.
Row: `evidence/e2e-p0/runs.jsonl` (1 row, all 29 `REQUIRED_FIELDS`).

```
BATCH_START batch=p0-e2e-0001 shape=smoke level=E1 design_dir=$DATASTORE/e2e-p0
BATCH_HEAD selftest --inject-one-fuse: ok
BATCH_HEAD selftest --unpacker-completeness: ok
BATCH_HEAD gw_sh pre-flight: ok
BATCH_SIZE batch_runs=867 source=…/evidence/calibration/measured-budget.md parallelism=1
BATCH_RESUME batch=p0-e2e-0001 planned=1 already_terminal=0
RUN_START p0-e2e-0001-smoke-0000 sweep=None
RUN_DONE  p0-e2e-0001-smoke-0000 verdict=diff
BATCH_COMPLETE p0-e2e-0001 runs=1 ok=0 diff=1 aborted=0

WATCHDOG_ARMED batch=p0-e2e-0001 stall=6min poll=120s (independent process)
WATCHDOG_COMPLETE batch=p0-e2e-0001 saw BATCH_COMPLETE (clean exit)
```

Re-run of the identical command (condition 6):

```
BATCH_RESUME batch=p0-e2e-0001 planned=1 already_terminal=1
RUN_SKIP p0-e2e-0001-smoke-0000 (terminal row already present)
BATCH_SKIPPED batch=p0-e2e-0001 n=1 refused=0
BATCH_COMPLETE p0-e2e-0001 runs=0 ok=0 diff=0 aborted=0
```

0 `unknown option:` lines, 0 `Error` lines. `E1 placement level=E1
constrained=1 matched=1 mismatched=0 unobserved=0`; `DECODE_CHECK c1=ok c2=ok`;
`RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0`; mask unchanged.
The two amendments (`runs=3`→`1`, `diff=0`→`1`) are argued in the slug summary
and listed as `A8`/`A9` in `phase-report.md`.

---

### Artefact retention (a correction made during this close)

The `run/` trees under `$DATASTORE/e2e-p0/**` and `$DATASTORE/oracle-smoke/`
were deleted once as routine disk hygiene and then **restored by re-running**,
because an admissible row cites them: E2E condition 5 requires every
`vendor_fs`/`sdf`/`tr` path to resolve on disk with a matching sha256, and
`oracle-smoke` is the reference pair the batch head's self-tests and `V6` use.
The "delete `run/` after evidence is recorded" rule applies to throwaway runs,
**not** to a run an evidence row references. Verified after the restore:
every path in `evidence/e2e-p0/runs.jsonl` resolves with a matching sha256.

## Roll-up and the aggregate check

```
$ python $OTC/tools/evidence.py --rollup
ROLLUP evidence-table.md            # rows=24, six slugs

$ python $OTC/tools/check_evidence.py $PIPE/spec-primitives.md $OTC/evidence
EVIDENCE ok: 0 rows, 40 pending, 0 blank, 0 missing artifacts
0 admissibility findings

$ python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 0
CRITERIA ok: 0/0

$ python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence
… 55 `pending:` lines, exit 0 (the unscoped survey)
```

`0/0` for `--phase 0` is correct and expected: `spec-primitives.md` has no
`Phase` column yet (owed amendment `F31`/`A10`), and **Phase 0 closes no
primitive row** — its exit criteria are infrastructure (`S1`-`S6b`, `S17a`,
`S23b`, `S28`), not primitives. `P0.T39`'s "fill only the status cells this
phase closes" therefore resolves to **zero cells**, and `edu-provisional.flag`
being `false` means no cell would carry the ` (edu-provisional)` suffix in any
case. `spec-primitives.md` is unchanged by this task.

## Slug roll-up

| slug | rows | ok | diff | aborted | refused | other |
|---|---|---|---|---|---|---|
| calibration | 7 | 4 | 3 | 0 | 0 | 0 |
| chipdb | 12 | 0 | 0 | 0 | 0 | 12 |
| e2e-p0 | 1 | 0 | 1 | 0 | 0 | 0 |
| harness-selftest | 0 | 0 | 0 | 0 | 0 | 0 |
| oracle-smoke | 3 | 3 | 0 | 0 | 0 | 0 |
| timing-l0-cfu | 1 | 0 | 1 | 0 | 0 | 0 |
