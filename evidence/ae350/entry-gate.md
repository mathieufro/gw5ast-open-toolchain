# P2.T01 — Phase-2 entry gate

Read-only on code. Every line below is a command that was run and the output it
printed; nothing here was repaired, and a `FAIL` would have stopped the phase
rather than been patched from Phase 2.

```
PRECOND 1 ok
PRECOND 2 ok
PRECOND 3 ok
PRECOND 4 ok
PRECOND 5 ok
PRECOND 6 ok
PRECOND 7 ok
```

## Provenance block

```
ide_version: Gowin EDA Standard 1.9.12.03 (/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA)
yosys_version: Yosys 0.63 (git sha1 70a11c6bf0e8dd669f56c7da3587f78b405138e2)
apicula_sha: d05f984dd2d2369c26d2c85e9175bbbe6b2faf39
nextpnr_sha: 0882cd4cd0e1945f62bbbe75640501f0867d73e2
chipdb_sha256: 100ffd8e9d3901da3701849788c96cb4f027639b5e6f93c3c7e4c55d1ed69dc5
mask_sha256: 59147bfc633e10c5c1f4875bef6cf0cf9b76f8d58868ffc084f8c252557a1ec0
```

`GOWINHOME` is the `PL-P0-4` selection file `evidence/_runs/gowinhome.selected`
(Standard, licensed) — `edu-provisional` is **not** set on this phase.

---

## 1. Chipdb builds and is byte-reproducible (`F1`-`F5`)

```
$ PYTHONPATH=$APICULA python -m apycula.chipdb_builder GW5AST-138C
CHIPDB_EXIT=0            (11.8 s user, log: evidence/_runs/p2t01-chipdb.log)
$ shasum -a 256 apycula/GW5AST-138C.msgpack.xz
100ffd8e9d3901da3701849788c96cb4f027639b5e6f93c3c7e4c55d1ed69dc5
```

The file already present at `epic/gw5ast138c` carried that same digest before
the rebuild, so the build is reproducible, and it is the msgpack half of the
Phase-1 installed pair (`.bin 43bea88d`, binary `f029437e`).

## 2. Twelve PLL bels (Phase 1's `S7`)

```
PLL_BELS 12
PLL_LOCS [(27,1) (27,177) (45,0) (45,178) (63,0) (63,178) (81,1) (81,177)
          (108,28) (108,32) (108,146) (108,150)]
```

Counted as `extra_func[(row, col)]['pll']` entries in the built chipdb — the
structure `gowin_arch_gen.py:1100-1107` turns into a bel, i.e. the same twelve
nextpnr reported as `PLLA: 0/12` in `evidence/plla/openflow-gap-138c.md`.
`PLL_R[0]` therefore exists as a bel, which is what the AE350 core clock needs.

## 3. No `KeyError` path left for the 138C (`F23`)

```
chipdb._gw5a_hclk_locs['GW5AST-138C']  -> present (True)
chipdb.gw5_ihclk_wire_num('GW5AST-138C') -> 38
```

Both are lookups that raised before Phase 1; neither raises now.

## 4. `gw_sh` runs and is licensed (`D52`, `F64`)

```
$ $GOWINHOME/IDE/bin/gw_sh hello.tcl        # puts hello ; exit
*** GOWIN Tcl Command Line Console  ***
hello
exit=0
```

No `License verification failed` line. The three OpenGL/Chromium warnings the
console prints are unrelated to the licence and appear on every headless run.
Because the smoke passes, `GOWINHOME` stays on Standard 1.9.12.03 and no row of
this phase is stamped `edu-provisional: true`.

## 5. `case insloc:` present in nextpnr (`P0.T38`)

```
$ grep -n "case insloc:" himbaechel/uarch/gowin/cst.cc
331:                case insloc: { // INS_LOC name RrCc[cls][A|B]
```

`grep -rn INS_LOC himbaechel/` shows **three** reader regexes, not the two the
blueprint quoted: `inslocre` (`cst.cc:146`), `hclkre` (`:148`) and
`inslocmacrore` (`:155`). The third is `P0.T38`'s placement-macro spelling
(`INS_LOC "u_Gowin_PLL_AE350/PLL_inst" PLL_R[0];`), matched last so it cannot
steal the other two. A superset of the expected readers, and the one this phase
depends on for `PLL_R[0]` — recorded, not a failure.

## 6. Harness self-tests (`S5`, `S6b`)

Design under test `$DATASTORE/oracle-smoke` (the `P0.T29` smoke design; the
selftest CLI takes `--design-dir` and never infers it from cwd).

```
$ python -m fuzz.gw5ast138c.harness.selftest --design-dir $D --inject-one-fuse
SELFTEST ok: 1 difference reported, 0 spurious            rc=0
$ python -m fuzz.gw5ast138c.harness.selftest --design-dir $D --unpacker-completeness
COMPLETENESS ok: 0 unattributed tiles, 0 missing cells     rc=0
```

## 7. The `E1` `INS_LOC` exporter exists and round-trips (`P0.T26`)

`fuzz.gw5ast138c.harness.equiv.export_insloc` (`equiv.py:2381`) is the only
exporter in the project; nextpnr has none. Called on a one-LUT placement
(`LUT4` on `X2Y1/LUT0`):

```
EXPORTED count=1
LINE INS_LOC "dut_lut" R2C3[0][A];
MATCH cell=dut_lut R=2 C=3 cls=0 half=A     (against cst.cc:146 inslocre)
ROUNDTRIP ok x=2 y=1                        (cst.cc's x=C-1, y=R-1)
```

The emitted line matches the reader regex and decodes back to the site it was
exported from, so `E1` rows in this phase have a working export path.
