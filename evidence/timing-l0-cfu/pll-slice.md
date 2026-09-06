# L0 PLL slice — `check_timing_l0.py --classes pll` (`P1.T33`, `V12a`, `D60`)

`D60` gives Phase 1 the PLL arcs of the L0 band. The measurement below is that
the slice is **empty by design on both sides**, and the band asserts exactly
that rather than skipping it.

NO-DATA: the GW5AST-138C .tm publishes no PLL timing group. Only chunks 0, 1 and 2 are parsed at all -- each is 15552 bytes and `tm_parser.py:344` breaks on `if i >= 3 and device in {...'GW5AST-138C'}` -- and at offset 0x7cc each carries an 80-byte, five-path block byte-identical to `GW2A-18.tm`'s, naming five rPLL outputs (CLKOUT/LOCK/CLKOUTP/CLKOUTD/CLKOUTD3) this die does not have. UG306E Table 5-2 gives the Arora-V PLL CLKOUT0..6/CLKFBOUT/LOCK, DS1239E Table 3-18 publishes no CLKIN->CLKOUT delay, and the vendor SDF emits all seven CLKIN->CLKOUTn IOPATHs as 0.000 -- so the PLL slice of the L0 band is "no arcs by design", asserted as 7/7 rather than skipped.

## 1. What the `.tm` actually holds at the PLL offset

`offsets[0x7cc] = parse_pll`, and the next registered offset is `0x81c`
(`parse_dll`), so the block is `0x50` = **80 bytes** = five `float_data` paths
of four corners each. On `GW5AST-138C.tm` chunk 0 (ns):

```
0.198   0.1935  0.208   0.2015
0.1785  0.1805  0.216   0.2275
0.1705  0.181   0.226   0.2215
0.169   0.1635  0.2025  0.206
0.183   0.1765  0.206   0.221
```

Chunk 1 is identical to chunk 0 here; chunk 2 is the 0.862× derate `P0.T36`
already measured (0.1707 … 0.1905).

**These bytes are not GW5A data.** Chunk 0 of `GW5AST-138C.tm` is byte-identical
to chunk 0 of `GW2A-18.tm` in **15,471 of its 15,552 bytes** — every registered
block matches except `iodelay` (0x3728) and `fanout` (0x381c). The PLL block is
one of the identical ones. Against GW1N (`GW1NR-9C`, `GW1NZ-1`) the same block
has the same five-path shape with different values (0.51–0.73 ns), i.e. it is a
GW1N/GW2A **rPLL** table carried forward into the GW5A preamble.

Five paths is the rPLL output count — `CLKOUT`, `LOCK`, `CLKOUTP`, `CLKOUTD`,
`CLKOUTD3`, the set nextpnr still hard-codes at
`himbaechel/uarch/gowin/gowin_arch_gen.py:1766`. This die's PLL has none of
those ports: UG306E (Arora V Clock User Guide, `vendor/gowin/ip/ddr3/UG306E.txt`
Table 5-2) gives the `PLL` primitive `CLKOUT0..CLKOUT6`, `CLKFBOUT` and `LOCK`.
Seven clock outputs, not five. There is no mapping from the block to this die's
ports that is anything but invention, so `parse_pll` publishes nothing.

**Confidence.** That the block is 5×4 floats at 0x7cc and byte-identical to
GW2A-18: **certain** (bytes, reproduced by `tests/test_timing_pll.py`). That it
is the rPLL CLKIN→output table in the GW1N/GW2A order: **high but unverified** —
the shape and the magnitudes fit and nothing else in either primitive has five
paths, but no vendor document names it. That it is *inapplicable to this die*:
**certain**, on the port count alone and on §3 below.

## 2. What the datasheet publishes for the PLL

DS1239E Table 3-18 (`vendor/gowin/tang-mega/DS1239E.txt:2178-2240`) publishes
`FINMIN/FINMAX` 19/800 MHz, `FPFD` 19/81.25 MHz, `FVCO` 650/1300 MHz,
`FOUT` 5.079/1000 MHz, `TLOCKMAX` 15 ms, `TSTATPHAOFFSET` ±50 ps, cycle-to-cycle
and period jitter in ps/mUI, `RSTMINPULSE` 10 ns — and **no CLKIN→CLKOUT delay
or skew at all**, in either speed-grade column. So there is no datasheet value
the 0.16–0.23 ns block could be matched against; the only ~0.2 ns numbers in the
sheet are `tCO_CFU` 0.200/0.230, `tCOOR_BSRAM` 0.23 and `tCOIR_DSP` 0.2 — all
CFU/BSRAM/DSP, all already parsed by other `parse_*` functions.

## 3. The vendor `.sdf`: the PLL is a zero-delay hard macro

Vendor SDF from a real 138C PLL design (the `P1.T21/T22` PLL attrmap sweep,
shape `clocking_pll_attrmap`, IDE 1.9.12.03 Standard, `-device_version C`):

```
  (CELL
   (CELLTYPE "PLL")
   (INSTANCE dut_pll)
    (DELAY
     (ABSOLUTE
      (IOPATH CLKIN CLKOUT0 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT1 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT2 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT3 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT4 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT5 (0.000:0.000:0.000))
      (IOPATH CLKIN CLKOUT6 (0.000:0.000:0.000))
     )
```

Seven arcs, every field of every triple `0.000`. Checked on runs `-0000`,
`-0005` and `-0011` of the sweep (different PLL parameter points): identical.
The vendor's own static timing models this PLL as **zero internal delay** —
what it constrains is frequency, jitter and lock time, none of which is an
`IOPATH`. **The PLL slice of L0 therefore has no arcs by design.**

## 4. Implementation

`apycula/tm_parser.py` — `parse_pll` is no longer a bare `pass`. It returns an
empty mapping with the reasoning recorded above it, and the decoder is kept as
`pll_block(data)` so the claim stays checkable against the shipped file. No
speed grade gains a `pll` group, so **no chipdb byte changes**: `read_tm`'s
output is `repr`-identical before and after for `GW1N-9C`, `GW2A-18C`,
`GW5A-25A`, `GW5AT-60B` and `GW5AST-138C`, and `GW5A-25A.msgpack.xz` stays
`6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca`.

`tools/check_timing_l0.py` — `pll` moves out of the skip line into
`LIVE_CLASSES` as a zero-arc class with its own band policy: the SDF is filtered
to PLL cell types, and an arc nextpnr does not install is compared against a
model delay of `0.0`. So a vendor release that starts publishing a non-zero PLL
delay fails this check loudly instead of passing as "skipped". No `nextpnr`
change: there is no arc to emit.

## 5. `V12a` — band mode, verbatim

```
$ python $OTC/tools/check_timing_l0.py --classes pll \
    --sdf $DATASTORE/clocking/pll/attrmap/p1-pll-attrmap-clocking_pll_attrmap-0000/run/impl/pnr/run.sdf \
    --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz
L0 ok: 7/7 arcs within ±10%, 0 exceptions listed
(VOLTAGE 0.93:0.90:0.87) (PROCESS "best=0.65: nom=1.0: worst=1.8") (TEMPERATURE 85:25:0)
grade: C1/I0 -- derived (1.25 x C2/I1, P0.T35 -- NOT measured)
pll: 0 chipdb arcs and 0 nextpnr arcs BY DESIGN (P1.T33) -- the .tm block at offset 0x7cc is 80 bytes of inherited GW2A rPLL data (byte-identical to GW2A-18.tm) naming five rPLL outputs this die does not have; UG306E Table 5-2 gives the Arora-V PLL CLKOUT0..6/CLKFBOUT/LOCK, and the vendor SDF emits every CLKIN->CLKOUTn IOPATH as 0.000. DS1239E Table 3-18 publishes no CLKIN->CLKOUT delay at all.
```
exit 0. 7/7, 0 exceptions, 0 unmapped.

## 6. Inventory mode, verbatim

```
$ python $OTC/tools/check_timing_l0.py --classes pll \
    --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz
L0 inventory: chipdb GW5AST-138C.msgpack.xz
grades: C1/I0 = derived (1.25 x C2/I1, P0.T35 -- NOT measured); C2/I1 = measured (.tm chunk 0); unidentified_1 = unidentified (.tm chunk, P0.T36 -- not a graded table); unidentified_2 = unidentified (.tm chunk, P0.T36 -- not a graded table)

class group    grade            arcs      min   median      max   (ns)
pll   pll: 0 chipdb arcs and 0 nextpnr arcs BY DESIGN (P1.T33) -- the .tm block at offset 0x7cc is 80 bytes of inherited GW2A rPLL data (byte-identical to GW2A-18.tm) naming five rPLL outputs this die does not have; UG306E Table 5-2 gives the Arora-V PLL CLKOUT0..6/CLKFBOUT/LOCK, and the vendor SDF emits every CLKIN->CLKOUTn IOPATH as 0.000. DS1239E Table 3-18 publishes no CLKIN->CLKOUT delay at all.
pll   pll      -                   0   absent (supporting group)

ratio C1/I0 : C2/I1 -- no comparable arcs (both grades needed)

nextpnr emission (gowin_arch_gen.py create_timing_info): 2192 cell arcs, 144 pip classes, 10 groups handled
chipdb groups nextpnr never emits: none
unconsumed chipdb arc keys (38 across 6 groups):
  gap: bram: clk_clk, clk_do, clk_reset_hold_syn, clk_reset_set_syn, clka_doa, clka_reseta_hold_syn, clka_reseta_set_syn, clkb_do, clkb_dob, clkb_oce_hold, clkb_oce_set, clkb_resetb_hold_syn, clkb_resetb_set_syn
  gap: dff: clk_clk, lsr_lsr
  gap: fanout: SX1Fan, SX1FanNum, X1Fan, X1FanNum
  gap: glbsrc: BRANCH_SCLK, CENT_SPINE_SCLK, CIB_CENT_PCLK, CIB_CENT_SCLK, CIB_PIC_INSIDE, GSRREC_HLD, GSRREC_SET, GSR_MPW, PIO_CENT_PCLK, PIO_CENT_SCLK, SPINE_TAP_SCLK_0, SPINE_TAP_SCLK_1, TAP_BRANCH_SCLK
  gap: lut: a_ofx, b_ofx, c_ofx, d_ofx
  gap: wire: ISB, X0ME

L0 INVENTORY ok: 0/0 required groups populated, 4 grades, ratio band ok
```
exit 0.

## 7. Artefact

`sdf` `/Users/alex/fine-line-data/open-toolchain-gw5ast/clocking/pll/attrmap/p1-pll-attrmap-clocking_pll_attrmap-0000/run/impl/pnr/run.sdf`
sha256 `5fe75e8836581c79dee6f7ab122f67aaa5a5e0a9fe26f6c177d05c28d8f25378`, 12,089 B —
the `P1.T22` vendor run, not re-run (a fresh oracle run would produce the same
seven zero arcs; runs `-0005`/`-0011` already confirm the invariance).
Condition line `(VOLTAGE 0.93:0.90:0.87) (PROCESS "best=0.65: nom=1.0: worst=1.8") (TEMPERATURE 85:25:0)` (`D49f`).

## 8. Cross-phase finding (NOT fixed here — `P0.T35`/`P0.T36` / Phase 6 own it)

Chunk 0 of `GW5AST-138C.tm` is byte-identical to chunk 0 of `GW2A-18.tm` in
15,471/15,552 bytes, `lut`/`alu`/`dff`/`bram`/`dsp`/`io`/`wire`/`glbsrc`/`hclk`
blocks included. `P0.T36` established that chunks 0-2 are a family-generic
preamble across 22 GW5\* devices; this measurement widens that: the preamble is
not even GW5-generic, it is inherited from GW2A. That is a live input to the
`P0.T37` conflict (`chunk 0 fits C1/I0 for LUT/BSRAM but not DFF CLK→Q`, `D91`)
and to `S17b`. Recorded, not acted on, per this task's scope.
