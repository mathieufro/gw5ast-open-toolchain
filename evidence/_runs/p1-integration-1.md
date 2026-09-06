# `p1-integration-1` — P1.T38a interim integration + D101 (2026-09-06)

Interim landing of Phase 1's clocking work onto `integration/p1-clocking` in both
forks, plus the `D101` nextpnr determinism fix. `P1.T38` proper (branch scoping,
rebase onto `upstream/master`, the two `fine-line` pointer commits) still runs at
phase end; **no umbrella pointer was touched here**.

## 1. Branches merged

### apicula — `integration/p1-clocking` = `4232744`
Reset to `epic/gw5ast138c` `b9447d4`, then four merges in this order:

| branch | tip taken | merge commit |
|---|---|---|
| `clocking/gw5a-hclk-6block` | `4c133f6` (P1.T08c; the branch was live — this is the tip at merge time) | `ee4596e` |
| `clocking/dhcen-gw5a` | `e4efd41` (P1.T26; already contained hclk) | `eced385` |
| `clocking/plla-138c` | `c0c4133` (P1.T22) | `3cc6dca` |
| `clocking/iologic-guard-spelling` | `39e5976` (P1.T12-T13) | `4232744` |

`clocking/dqce-dcs-quadrants-138c` (`258254b`) is **not** in this merge — it was
not in this task's list.

### nextpnr — `integration/p1-clocking` = `527c7169`
Reset to `epic/gw5ast138c` `d73142a`, then:

| branch | tip taken | merge commit |
|---|---|---|
| `clocking/gw5a-hclk-6block` | `8566c51` (P1.T10) | `cee74d8` |
| `clocking/dhcen-gw5a` | `39859be` (P1.T26) | `327a37c4` |

plus the D101 commit `527c7169` on top.

## 2. Conflict resolutions (3)

1. **`apycula/gowin_pack.py`** (plla vs dhcen, in `class GW5AST_138C`) — both
   branches inserted a section immediately after the class docstring. Kept
   **both**: DHCE's `get_DHCEN_fuses` override (from dhcen) stays first, PLL's
   `get_permitted_pll_freqs`/`check_pll_fvco` (from plla, merged cleanly after
   `__init__`) untouched. No line of either branch was dropped.
2. **`tests/test_gw5ast138c_clocking.py`** (add/add, hclk vs iologic) — the file
   is shared by two tasks. Kept **every test from both sides**: the 20 HCLK
   tests (P1.T05-T09) followed by the 4 IOLOGIC-guard tests (P1.T12-T13); the
   iologic side's `gowin_pack` and `tests.fixtures.no_hclk_device` imports were
   hoisted to the file's import block. 24 tests total, all collected.
3. **`nextpnr/Makefile`** (gate comment block) — took the hclk side, which is the
   one describing the now-real `himbaechel/uarch/gowin/tests/` scripts.

## 3. Test run — apicula `integration/p1-clocking`

```
PYTHONPATH=<apicula integ worktree> python -m pytest tests -q -m "not heavy and not gate_proof"
287 passed, 2 skipped, 59 deselected, 1 xfailed in 20.61s
```

**0 failures, 0 errors.** No pre-existing unrelated failure survived: the first
run of the fresh worktree showed 1 failure + 3 errors
(`test_unpack_gw5a_completeness.py::test_gw5ast_iob_tables_are_all_aliased` and
the three `test_selftest.py` mask-probe tests) — all four were the worktree
simply not having a built `apycula/GW5AST-138C.msgpack.xz` yet, and all four pass
once it is built. The one `xfail` and the two skips are pre-existing.

## 4. Chipdb artefacts

| artefact | sha256 | bytes |
|---|---|---|
| `apycula/GW5A-25A.msgpack.xz` | `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca` | 321484 |
| `apycula/GW5AST-138C.msgpack.xz` | `1ca8157c99dc81e27593775d1d7a83737d3fae3d0d264e5510d7dbebec6df62a` | 816760 |
| `chipdb-GW5AST-138C.bin` | `570a2e3b4463d30eb9491b4c649587d811070edd9575977158afdfc495d075dc` | 32,199,522 |
| `nextpnr-himbaechel` (installed) | `38dbe2cd72486b38466b88775c0bc3dc0dfd5b2c7fa720f73491ec87b776ce60` | 4,034,624 |

`GW5A-25A` is `6311219d…`, **byte-identical to the P0.T40 baseline** — the merge
changed no pre-138C code path. `GW5AST-138C.msgpack.xz` built twice, identical.

`chipdb-GW5AST-138C.bin` regenerated **twice** from the same
`GW5AST-138C.msgpack.xz` with the newly built binary's `bbasm`: both runs
`570a2e3b…`, byte-identical. The `.bin` is now **32.2 MB, down from 63.86 MB** —
see D101: the old file was ~2x larger purely because the randomised order
defeated tile-shape deduplication (19825-19832 "unique" shapes vs 2849 real ones).

**Matching pair installed together** (binary + `.bin`, per the LOOP-BRIEF rule
that a constids change invalidates every older `.bin`):
`$DATASTORE/toolchains/nextpnr/bin/nextpnr-himbaechel`,
`$DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/chipdb-GW5AST-138C.bin` and
`$DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin` (the harness `--chipdb` pin) —
the two `.bin` copies verified identical after install.

## 5. D101 — `gowin_arch_gen.py` non-determinism

**Reproduced first, on the pre-fix generator**: three runs over one msgpack gave
`.bba` sha256 `51a50103…`, `d8f98c1c…`, `d7c598cf…` and 19825 / 19830 / 19832
unique tile shapes. So the installed `.bin` was never reproducible and no sha256
recorded for it in any earlier phase means what it claims to mean.

**Root cause — three places where a set of strings decides an output order:**

1. `create_global_nodes` iterated `db.nodes`' **member set** directly. It holds
   `(y, x, wire)` tuples, so its order is `PYTHONHASHSEED`-dependent, and it
   fixes both the wire-creation order inside the tile types and the `NodeWire`
   order of the node. This is the dominant one: it is what destroyed the tile
   shape dedup.
2. `create_extra_data` iterated `db.io2hclk`'s and `db.hclk_div2`'s member sets,
   fixing the order of those extra-data arrays.
3. ~20 `for x in {'A', 'B'}` **set literals** in the IO/IOLOGIC/BSRAM/DSP tile
   type builders, plus `_bsram_inputs`, fixing wire and bel-pin creation order
   inside those tile types. (Symptom seen in the diff: BSRAM `W0` was `CLK0` in
   one run and `CE1` in the next.)

Fix: sort at (1) and (2), tuples at (3). None of the converted literals was used
in a membership test. After the fix: 2849 shapes and one sha256 across every run,
for both `GW5AST-138C` and `GW5A-25A`.

**New gate check** `himbaechel/uarch/gowin/tests/check_arch_gen_deterministic.py`
builds the `.bba` twice, in two interpreters with two *different*
`PYTHONHASHSEED`s (one seed would pass even on the broken generator), and
compares sha256. It hangs off `_gate-fast` — the single definition of green — and
takes ~41 s. `gate.env` gains `APICULA_ROOT` and `GATE_PYTHON` (apicula's
`msgpack`/`numpy` are in the project venv, not system `python3`).

**The gate is validated, not assumed**: run against the pre-fix generator it
fails red (`.bba` `af4161c6…` vs `45571b98…`); against the fixed one it prints
`OK-arch-gen-deterministic`.

## 6. Openflow smoke — exit 0

`fuzz.gw5ast138c.harness.openflow` on the P0.T21 smoke design, against the newly
installed pair:

```
STEP yosys       returncode=0  0.598s
STEP nextpnr     returncode=0  2.060s
STEP gowin_pack  returncode=0  7.736s
FMAX clock=clk_IBUF_I_O mhz=3012.05 verdict=PASS target_mhz=12.0
BITSTREAM top.fs 34668145 489587b1a547414a168664f1ccb38a7629df77316c3194ffc6947204a6170c64
chipdb_sha256=570a2e3b…  timing_allow_fail_needed=False
```

Design dir `$DATASTORE/batch/p1t38a/smoke/`.

## 7. T26 DHCE design — placement PASSES, routing still blocked (D100)

Re-ran P1.T26's DHCE design (`$DATASTORE/clocking/dhcen/openflow/top.v`, 24 DHCE
+ 4 CLKDIV) through yosys + the newly installed `nextpnr-himbaechel`/`.bin`, in
`$DATASTORE/batch/p1t38a/dhce/`:

* chipdb loads with **0 errors** (`Using uarch 'gowin' for device
  'GW5AST-LV138PG484AC1/I0'`);
* `DHCEN: 25/24 (104%)`, `CLKDIV: 4/24` — the **24 hardware DHCE bels** are
  present in the six HCLK blocks and placed, plus the design pseudo cell;
* placement completes (HeAP + SA, `Checksum: 0x332983e8`);
* **routing then fails**, exactly as P1.T26 recorded and exactly as `D100`
  predicts: `Warning: Failed to route net 'hclk[0]' from X91Y108/CLK1 to
  X64Y108/CLKDIV_I43 using dedicated routing.` / `ERROR: Can't route the hclk[0]
  network.`, exit 125.

This is the expected state, not a regression: `D100`/`P1.T08c` own the central
clock-mux table (fse table 38) that the HCLK routing needs, and `P1.T08d` is
where it gets read. The DHCE deliverable is the bels and the fuse, both of which
this run confirms survive the merge.

## 8. Gates

Both pushes spawned the detached branch-scope gate; both **PASS**:

| repo | marker | verdict |
|---|---|---|
| apicula | `integ-integration-p1-clocking-4232744` | `PASS` — `287 passed, 2 skipped, 59 deselected, 1 xfailed`, `BATCH_COMPLETE` |
| nextpnr | `integ-integration-p1-clocking-527c7169` | `PASS` — `hclk-6block 2/2`, `OK-arch-gen-deterministic`, `BATCH_COMPLETE` |

Marker files copied into `evidence/_gates/` (gitignored local artefacts, on disk only)
— see the deviation below.

## 9. Deviations and unrelated breakage (noted, not fixed)

* **apicula's `integration/p1-clocking` needed a `--force-with-lease` push.** The
  remote tip was `1c27447` ("GitHub CI: updated workflows to avoid Node.js
  version warnings", an upstream commit), which the reset-to-`epic` dropped from
  the branch's history. Checked before forcing: `git diff HEAD 1c27447 -- .github`
  is **empty** — that commit's content is already in the merged tree via
  `clocking/dhcen-gw5a`, so nothing was lost. nextpnr pushed fast-forward.
* **`.githooks/pre-push` resolves `$OTC` relative to the pushing worktree.** From
  a per-branch worktree the gate markers land in
  `<worktree>/../open-toolchain/evidence/_gates/` (apicula) and
  `<worktree>/open-toolchain/evidence/_gates/` (nextpnr) instead of the real
  `$OTC`; the nextpnr case **creates an untracked `open-toolchain/` directory
  inside the nextpnr worktree**, which a future `git add -A` would commit. Both
  markers were copied into `$OTC/evidence/_gates/` by hand here. Unrelated to
  this task — recorded, not fixed.
* **`openflow.py`'s `PROVENANCE` line reports stale repo shas** (`apicula_sha=
  4232744…` is right, but `nextpnr_sha=8566c51d…` is the *main submodule
  checkout's* HEAD, not the integration worktree the binary was built from). The
  `chipdb_sha256` it records is correct and is the one that matters. Recorded,
  not fixed.
* `P1.T38` proper is **not** done: branches are not rebased onto
  `upstream/master`, not scope-checked, and **no `fine-line` pointer commit was
  made**. That is phase-end work.
