# L0 CFU arc inventory — `check_timing_l0.py --classes cfu` (`P0.T32`, `V12a`, `D60`)

First cut of `DEL-e`'s L0 checker, chipdb side. The band measurement against a vendor
`.sdf` (`--sdf`, the `V12a` stdout contract) is `P0.T37`; no vendor SDF exists on this
box yet, so what is recorded here is the **inventory mode** run.

- tool: `/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84/open-toolchain/tools/check_timing_l0.py` (tests: `tools/tests/test_check_timing_l0.py`, 11 pass)
- chipdb: `apicula/apycula/GW5AST-138C.msgpack.xz`, sha256 `fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb`
  (apicula `143d156`, branch `epic/gw5ast138c`)
- arc source of truth: `nextpnr/himbaechel/uarch/gowin/gowin_arch_gen.py:create_timing_info`
  (`e8440c71`), executed against a recording chipdb — the emitted-arc and gap numbers below
  are measured by running the real emitter, not read off a hand-written list.
- python: `/Users/alex/fine-line/vendor/venv/bin/python`
- date: 2026-09-04

## Verdict

`L0 INVENTORY ok` — all **8** required `D60` CFU groups populated
(lut, alu, dff, sram/SSRAM, bram/BSRAM, wire, glbsrc, hclk; `fanout` is a supporting
group consumed by the `wire` block), **4** grades, C1/I0 : C2/I1 ratio exactly 1.25 on
all 153 comparable arcs. **C1/I0 is `derived`, not `measured`** (`P0.T35`,
`apicula/doc/timing-c1i0.md`); the tool prints that provenance on every run and the
1.25 band is a derivation regression check, not silicon.

## Gaps — chipdb arc keys `create_timing_info` never consumes

Group level: **none** — every one of the 10 chipdb timing groups has an emitter branch.
Key level: **38 keys across 6 groups** are present in the chipdb and never installed
into nextpnr (see the literal output). Notable ones for later phases:
`lut: a_ofx..d_ofx` (the LUT->OFX path), `dff: clk_clk` and `bram/glbsrc` clock-period
and SCLK entries, `glbsrc: GSR*`, `wire: ISB, X0ME` (installed with a zero
`TimingValue()` instead of the chipdb value). These are Phase 6 (`S17b`/`S18`) inputs,
not Phase 0 failures.

## Literal output

```
$ python tools/check_timing_l0.py --classes cfu --chipdb apicula/apycula/GW5AST-138C.msgpack.xz
L0 inventory: chipdb GW5AST-138C.msgpack.xz
grades: C1/I0 = derived (1.25 x C2/I1, P0.T35 -- NOT measured); C2/I1 = measured (.tm chunk 0); unidentified_1 = unidentified (.tm chunk, P0.T36 -- not a graded table); unidentified_2 = unidentified (.tm chunk, P0.T36 -- not a graded table)

class group    grade            arcs      min   median      max   (ns)
cfu   lut      C1/I0              11    0.131    0.592    0.844
cfu   lut      C2/I1              11    0.105    0.474    0.675
cfu   lut      unidentified_1     11    0.076    0.347    0.516
cfu   lut      unidentified_2     11    0.091    0.409    0.582
cfu   alu      C1/I0               8    0.044    0.637    0.712
cfu   alu      C2/I1               8    0.035    0.510    0.570
cfu   alu      unidentified_1      8    0.024    0.351    0.440
cfu   alu      unidentified_2      8    0.030    0.439    0.491
cfu   dff      C1/I0              21    0.014    0.044    3.750
cfu   dff      C2/I1              21    0.011    0.035    3.000
cfu   dff      unidentified_1     21    0.011    0.035    3.000
cfu   dff      unidentified_2     21    0.009    0.030    2.586
cfu   sram     C1/I0              17    0.015    0.043    0.712
cfu   sram     C2/I1              17    0.012    0.035    0.570
cfu   sram     unidentified_1     17    0.012    0.035    0.440
cfu   sram     unidentified_2     17    0.010    0.030    0.491
cfu   bram     C1/I0              61    0.015    0.043    2.825
cfu   bram     C2/I1              61    0.012    0.035    2.260
cfu   bram     unidentified_1     61    0.012    0.035    2.260
cfu   bram     unidentified_2     61    0.010    0.030    1.948
cfu   wire     C1/I0               8    0.000    0.194    0.333
cfu   wire     C2/I1               8    0.000    0.155    0.266
cfu   wire     unidentified_1      8    0.000    0.146    0.214
cfu   wire     unidentified_2      8    0.000    0.134    0.229
cfu   glbsrc   C1/I0              17    0.044    0.175    3.638
cfu   glbsrc   C2/I1              17    0.035    0.140    2.910
cfu   glbsrc   unidentified_1     17    0.035    0.140    2.910
cfu   glbsrc   unidentified_2     17    0.030    0.121    2.509
cfu   hclk     C1/I0               4    0.014    0.073    0.326
cfu   hclk     C2/I1               4    0.011    0.058    0.261
cfu   hclk     unidentified_1      4    0.011    0.058    0.261
cfu   hclk     unidentified_2      4    0.009    0.050    0.225
cfu   fanout   C1/I0               8    0.089    0.232    0.611
cfu   fanout   C2/I1               8    0.071    0.186    0.489
cfu   fanout   unidentified_1      8    0.071    0.186    0.489
cfu   fanout   unidentified_2      8    0.061    0.103    0.218

ratio C1/I0 : C2/I1: n=153 min=1.250 median=1.250 max=1.250 band=[1.2375,1.2625] expect=1.25 status: ok -- DERIVED, not measured (P0.T35, apicula/doc/timing-c1i0.md)

nextpnr emission (gowin_arch_gen.py create_timing_info): 2192 cell arcs, 144 pip classes, 10 groups handled
chipdb groups nextpnr never emits: none
unconsumed chipdb arc keys (38 across 6 groups):
  gap: bram: clk_clk, clk_do, clk_reset_hold_syn, clk_reset_set_syn, clka_doa, clka_reseta_hold_syn, clka_reseta_set_syn, clkb_do, clkb_dob, clkb_oce_hold, clkb_oce_set, clkb_resetb_hold_syn, clkb_resetb_set_syn
  gap: dff: clk_clk, lsr_lsr
  gap: fanout: SX1Fan, SX1FanNum, X1Fan, X1FanNum
  gap: glbsrc: BRANCH_SCLK, CENT_SPINE_SCLK, CIB_CENT_PCLK, CIB_CENT_SCLK, CIB_PIC_INSIDE, GSRREC_HLD, GSRREC_SET, GSR_MPW, PIO_CENT_PCLK, PIO_CENT_SCLK, SPINE_TAP_SCLK_0, SPINE_TAP_SCLK_1, TAP_BRANCH_SCLK
  gap: lut: a_ofx, b_ofx, c_ofx, d_ofx
  gap: wire: ISB, X0ME

L0 INVENTORY ok: 8/8 required groups populated, 4 grades, ratio band ok
exit 0
```
