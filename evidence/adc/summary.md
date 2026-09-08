# The on-die ADC of the GW5AST-138C (`P3.T28`, `P3.T29`)

## Verdict: **the vendor accepts both ADCs; the open flow refuses by name.**

`refused:Unable to place cell 'dut', no BELs remaining to implement cell type 'ADCLRC'`

Four vendor runs, all `gw_sh` exit 0 with **zero** errors and a full `run.fs`:

| run | primitive | sweep | vendor | resource report |
|---|---|---|---|---|
| `p3-adc-adc_osc-0000` | `ADCLRC` | `VSENCTL=1` (on-die thermometer) | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0001` | `ADCLRC` | `VSENCTL=2` (`vdd09_0`) | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0002` | `ADCLRC` | `DIV_CTL=2` | accepted | `ADCLRC 1/1 100%` |
| `p3-adc-adc_osc-0003` | `ADCULC` | `VSENCTL=1` | accepted | `ADCULC 1/1 100%` |

So the die has **two** ADC blocks, one of each kind, one site each — not the
25A's single `ADC`. The primitives are `ADCLRC` and `ADCULC`
(`$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:17539`, `:17592`; the vendor's own
comment on the second reads `//ADCULC,GW5AT-138K`). The vendor also brings out
dedicated analog pads for them, which the pin report names:
`N9/ADCTN`, `N10/ADCTP`, `M9/ADCVN`, `L10/ADCVP`, plus `ADCINCK0` on `B1`
(`IOL2[A]`) and `ADCINCK1` on `G17` (`IOR107[A]`).

## Where the blocks are — MEASURED, at zero extra vendor runs

The four bitstreams differ only in the ADC's own parameters, so a pairwise
diff localises the block without a control run:

| pair | what changed | tiles that move |
|---|---|---|
| `0000` vs `0001` | `VSENCTL` 1 → 2 | `(108,180)` 8 bits, `(108,167)` 4 bits |
| `0000` vs `0002` | `DIV_CTL` 0 → 2 | `(108,181)` 4 bits |
| `0000` vs `0003` | `ADCLRC` → `ADCULC` | 304 tiles, largest `(108,179)`, `(1,1)`, `(108,180)` |

`ADCLRC`'s configuration is in the **lower-right** corner, tiles `(108,180)`
and `(108,181)` — `dev.rows-1 = 108`, `dev.cols-1 = 181` — and `ADCULC`'s in
the **upper-left**, around `(1,1)`. The two names are literal.

## Why `P3.T28` did not create the bels

`fse_create_adc` builds its portmap from `dat.gw5aStuff['Adc25kIns'/'Adc25kOuts']`,
which are 25A tables. The 138C's own tables are `AdcLRCIns` (0x28 records),
`AdcLRCOuts` (0x12), `AdcULCOuts` (0x12) and the two `Cfgvsenctl` tables —
`P2.T08a` unlocked them, but **at their declared bases they read zeros and
ASCII bytes**, i.e. the base has drifted between IDE releases exactly as
`Ae350SocIns`' and `CibFabricNode`'s did. A bel whose portmap comes from a
mis-based table is worse than no bel: `nextpnr` binds it and then fails in the
router on a wire that was never the port's (`D30`). So the bels are **not**
created, both open tools refuse by name, and what this task hands the
follow-up is the anchor work already done:

* the record *shapes* are confirmed by the primitive's own port count —
  `ADCLRC` has 37 input ports (8 analog `ADCINBK*` + `VSENCTL[2:0]` +
  `FSCAL_VALUE[9:0]` + `OFFSET_VALUE[11:0]` + `ADCEN`/`CLK`/`DRSTN`/`ADCREQI`)
  against 0x28 = 40 slots, and 15 output ports (`ADCRDY` + `ADCVALUE[13:0]`)
  against 0x12 = 18 slots. Three trailing pad slots in each case;
* filtered by the corners measured above, the `.dat` yields a **small** set of
  surviving bases rather than the hundreds a plain plausibility filter leaves.
  The strongest single candidate for `AdcLRCOuts` is byte `0xa2044`
  (`0x135cc` words from the RS table anchor, against the declared `0x13078`):
  15 live records then 3 absent, walking `(109,168,37..45)`, `(109,167,36..40)`,
  `(109,169,40)` — one column band at a time — and its columns 167/168 are
  **the same tiles the `VSENCTL` bitstream diff moves**, which is an
  independent confirmation the plausibility filter could not give;
* the strongest candidate for `AdcLRCIns` is byte `0xa1bca`: exactly 37 live
  records then 3 absent, all in the block's own columns 180/181;
* `AdcULCOuts` is **not** at the same drift as `AdcLRCOuts`, which is the fact
  that stops this being finished here: two structurally clean candidates
  survive for it (`0x80e24` and `0xa194e`) and nothing measured yet separates
  them. Separating them needs one `ADCULC` bitstream diff against an
  `ADCULC`-free control — one vendor run, outside this task's four.

Until that run, the ADC row is `refused` with the open flow's exact words.

## Shape caveat

`adc_osc.py` XOR-reduces `ADCVALUE[13:10]` onto one ball, because bank 5 brings
out eleven free balls and not fifteen, and it claims **no analog ball at all** —
the sweep uses the internal sources `VSENCTL` selects, so the board's IO
envelope is untouched. The row is an adjudication and a localisation, not an
`E1` identity claim.
