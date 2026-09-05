# `e2e-p0` — the Phase-0 end-to-end scenario (`P0.T39`, blueprint §E2E)

Measured 2026-09-04 on GW5AST-138C (part `GW5AST-LV138PG484AC1/I0`,
`device_version C`), oracle Gowin Standard 1.9.12.03 (licensed,
`edu-provisional: false`). Nothing in this run is stubbed, mocked or
short-circuited: the real `gw_sh`, the real `nextpnr-himbaechel`, the real
`gowin_pack`/`gowin_unpack`, two real 34 MB bitstreams.

Command (verbatim, from `$FL_WT/apicula`):

```sh
python -m fuzz.gw5ast138c.harness \
    --design-dir $DATASTORE/e2e-p0 \
    --shape smoke --sweep-points 3 --level E1 \
    --batch-id p0-e2e-0001 --detach --expected-minutes 60
```

## The six conditions

| # | Condition | Result |
|---|---|---|
| 1 | `SELFTEST ok: 1 difference reported, 0 spurious`, `COMPLETENESS ok: 0 unattributed tiles, 0 missing cells`, final `BATCH_COMPLETE` line | **met, with the run count amended** — `BATCH_COMPLETE p0-e2e-0001 runs=1 ok=0 diff=1 aborted=0`; see *Amendments* |
| 2 | 0 `unknown option:` lines, 0 `Error` lines in the batch log | **met** |
| 3 | exactly 1 `WATCHDOG_ARMED` line and one terminal line, the clean-exit one | **met** — `WATCHDOG_ARMED batch=p0-e2e-0001 stall=6min poll=120s`, then `WATCHDOG_COMPLETE … saw BATCH_COMPLETE (clean exit)` |
| 4 | `runs.jsonl` rows carry all 29 `REQUIRED_FIELDS`, `primitive=DFF`, scope tile `(2,1)`, `verdict=ok`, `unexplained_bits=[]`, `decode_check={c1:ok,c2:ok}`, `level=E1` | **met except `verdict`** — 29/29 fields, `primitive=DFF`, scope `(2,1)`, `unexplained_bits=[]`, `decode_check={"c1":"ok","c2":"ok"}`, `level=E1`, `verdict=diff`; see *Amendments* |
| 5 | every artefact path absolute under `$DATASTORE` with a matching sha256; 0 binaries committed | **met** — `vendor_fs` 34,668,941 B, `open_fs`, `sdf`, `tr`, `oracle_log`, `open_log` all under `$DATASTORE/e2e-p0/…`; `git ls-files evidence/e2e-p0 \| grep -cE '\.(fs\|vo\|tr\|sdf)$'` = 0 |
| 6 | re-running the identical command resumes rather than repeats | **met** — second invocation: `BATCH_RESUME … already_terminal=1`, `RUN_SKIP p0-e2e-0001-smoke-0000`, `BATCH_SKIPPED … n=1`, `BATCH_COMPLETE … runs=0`; `runs.jsonl` still 1 row |

Logs: `_runs/p0-e2e-0001-run1.log` (the executing run),
`_runs/p0-e2e-0001.log` (the resume run), `_runs/p0-e2e-0001.watchdog.log`.

## The one row

`level=E1`, `E1 placement level=E1 constrained=1 matched=1 mismatched=0
unobserved=0` — the `INS_LOC` seam (`P0.T38`) holds on a real batch:
`dut_dff` is placed where the export asked.

`DECODE_CHECK c1=ok c2=ok` (c1 recovered 13/13 placed cells, 6 not
fuse-backed; c2 0 differing bytes of 4,147,478).

`RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0`. Every residual bit is
attributed: `net_route` 3,871,035 / `io_default_unused_pins` 648 /
`vendor_only_fill` 33 / `comment_header` 634 B (all masked, base entries),
`set_level_diff` 41 bits (visible to the E0 sets, never masked), plus two
named gaps already owned by later phases — `unmodelled_config_fuse` 18 bits /
3 tiles (Phase 1, Phase 3) and `extra_command_words` 20 B (Phase 8).

`DIFF_COUNT cells=3 attrs=36 conns=40`, first diff
`tile (2,1) bel 2: cell vendor=<absent> open=LUT`. The mask is unchanged:
`59147bfc…`, six base entries, none added.

## Amendments this run owes the spec

1. **`runs=3` → `runs=1`.** `shapes/smoke.py` (`P0.T20`, `F6`) declares
   `sweep_axis="none"`, `sweep_values=[None]` — `smoke` is a single-point
   shape by construction, "its job is to prove the flow end to end, not to
   attribute a fuse". `--sweep-points 3` clamps to the shape's own sweep, so
   1 run is the correct and only reachable count. Repeating an identical
   single-point design three times would prove nothing further.
2. **`diff=0` → `diff=1`, fully attributed.** The differing cell at
   `(2,1)` bel 2 is the nextpnr passthrough LUT, which `P0.T33` settled as
   **architecturally required and deliberately not masked**: the chipdb CLS
   `DFF` bel has no `D` port (`portmap {CE,CLK,LSR,Q}`), the flop's data input
   being hard-wired to the paired LUT's `F` inside the slice, so
   `gowin.cc:1199 create_passthrough_luts` must insert it. It is enumerated
   under `set_level_diff`, the class `S6`/`D32` declares expected. `diff=0` at
   tile `(2,1)` is therefore not reachable for a `DFF` shape on this
   architecture, and the E2E's expected result is amended to `diff=1` with the
   diff attributed to that class — not to a mask entry.

## Re-measured after the §5.3 mask conditions were implemented (2026-09-05)

The recorded `unexplained 0` above was produced by a checker that classified a
differing fuse by its chipdb **fuse-group name alone**, so neither conditioned
mask row ever tested its own condition: §5.3 row 5 masks *"the physical route
of a net whose endpoint set matches"* and row 6 masks the IO default *"only
when both sides carry a defaulted value"* on *"pins used by neither design"*.
Both conditions are now implemented (`equiv.refine_group_category`). Re-running
`residual()` on the same real `.fs` pair, unchanged, with the same mask file:

```
explained    set_level_diff 41 | vendor_only_fill 33 (unused_tile_fill)
             net_route 4 (net_route) | io_default_unused_pins 6
             comment_header 634 B (header_words)
unexplained  net_route_endpoint_diff 3,871,031
             io_used_pin_config 333 | io_nondefault_config 309
             total 3,871,673 bits
```

**This is the same bitstream pair and the same numbers, re-attributed.** Of the
3,871,035 bits previously masked as `net_route`, only **4** drive a wire whose
net has the same endpoint set on both sides; of the 648 masked as
`io_default_unused_pins`, only **6** are on an IOB site neither design uses and
outside every `DRIVE`/`PULLMODE` fuse. The rest were never covered by the mask
rows as those rows are written.

The measurement itself is not in dispute — the vendor side unpacks 138,576
cells against the open side's 873, so the two bitstreams genuinely do not share
their routing, and almost none of the routing delta is "one net routed two
ways". What changes is that the checker no longer reports that as nothing.

**`unexplained 0` therefore does not hold for this pair, and no Phase-0
criterion may be read as having been closed on it.** What Phase 0 established
here stands unchanged: the flow runs end to end, the residual is reproducible
byte for byte, and every bit is attributed to a named class. What it did not
establish is that the vendor and open bitstreams agree once the mask is held
to its own conditions. Whether the smoke pair is expected to agree at that
level, or whether §5.3's rows want re-scoping for a whole-device comparison, is
a spec question for the orchestrator, recorded here rather than masked away.
