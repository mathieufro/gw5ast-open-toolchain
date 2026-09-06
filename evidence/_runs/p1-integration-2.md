# `p1-integration-2` — P1.T38b full integration + the E2E (2026-09-06)

Second and final Phase-1 integration pass. Every `clocking/*` branch plus the
epic's harness decode fix is merged into `integration/p1-clocking` in both
forks, the toolchain pair is rebuilt from the merged trees, and the phase's
end-to-end design runs through it. `P1.T38` proper (rebase onto
`upstream/master`, branch scope check, the two `fine-line` pointer commits) is
still phase-end work; **no umbrella pointer was touched here.**

## 1. Branches merged

### apicula — `integration/p1-clocking` = `2b26bcd`
Base `9ec95c2` (the `P1.T38a` tip plus the `gw5a-hclk-6block` merge), then five
merges in this order:

| branch | tip taken | merge commit |
|---|---|---|
| `epic/gw5ast138c` | `2d4c232` (the harness decode fix) | `dd2058d` |
| `clocking/gw5a-hclk-6block` | `20451cb` (P1.T14 + P1.T15) | `a705e55` |
| `clocking/dqce-dcs-quadrants-138c` | `a2179ca` (P1.T28) | `092d396` |
| `clocking/plla-138c` | `973b31b` (P1.T23) | `3feef0c` |
| `clocking/hclk-6block-138c` | `ac4da09` (hooks, C12/D95) | `2b26bcd` |

`clocking/dhcen-gw5a` (`e4efd41`) and `clocking/iologic-guard-spelling`
(`39e5976`) were already ancestors from `P1.T38a` and needed no merge.
`clocking/pll-timing-138c` (`d88235a`, P1.T33) is **not** in this integration —
it was not in the task's list.

### nextpnr — `integration/p1-clocking` = `6514b80c`
Base `527c7169` (`P1.T38a` + `D101`), then one merge:

| branch | tip taken | merge commit |
|---|---|---|
| `clocking/gw5a-hclk-6block` | `af8e8c03` (hooks, C12/D95) | `6514b80c` |

The merge changes **no source**: `git diff 527c7169 6514b80c` is empty outside
`.githooks/`, which is why the rebuilt binary's sha256 is unchanged.

## 2. Conflict resolution (1)

`fuzz/gw5ast138c/harness/gen.py`, three hunks, `epic` vs
`clocking/gw5a-hclk-6block`. Both sides had changed `render_cst`: the epic side
to let an `ins_loc` **value** be a callable `(sweep_value) -> site`, the branch
side to add `with_ins_loc=False` for the split `top-open.cst` and the
`ins_loc_of` helper (whose callable form is at the *dict* level). Kept
**both**: the branch's signature and `ins_loc_of`, plus the epic's per-value
callable inside the loop. No behaviour of either side was dropped; both
docstrings survive.

## 3. Toolchain artefacts (rebuilt from the merged trees)

| artefact | sha256 | bytes |
|---|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `ba885471feab93f6a659b39a517e2e0ed71f5f8b38d53eb9ff366d17dec5850c` | 819 184 |
| `chipdb-GW5AST-138C.bin` | `986d698919480d3de39668162084ea36824727aac1afb43b2779a45bb91a645c` | 32 219 031 |
| `nextpnr-himbaechel` | `38dbe2cd72486b38466b88775c0bc3dc0dfd5b2c7fa720f73491ec87b776ce60` | 4 034 624 |

* The msgpack was built **twice** from the merged worktree: identical both
  times.
* The `.bin` was built **twice**, the second under a different
  `PYTHONHASHSEED`: identical both times, 2849 unique tile routing shapes
  (the `D101` figure).
* **A trap worth recording.** `himbaechel/uarch/gowin/CMakeLists.txt` runs
  `gowin_arch_gen.py` with the venv's Python, and the venv's `apycula` is an
  editable install of the **main submodule checkout**, not the integration
  worktree. A plain `cmake --build` therefore generated the `.bin` from the
  wrong tree (`f77291ae…`, 2786 shapes). The build must be run as
  `PYTHONPATH=<apicula integ worktree> cmake --build .`, and the `.bba`
  deleted first so the generator actually re-runs.

**Matching pair installed together** (binary + `.bin`, per the LOOP-BRIEF rule
that a constids change invalidates every older `.bin`):
`$DATASTORE/toolchains/nextpnr/bin/nextpnr-himbaechel`,
`$DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/chipdb-GW5AST-138C.bin`,
`$DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin` (the harness `--chipdb` pin) and
`$DATASTORE/chipdb/std/GW5AST-138C.msgpack.xz`; all copies verified identical
after install.

## 4. The E2E — `E1 ok`

Full write-up and the excluded primitives: `../clocking/summary.md`. Two oracle
runs were spent, both against the pair above:

| batch | design | verdict |
|---|---|---|
| `p1t38b-e2e` | DHCE gate + CLKDIV, block 5 lane 0 | `diff` — one bit, the DHCE gate the open flow never sets (`P1.T27`) |
| `p1t38b-e2e2` | two CLKDIVs, block 5 lanes 0 and 2, `DIV_MODE` 4 and 8 | **`ok`, `E1`** |

```
EQUIV E1 ok
BATCH_COMPLETE p1t38b-e2e2 runs=1 ok=1 diff=0 aborted=0
```

`cells = 0`, `attrs = 0`, `conns = 0`, `unexplained_bits` empty,
`decode_check {c1: ok, c2: ok}`, `chipdb_sha256 986d6989…`.

## 5. Changes this task made beyond the merges

* **`D103` implemented.** `CLKDIV2` joins `equiv.NON_FUSE_BACKED_BELS` with its
  justification, and `c1` now asks instead for the chained `CLKDIV` decoding
  `DIV_MODE = 2` on the same lane — the exemption is conditional, not blanket
  (`tests/test_clkdiv2_non_fuse_backed.py`). The seven `P1.T15` pinned rows are
  re-derived from the fields they already carry, close `ok`, and the
  `spec-primitives.md` `CLKDIV2` status cell becomes `E0+hw-pending`.
* **A latent defect found while doing it.** `equiv._hclk_type` stripped the
  index suffix *characterwise* (`rstrip("_0123456789")`), so `"CLKDIV2_1"` came
  back as `"CLKDIV"` and the function could never return `"CLKDIV2"` at all —
  contradicting its own docstring and silently collapsing the two primitives in
  `hclk_realised`. Fixed to strip exactly one trailing `_<digits>`, with a test.
* **`c1` skips nextpnr's `$PACKER_DHCEN_*` placeholders** — see
  `../clocking/summary.md`.

## 6. Deviations

* `P1.T40`'s `examples/gw5a/clocktree_e2e-tangmega138k.v` and its Makefile
  entry are **not** written here: the port names this design needs collide with
  the `led[0..15]` / `clk` / `reset` set `examples/gw5a/tangmega138k.cst`
  already binds (one `.cst` serves every tangmega138k design, **F39**), so
  appending them would break the other examples. The shape is the runnable
  artefact and it exists; the example file stays `P1.T40`'s.
* `.githooks/pre-push` still resolves `$OTC` relative to the pushing worktree,
  so gate markers land beside the worktree rather than in `$OTC` (recorded in
  `p1-integration-1.md`, still not fixed).
