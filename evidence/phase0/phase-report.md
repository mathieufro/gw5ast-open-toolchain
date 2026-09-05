# Phase 0 — close report (`P0.T39`)

`edu-provisional: false`. Oracle of record: Gowin **Standard 1.9.12.03**,
licensed, `$GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA`
(`C9`, `D79`). The Education install no longer exists on disk; the archived
1.9.11.03 device tree at `$DATASTORE/ide-share-device/edu-1.9.11.03` is what
the version-tolerance work is measured against.

Full literal outputs: `evidence/phase0/validation.md`.
Roll-up: `evidence/evidence-table.md` (24 rows across the **six** owned slugs
`calibration`, `chipdb`, `e2e-p0`, `harness-selftest`, `oracle-smoke`,
`timing-l0-cfu`).

## 1. Exit criteria — reached vs not

| S-id | Step | Verdict |
|---|---|---|
| entry: Licence Gate / prerequisites | `V0` | **REACHED** — gate **open** (Standard, licensed); every prerequisite line green |
| `S1` chipdb builds from the installed IDE | `V2` | **REACHED** — 138C builds on both editions, no `FAIL` line |
| `S2` no opaque parser failures | `V3` | **REACHED** — 12 `fse_version` tests; the error names IDE version, table and expected-vs-found row width |
| `S3` no family regression (25A / 60B, two **device-file sets**) | `V2` | **REACHED** — six builds, six sha256s, zero failures; **one install**, see §1b |
| `S4` oracle runs end to end | `V4` | **REACHED** — 0 `Error`, 0 `unknown option:`, four artefact classes |
| `S5` harness runs unattended and correctly | `V6`, E2E | **NOT REACHED** — machinery reached; the ≥20-run half is owed to Phase 1 — see §1a |
| `S6` equivalence checker calibrated on a whole-design baseline | `V5` | **REACHED** — three `CALIBRATION ok … 0 unexplained` lines on `big-shift`/`attosoc`/`uart-message`, mask unchanged (`59147bfc…`, six base entries, none added) |
| `S6b` unpacker is complete enough to be evidence | `V6` | **REACHED** — `COMPLETENESS ok: 0 unattributed tiles, 0 missing cells`; E2E row `decode_check {c1: ok, c2: ok}` |
| `S17a` C1/I0 de-aliased + derived, `V7` regression passes | `V7`, `V12a` | **REACHED for the de-aliasing half; the L0 ±10% band is NOT met** — see §2 |
| `S28` (creation half) forks are submodules | `V1` | **REACHED** — `apicula`, `nextpnr` are submodules of `mathieufro/*`; the throwaway `vendor/` clones are gone |
| standing: storage hygiene | `V20` | **REACHED** — deny-by-default `.gitignore`, both manifests present, 0 binaries committed |
| standing: `DEL-e` first cut exists | — | **REACHED** — `evidence.py`, `check_evidence.py`, `check_criteria.py`, `check_timing_l0.py` with their tests |
| standing: an evidence row is attributable (`fuses_moved`) | `P0.T27` | **REACHED** — `FUSES_MOVED` equals the equiv residual exactly |
| standing: `D26` measured budgets supersede §8's ASSUMED rows | E2E | **REACHED** — 6/6 rows measured; the batch runner now actually reads them (see §3) |
| standing: nextpnr `.cst` round-trip seam | `P0.T38` | **REACHED** — `case insloc`; E2E row `constrained=1 matched=1 mismatched=0` |
| `S23b` the local gate is installed and provably blocking | `V21` | **REACHED** — hooks in all three repos, `GATE_SCOPE=fast` green, a bogus scope rejected, `test_gate_blocks.py` green |

### 1a. `S5` — machinery reached, the ≥20-run half is owed to Phase 1

`S5` is two claims and Phase 0 met one of them.

**Met:** the harness runs unattended and correctly. A real detached batch,
logging to a file, watched by an **out-of-process** watchdog that fired on
completion (`WATCHDOG_ARMED` + `WATCHDOG_COMPLETE`), with a proven resume, and
the head-of-batch self-tests green.

**Not met:** *"a **≥20-run batch** completes detached"* (`spec.md:665`). The
largest batch anywhere in the evidence tree is `runs=3`
(`_runs/calib-vendor.log:11 BATCH_COMPLETE calib-vendor runs=3`); the E2E batch
is `runs=1`, correctly amended from 3 because `shapes/smoke.py` is a
single-point shape (`sweep_axis="none"`). Row counts confirm it: `e2e-p0` 1,
`oracle-smoke` 3, `calibration` 7, `timing-l0-cfu` 1.

The ≥20 half is **unreachable in Phase 0** — `smoke` is the only shape this
phase ships and it is single-point, so there are not 20 distinct points to
sweep. It is therefore **not** run here and **not** recorded as reached: the
clause moves to the first phase that ships a swept shape, **Phase 1**, which
must run it on a real multi-point shape before it closes. Recording `S5` as
REACHED on the strength of the machinery alone was the false PASS this
correction removes.

### 1b. `S3` — six builds, one install and one archived device tree

`S3`'s *"three devices × two installs"* is not what was exercised, and the
report no longer reads as though it were. The Education 1.9.11.03 **install**
no longer exists (`C9`/`D79`). What the six builds actually cover is three
devices × **two device-file sets**: the licensed Standard 1.9.12.03 install,
and the **archived** 1.9.11.03 `IDE/share/device` tree at
`$DATASTORE/ide-share-device/edu-1.9.11.03`, read directly as a bare
`<device>/<device>.<ext>` tree with `GOWIN_IDE_VERSION=1.9.11.03` forcing the
shape set.

No shim root is used and none is built: nothing under `IDE/` other than
`share/device` was archived, so there is nothing for a symlinked `IDE/` view
to be honest about. `tests/conftest.py`'s `archived_device_file` fixture and
`tests/test_dat_gw5a_stuff.py` point the parser at the archived path directly.

The claim that survives is the one that was measured — the parsers tolerate
both editions' device files. **No second install was exercised**, and the
phase is stamped `edu-provisional: false` throughout on that basis.

**Not reached, and not claimed by any Phase-0 task:** `S7`–`S16`, `S18`–`S23`,
`S24`–`S27`.

### The one criterion carrying a measured caveat — `S17a` (`P0.T37`)

`S17a` as written (no aliasing + `V7` regression) is met: `C1/I0` is no longer
a bare alias of chunk 0, the four `timing_c1i0` tests pass, and the printed
numbers sit in the DS1239E C1/I0 band, far from the C2/I1 band. What is **not**
met is the L0 arc band. Quoting `P0.T37`'s measurement against the first real
vendor SDF (attosoc, Slow 0.873 V 0 °C C1/I0):

> L0 1175/7136 arcs within ±10%, 5961 exceptions; vendor/chunk0 median 0.984,
> vendor/derived-C1I0 median 0.787 → the 1.25x derivation does not hold and
> chunk 0 fits C1/I0 for LUT/BSRAM but not DFF clk→q (1.49x); 825 SDF arcs
> unmapped (LUT1-3, IO).

Phase 0 keeps the derived `C1/I0`, and it is **`timing_model=unverified`**:
it is conservative *in aggregate only* (median ratio 0.787), and it is
**not** a conservative bound per class. `timing-l0-cfu/l0-cfu-band.md`
refutes that reading arc class by arc class — `ratio = vendor SDF / nextpnr
arc`, so `> 1` means the open model is **optimistic**:

| class | arcs | ratio (min / med / max) | conservative? |
|---|---|---|---|
| ALL | 7136 | 0.365 / **0.787** / 1.779 | in aggregate only |
| DFFRE | 532 | **1.190 / 1.190 / 1.190** | **NO — uniformly optimistic** |
| DFFSE | 12 | **1.190 / 1.190 / 1.190** | **NO — uniformly optimistic** |
| MUX2_LUT5 | 72 | up to **1.779** | NO at the tail |
| LUT4 / ALU / SDPB | 6520 | median < 1 | yes |

Every DFF `CLK->Q` arc is `model=0.289 ns` against `sdf=0.344 ns`
(`dev=-16.0%`) with **zero spread** — a systematic per-group error, not
sampling noise. On top of that, **825 SDF arcs have no nextpnr model arc at
all** (LUT3 579, LUT2 234, LUT1 2, OBUF 8, IO): an unmodelled delay
contributes zero, the most optimistic value there is.

Aggregate pessimism does not compose, because a path is the **sum** of its
arcs and a register-rich pipeline is mostly the class that is optimistic. So
every evidence row and every `openflow` `FMAX` line this phase produces
carries `timing_model=unverified` in its `notes`, and **no Fmax claim may be
made from these tables**. Phase 6 entry condition: re-identify chunk 0's grade
against the SDF medians (the `S17b`/L1 method) *before* any Fmax claim, and
until then apply per-class floors — no `CLK->Q` under the measured 0.344 ns,
and a **named error**, never a silent zero, for every unmodelled arc class.

The grade identification is **CONTESTED** and is handed to Phase 6 / `S17b`
with the SDF-corpus method (L1). A second, minor symptom of the same
derivation: `V7`'s fourth `clk_qpos` value is 0.29000 against the quoted upper
bound 0.288 (+0.7%).

**Named gaps have no magnitude ceiling yet (`D2`).** `GAP_CATEGORIES`
(`unmodelled_config_fuse`, `bsram_mode_fuse`, `extra_config_frames`,
`extra_command_words`) count toward `diffs` and never toward `unexplained`,
and `unexplained` counts **categories, not bits** — so an arbitrary number of
differing config fuses keeps `CALIBRATION ok`. That is `D32`-conformant and
the gaps are printed, but the verdict is insensitive to a gap class's
*magnitude*. Each phase from 1 on records a per-gap bit ceiling.

### The `S6` result, quoted (`P0.T33`)

> `S6` MET on all three tangmega138k baselines at E0 **and** E1: six
> `CALIBRATION ok: <n> diffs enumerated, 0 unexplained` lines, no FAIL,
> `RESIDUAL_UNEXPLAINED entries=0`, mask unchanged (`59147bfc`, six base
> entries, none added). big-shift 829,826 diffs; attosoc 879,294;
> uart-message 830,846.

Re-run in full for this close: identical counts, identical verdicts.
The passthrough LUT is settled as architecturally required (the chipdb CLS
`DFF` bel has no `D` port) — enumerated under `set_level_diff`, never masked.

## 2. Gate artefacts

**There is no human gate in Phase 0.** The only gate is the local blocking one
(`C8`, `S23b`): `.githooks/pre-commit` → `make gate GATE_SCOPE=fast`,
`.githooks/pre-push` → `full`/`all`, `core.hooksPath=.githooks` in all three
repos, proven blocking by `test_gate_blocks.py` (including its negative
control and its meta-assertion). Every commit in this close went through it;
`--no-verify` was never used. No PR is opened — PR branches are Phase 8
(`S24`). The hardware gate is Phase 9 and nothing here touched hardware.

## 3. Defects found and fixed during this close

Each was fixed on the spot with the guard that missed it repaired
(fine-line standing order), not queued:

1. **`equiv` result never became an evidence row.** `real_runner` hand-built a
   row and did `row.update(result)` on the checker's `E0Result` dataclass →
   `TypeError: 'E0Result' object is not iterable` on **every** real batch, so
   no batch could ever produce a row. Fixed by publishing
   `equiv.evidence_fields()` — the missing fragment builder beside
   `oracle.evidence_row` and `openflow.evidence_fields` — and rebuilding the
   row through `evidence.adapt()`. Four new tests pin the seam, one of them
   `evidence.validate_row`-ing the folded row.
2. **`decode_check` carried non-schema keys.** The checker's per-cell
   diagnostics (`c1_missing`, `c2_differing_bytes`, …) were passed straight
   into the schema field, which `validate_row` rejects. They are now kept as a
   `decode_detail=` note tail; the field is exactly `{c1, c2}`. One test.
3. **The batch head's self-tests pointed at `os.getcwd()`.** They need a
   reference vendor/open-flow pair; the apicula checkout has none, so both
   gates failed and `BATCH_HEAD_BLOCKED` was the only reachable outcome.
   Now `oracle.SMOKE_DIR`, overridable by `$FUZZ_HARNESS_SELFTEST_DIR`. Three
   tests.
4. **`BATCH_SIZE` silently used the ASSUMED budget.** `P0.T34`'s number lived
   only inside a three-addend worked derivation, outside the reader's
   adjacency window, so every batch sized itself off `spec.md` §8.2's
   35-minute ASSUMED row. A machine-readable single-line form was added to
   `measured-budget.md` and the reader no longer truncates the value to whole
   seconds (it was moving `batch_runs` off the recorded 867). Two tests, one
   of them against the checked-in ledger itself.
5. **`evidence/.gitignore` could not commit `edu-provisional.flag`.** `V20`'s
   allowlist covered `_runs/*.log|txt|selected` but not the flag `P0.T39` must
   read. `!_runs/*.flag` added.
6. **The `P0.T04` golden netlist was gone** with the deleted `$DATASTORE`
   mirror; recreated inside `$FL/vendor/gowin`, manifest 29607/29607 OK.
7. **The retired `vendor/apicula` and `vendor/nextpnr` clones** blocked
   `V1`'s `OK-vendor-clean`; verified to hold no unique commits and deleted.

## 4. Deviations to batch into `spec.md` Amendments

The orchestrator applies these; they are listed, not applied here.

* **A1 — `V1`'s submodule grep is unsatisfiable.** `grep -E ' (apicula|nextpnr)$'`
  can never match `git submodule status`, whose lines end with the
  `git describe` string in parentheses. Correct pattern:
  `grep -E ' (apicula|nextpnr) '`.
* **A2 — `V5`'s command is not runnable as written.** `--makefile-recipe`
  takes an argument, and the calibration design directories are
  `$DATASTORE/calibration/<design>` (per-design filtered `.cst`, `P0.T33`),
  not `examples/gw5a`.
* **A3 — `V6`'s `selftest` lines omit the required `--design-dir`.** The
  reference pair is `$DATASTORE/oracle-smoke`.
* **A4 — `V2` leaves the Education chipdb in place.** Its second loop
  overwrites `apycula/<device>.msgpack.xz` with the Education build, silently
  repointing every later step. The step must restore the Standard artefacts,
  or build to distinct output paths.
* **A5 — `V0`/`V20` name pre-`C10` paths.** `$FL` → the worktree for the code
  repos; `git -C $FL` on an `$OTC/…` path fails with "is in submodule";
  `$DATASTORE/vendor-gowin` is a deleted regenerable mirror and
  `$FL/vendor/gowin` is the source.
* **A6 — `V0` details.** `gw_sh` has no `-c` option; `gh auth status` prints
  the keyring label, so the identity assert must be `gh api user`;
  `riscv32-unknown-elf-gcc` needs `$DATASTORE/toolchains/riscv/bin` on `PATH`.
* **A7 — `V2`'s Education half needs a device-tree form.** The Education
  install is gone (`C9`); the archived bare device tree plus
  `GOWIN_IDE_VERSION` is the only executable form of the version-tolerance
  check, and the step should say so.
* **A8 — E2E `runs=3` → `runs=1`.** `shapes/smoke.py` (`P0.T20`, `F6`) is a
  single-point shape (`sweep_axis="none"`, `sweep_values=[None]`);
  `--sweep-points 3` clamps to it.
* **A9 — E2E `diff=0` → `diff=1`, attributed.** The differing cell in the
  `(2,1)` scope is the nextpnr passthrough LUT, which `P0.T33` settled as
  architecturally required and deliberately **not** masked. `diff=0` is not
  reachable for a `DFF` shape on this architecture.
* **A10 — `F31`, `spec-primitives.md` needs `Phase` and `Evidence` columns.**
  `check_criteria.py --phase 0` therefore selects nothing and reports
  `CRITERIA ok: 0/0`. `P0.T39`'s "must NOT change any non-status cell" forbids
  this task from adding the columns, and assigning a phase to each of the 41
  rows is design work belonging to the amendment. Carried forward unapplied.
* **A11 — `spec-harness.md` §3 vs measurement (`P0.T19`, `P0.T26`).**
  `create_project` requires `-pn`; `add_file` paths are `../top.v` after the
  chdir into `run/`; `INS_LOC` uses flat instance names; `DRIVE` is legal on
  outputs only; and only instances the vendor synthesiser keeps can be
  exported as `INS_LOC` (measured `CT1135`).
* **A12 — `spec-harness.md` §6 vs the calibration row shape (`P0.T33`).**
  `evidence/calibration/runs.jsonl` carries the blueprint's test-required
  fields (`design`, `yosys_cmd`, `nextpnr_cmd`, `gaps`, sha256s) beyond the
  §6 schema, so `evidence.validate_row` rejects it.
* **A13 — vendor `.fs`/`.sdf` embed `//Created Time`.** Recorded
  `vendor_fs_sha256` values are not reproducible run to run (3 bytes differ);
  rows should also record a header-stripped sha256.
* **A14 — `W-TIMING` (`P0.T37`).** The chunk-0 grade identification is
  CONTESTED; the `1.25 ×` C1/I0 derivation is refuted as a numeric model and
  retained only as a conservative bound. Hand to `S17b`.
* **A15 — `evidence/calibration/summary.md` names two files it does not
  contain.** `calibration-stdout.txt` and `calibration-stdout-E1.txt` live in
  `$DATASTORE/calibration/`, correctly (they are bulk output), but the
  summary's Evidence line says `evidence/calibration/`.
* **A16 — batch rows land in `_runs/<batch-id>.rows.jsonl`, not in the
  slug.** `F7` requires `evidence/e2e-p0/runs.jsonl`; publishing the batch
  ledger into its slug is currently a manual step and should be the batch's
  own last act.

## 5. Reproducing Phase 0's exit state from a fresh clone

```sh
# 1. Umbrella + submodules, at this phase's pointers
git clone git@github.com:mathieufro/fine-line.git $FL
cd $FL && git checkout atelier/open-toolchain-gw5ast
git submodule update --init --recursive apicula nextpnr open-toolchain

# 2. Environment (impl/LOOP-BRIEF.md §2, as amended by C9/C10)
export FL=$PWD
export OTC=$FL/open-toolchain
export PIPE=$FL/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84
export DATASTORE=/Users/alex/fine-line-data/open-toolchain-gw5ast
export GOWINHOME_STD=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export GOWINHOME=$(cat $OTC/evidence/_runs/gowinhome.selected)
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib
export DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib      # omit -> Tcl.framework not found
export PATH=$DATASTORE/toolchains/nextpnr/bin:$DATASTORE/toolchains/riscv/bin:$PATH
python3 -m venv $FL/vendor/venv && . $FL/vendor/venv/bin/activate
pip install -e $FL/apicula                          # editable, against the submodule

# 3. The local blocking gate (C8) -- do this before any commit
for r in $FL/apicula $FL/nextpnr $FL; do git -C $r config core.hooksPath .githooks; done

# 4. Rebuild what is not committed (all of it regenerable, none of it in git)
python -m apycula.chipdb_builder GW5AST-138C        # -> apycula/GW5AST-138C.msgpack.xz
                                                    #    sha256 fd1d112d0c463d9e…
python -m apycula.chipdb_builder GW5A-25A           # sha256 6311219d52b996b8…
python -m apycula.chipdb_builder GW5AT-60B          # sha256 615d4d0349ba238c…
cmake -B $FL/nextpnr/build -S $FL/nextpnr -DARCH=himbaechel \
      -DHIMBAECHEL_UARCH=gowin -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=$DATASTORE/toolchains/nextpnr
cmake --build $FL/nextpnr/build -j$(sysctl -n hw.ncpu) && cmake --install $FL/nextpnr/build
# chipdb .bin for nextpnr (P0.T40): sha256 929efdf8…, installed under
# $DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/

# 5. Re-run the phase's validation (the amended forms are in
#    evidence/phase0/validation.md; V0 V1 V2 V3 V4 V5 V6 V7 V12a V20 V21)
make -C $FL/apicula gate GATE_SCOPE=all

# 6. Re-run the E2E end to end
python -m fuzz.gw5ast138c.harness --design-dir $DATASTORE/e2e-p0 \
    --shape smoke --sweep-points 3 --level E1 \
    --batch-id p0-e2e-0001 --detach --expected-minutes 60
python $OTC/tools/evidence.py --rollup
python $OTC/tools/check_evidence.py $PIPE/spec-primitives.md $OTC/evidence
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 0
```

Pinned state at close: `apicula` `epic/gw5ast138c` (contains
`harness/gw5ast138c`, verified by `merge-base --is-ancestor`), `nextpnr`
`epic/gw5ast138c`, `open-toolchain` `main`. Nothing binary is committed;
every artefact is an absolute `$DATASTORE` path plus a sha256 in a row.
