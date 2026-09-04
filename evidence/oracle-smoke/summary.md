# `oracle-smoke` — S4, the vendor oracle runs end to end (P0.T19)

`V4` passes verbatim on the install of record.

```
cd $DATASTORE/oracle-smoke && time $GOWINHOME/IDE/bin/gw_sh run.tcl > gw_sh.log 2>&1
exit=0            30.5 s wall
grep -c 'Error' gw_sh.log            -> 0
grep -c 'unknown option:' gw_sh.log  -> 0
run/impl/pnr/run.fs   34,668,941 B
run/impl/pnr/run.sdf       5,193 B
run/impl/pnr/run.tr       27,589 B
run/impl/pnr/run.vo        1,215 B
```

Design: 4-stage shift register, primitive under test one `DFF` instance
`dut_dff`, tile-pinned `INS_LOC "dut_dff" R2C3[0][A];`. Artefacts are named
after the **project** (`run.*`), never the top module, so the collector globs
on the extension and never assumes a basename.

## Install of record — the Licence Gate moved on 2026-09-04

- Standard 1.9.12.03 `/Applications/GowinIDE.app` **now passes** the `gw_sh`
  smoke (`TCL_ALIVE 8.6`, exit 0, 0.47 s). It printed
  `License verification failed  Connection timeout.` at 13:08 and passed at
  13:12 the same day. Rows here are `1.9.12.03 Standard`, `edu-provisional:
  false`.
- Education 1.9.11.03 `/Users/alex/Desktop/GowinIDE.app` was **removed from
  disk** in the same window. `evidence/_runs/gowinhome.selected` still names
  it and is stale.
- Three pre-existing tests fail purely because of that removal
  (`test_fse_version_longfuse_width_is_derived`, two
  `test_legacy_device_row_widths_unchanged[139-drpfuse-10-*]` rows): they
  encode Education 1.9.11 row widths and now see Standard 1.9.12. Verified
  failing on `HEAD` without this task's changes. Not fixed here.

## Measured facts that contradict the governing documents

Recorded, not edited: `spec-harness.md` §3 is frozen for this phase.

1. `create_project` **requires** `-pn <partnumber>`. Without it the command
   aborts with `No target device in this project`, whether or not `set_device`
   precedes it. `spec-harness.md` §3 / F57 state there is no `-pn`; the
   `libGWTE.dylib` option block they read (`-name -dir -device_version
   -force`) is incomplete.
2. `create_project` chdirs into `run/` **before** `add_file` runs, so the bare
   `add_file -type verilog top.v` of §3 resolves inside `run/` and is not
   found. The driver emits `../top.v`.
3. `INS_LOC` takes the **flat** instance name `dut_dff`. The blueprint's
   `INS_LOC "top.dut_dff"` raises `CT1135 Can't find object named
   'top.dut_dff'`.
4. `DRIVE` is legal only on an **output** port. Any `DRIVE` on an input raises
   `CT1108 Illegal port attribute value specified 'DRIVE = 8'` — including
   `DRIVE=NONE`.

## Non-determinism

The vendor `.fs`/`.tr`/`.sdf`/`.vo` differ in sha256 between two runs of the
identical inputs (sizes identical). Same class of finding as the chipdb
non-determinism recorded under `evidence/chipdb/`; not investigated here.

## Smoke design of record

`$DATASTORE/oracle-smoke/{top.v,top.cst,top.sdc}` is `gen.py` output from
`shapes/smoke.py` (`P0.T20`); `run.tcl` and the logs are `P0.T19`'s. Pins are
ordinary I/O with no CFG function: `clk AA9`, `rst_n AA10`, `din AA11`
(bank 5), `dout P20` (bank 4). The three inputs carry no `DRIVE`.
