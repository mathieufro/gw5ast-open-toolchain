# D26 calibration — measured wall clock, batch size and parallelism (P0.T34)

Measured 2026-09-04 on GW5AST-138C (part `GW5AST-LV138PG484AC1/I0`, `device_version C`),
oracle Gowin Standard 1.9.12.03 (licensed, `edu-provisional: false`). Replaces the six
ASSUMED rows of `spec.md` §8.2 (spec.md itself is not edited — Phase-0 governing-document
rule; the amendment is recorded here and at the end of this file as a parking-lot line).

## Measured rows (6/6, 0 ASSUMED)

| # | Quantity | ASSUMED | MEASURED | Design used | Notes |
|---|---|---|---|---|---|
| 1 | `gw_sh run all`, minimal 138K design | ≤ 10 min (600 s) | **23.144 s** | harness smoke `top.v`/`top.cst`/`top.sdc` (oracle-smoke) | rc=0, preflight ok |
| 2 | `gw_sh run all`, largest available design | ≤ 45 min (2700 s) | **26.834 s** | `attosoc-tangmega138k` (Phase 0 has no stand-in fabric — that's Phase 7; per the blueprint's explicit instruction, attosoc-tangmega138k is used and named here rather than leaving the row blank) | rc=0 on the 3rd attempt — see Deviations |
| 3 | chipdb build, `GW5AST-138C` | ≤ 30 min (1800 s) | **33.071 s** | fresh timed build, Standard install, own output path (`$DATASTORE/calibration/chipdb-timing/`); does **not** reuse or touch `P0.T15`'s six sha256s/artefacts | rc=0. (GW5 devices need no `gw_sh` for chipdb — Box notes — so this did not touch the build lock) |
| 4 | yosys synth, one stand-in | ≤ 5 min (300 s) | **5.064 s** | `attosoc-tangmega138k`, `yosys -p 'read_verilog ...; synth_gowin -family gw5a -json top.json -setundef -top attosoc'` | rc=0 |
| 5 | nextpnr PnR, one stand-in on 138K | ≤ 20 min (1200 s) | **13.273 s** | same design, `nextpnr-himbaechel --device GW5AST-LV138PG484AC1/I0 --chipdb <bin> --vopt cst=... --top attosoc --timing-allow-fail` | rc=0 |
| 6 | Parallelism (concurrent oracle pipelines) | **1** (ASSUMED, Licence Gate to verify) | **≥ 2, both succeed** | two `gw_sh` invocations on the minimal design launched together, **no** build-lock serialisation (that absence is the measurement) | rc=0/rc=0, both `preflight_ok`; Standard licence (not `edu-provisional`) — this **is** the Licence-Gate-scoped answer `D51` asks for. Both runs completed in ~16.0 s each (faster than the serial 23.1 s single run — plausibly warm Gowin project-template/db caches from the day's many prior runs, not a real speed-up; flagged, not claimed as fact) |

All 6 rows measured; 0 cells read `ASSUMED`.

## Derived numbers

```
measured_per_run_total = oracle(minimal) + yosys(stand-in) + nextpnr(stand-in)
                        = 23.144 + 5.064 + 13.273
                        = 41.481 s
```

(Mixed-scale, same as `spec.md` §8.2's own worked example, which combines the minimal
oracle row with the stand-in yosys/nextpnr rows into one "per differential run" figure —
`yosys`/`nextpnr` were only measured end-to-end on `attosoc`, the one design where the
full open-flow pipeline is available at Phase 0; a future phase with primitive-scale
shapes should re-measure `yosys`/`nextpnr` at that scale and refresh this number. Recorded
as a parking-lot note, not fixed here.)

```
batch_runs = floor(10 h * parallelism / measured_per_run_total)
  @ parallelism = 1 (spec.md default until measured):  floor(36000 / 41.481) = 867
  @ parallelism = 2 (this run's measured floor):        floor(72000 / 41.481) = 1735
```

```
campaign_wall_clock_s = runs * measured_per_run_total / parallelism
```
(`runs` is the grand total owned by `spec-primitives.md` §7, `D54` — not restated here.)

**`batch_runs = 867`** (parallelism = 1, the number `test_batch_size_formula_applied`
checks: `floor(36000 / 41.481) = 867`).

## Overrun check (`spec.md` §8.2: recompute if measured > 2x ASSUMED)

None of the 5 timed quantities overran; no `OVERRUN` line is emitted for real data:

| quantity | measured/assumed ratio |
|---|---|
| minimal gw_sh | 0.039x |
| largest gw_sh | 0.010x |
| chipdb build | 0.018x |
| yosys | 0.017x |
| nextpnr | 0.011x |

Self-check of the overrun rule (synthetic, not a real measurement): a synthetic
`chipdb_build = 3 x 1800 s = 5400 s` would print `OVERRUN chipdb_build measured=5400s
assumed=1800s ratio=3.0x` — confirming the >2x flag fires correctly; no such line appears
above because nothing overran.

## Parallelism verdict (`D51`)

**Concurrency works on the licensed Standard install**: two simultaneous `gw_sh`
invocations both completed successfully (rc=0, clean preflight) with no refusal and no
licence error. `spec.md`'s ASSUMED parallelism of 1 is now MEASURED ≥ 2. This is the
Licence-Gate-scoped verification `D51` calls for (Education is retired; the box runs
Standard 1.9.12.03 licensed — `edu-provisional: false` throughout this run). Only a pair
was tried (bounded by the ≤ 12 new-vendor-run budget for this task); higher concurrency
(3+) is untested and should not be assumed from this result — recorded as a bound, not a
ceiling.

## Provenance

- `apicula` (worktree, branch `epic/gw5ast138c`): `b1989678cbc9faa8c73a61be9172f04be836767f`
  at read time (this branch had concurrent commits landing from another task during this
  run; the sha is a snapshot, not a claim that nothing else touched the tree)
- `chipdb` sha256 (this task's own timed build): `fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb`
- `ide_version`: `1.9.12.03 Standard`
- `yosys_version`: `0.63 (70a11c6)`
- Raw results: `$PIPE/evidence/calibration/runs.jsonl` (4 new rows,
  `calibration-D26-{minimal,largest,parallel-a,parallel-b}-0001`), `$DATASTORE/calib/results.json`

## Deviations

- **`largest` (attosoc-tangmega138k) needed two fixes before it produced a real timing
  number, not a fast constraint-error abort:**
  1. `examples/gw5a/tangmega138k.cst` is shared across three designs (`big-shift`,
     `attosoc`, `uart-message`) and constrains `led[0..15]`, `reset`, `uart_tx`, `uart_rx`;
     `attosoc`'s top module only drives `clk` and `led[7:0]`. `nextpnr --vopt cst=` silently
     ignores a constraint on an absent port; the vendor `gw_sh` aborts the whole run with
     `ERROR (CT1135) : Can't find object named ...`. Fix: a copy of the `.cst` filtered to
     the ports `attosoc` actually declares, written under
     `$DATASTORE/calib/largest/tangmega138k.cst` — `examples/gw5a/` itself is untouched.
  2. Even filtered, the vendor placer refused `led[0]`, `led[1]`, `led[3]` with
     `ERROR (PR2017) ... dedicated pin (CPU/SSPI)`, because those package pins are also
     the SSPI function and the harness's default Tcl only sets `-use_cpu_as_gpio 1`
     (matching `examples/gw5a/Makefile`'s `gowin_pack --cpu_as_gpio`, which never needed
     `sspi_as_gpio` because nextpnr's open-flow tolerates the same constraint silently).
     Fix: passed `-use_sspi_as_gpio 1` via `oracle.py`'s existing, already-published
     `extra_options` parameter of `render_tcl`/`write_tcl`/`run_oracle` (used today by the
     AE350 shape per its own docstring) — `oracle.py` itself was not edited, only called
     with an argument it already supports.
- **A concurrent task (`P0.T33`) shares `$PIPE/evidence/calibration/runs.jsonl` as an
  append-only registry and was mid-batch when this task started.** An early write from
  this task's own tooling used `open(..., "w")` and clobbered T33's already-completed rows
  (3 designs x `E1`, `S6` calibration). Recovered without any new vendor run: T33's own
  `calibration-stdout.txt`/`calibration-stdout-E1.txt` transcripts (untouched) still held
  every JSON row T33's script would have written; those were re-parsed and the 3 rows
  reconstructed byte-for-byte against T33's own `summary.md` numbers (829826 / 879294 /
  830846 diffs enumerated, all matching), then this task's 4 rows were appended after them.
  Root cause: `runs.jsonl` is a shared append-only registry (`spec-harness.md` §6) and this
  task's tooling opened it destructively instead of appending — a process defect in this
  task's own scratchpad script, not in any frozen/owned file. No frozen or owned file was
  touched to fix it.
