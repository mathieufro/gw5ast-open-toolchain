# `AE350_SOC` fabric wire map — GW5AST-138C

`P2.T26` re-scope, measurement half. Companion data file:
`wire-map-138c.json` (the file `fse_create_ae350()` reads).
Status **PARTIAL / MEASURED**, runs `p2t26-tilewires` and `p2t26-baseline`,
Gowin IDE Standard 1.9.12.03.

## 1. The premise the blueprint was built on is dead

`P2.T06` costed `EC5` discovery at **149 vendor runs** — one presence diff per
bus — against a cap of 8. That costing assumed one bus can be varied at a time.
It cannot be the only shape, and it does not have to be: **run
`p2t26-tilewires` instantiates `AE350_SOC` with all 149 ports (911 bits)
simultaneously bound to distinct fabric flops, and the vendor synthesises,
places, routes and generates a bitstream for it.**

- `run.rpt.txt` §3: `AE350_SOC | 1/1 | 100%`.
- Every port is a real timing endpoint in `run.tr` §3.1.1 (`drv_401_s0/Q ->
  u_ae350/PGEN_CHAIN_I`, `u_ae350/TDO_OUT -> cap_375_s0/D`, …), so nothing was
  optimised away.
- Total place-and-route: **15 s**. The per-run cost placeholder of 35 min is
  wrong for this shape by two orders of magnitude.
- **No physical constraints file was used** (`<Physical Constraints File>: ---`)
  and the block still placed: `AE350_SOC` has a **single fixed site**. That
  matches the reference design, whose `.cst` constrains the two PLLs and never
  the SoC (`research/ae350-dossier.md` §2).

## 2. Where the block is — measured, not inferred

`p2t26-baseline` is the identical fabric with the `AE350_SOC` instance removed.
Presence diff of the two bitstreams (`bslib.read_bitstream` +
`chipdb.tile_bitmap`, the maintainer's method at `chipdb.py:1509-1515`):

| quantity | value |
|---|---|
| tiles differing | 1 477 |
| bits moved | 85 411 |
| bits moved in **columns 145-181** | **85 401 (99.99 %)** |
| bits moved anywhere else | **10**, at `(r, 95)` and `(r, 96)` — the clock spine |
| row span | 0-108 (the full die height) |
| peak column | **159** |

So the `AE350_SOC`'s entire fabric footprint on this die is the **right-hand
column band 145-181**. Nothing about the block touches the left two thirds.

Inside that band the chipdb holds two hard-block interface tile types that
exist nowhere else on the die:

| ttyp | rows | cols | tiles | touched by the diff | moved bits |
|---|---|---|---|---|---|
| **224** | 10, 28, 46 | 145-180 | 108 | 72 | 2 464 |
| **228** | 64, 82, 100 | 145-180 | 108 | 23 | 119 |

216 interface tiles against 911 port bits is ~4.2 bits per tile — the right
order for a hard macro's fabric tap rows. Which band carries inputs and which
outputs is not yet separated.

## 3. The `.dat` does carry the port map — under a different name

`P2.T03`/`P2.T04` measured `McuIns`/`McuOuts` as 637 all-sentinel slots and
concluded the 138C `.dat` has no AE350 port map. The first half is right and
the conclusion is wrong: the legacy triple block is dead on GW5, and GW5
devices carry their hard-block port maps in **`dat.gw5aStuff`** instead
(`chipdb.py:2489` reads the ADC's ports from `gw5aStuff['Adc25kIns']`, not from
`compat_dict`). `gw5aStuff` has 120 keys on this device, and two of them are:

```
dat_parser.py:545  ret["Ae350SocIns"]  = self.read_scaledGrid16(0x1b1, 3, 3, RSTable5ATOffset + 0x86a0, 6)
dat_parser.py:546  ret["Ae350SocOuts"] = self.read_scaledGrid16(0x206, 3, 3, RSTable5ATOffset + 0x8bb0, 10)
```

`0x1b1` = **433** slots and `0x206` = **518** slots, against **416** input bits
and **495** output bits — the table lengths bracket the port bit counts.

**They decode to garbage today, and that is a parser defect, not empty data.**
The signature is

```
def read_scaledGrid16(self, numRows, numCols, rowScaling, colScaling, baseOffset)
```

so the call above puts the base offset into `colScaling` and the row stride into
`baseOffset`; `self._cur` is then `row*3 + col*(rs+0x86a0)*2 + 6`, which reads
unrelated bytes. The working entries in the same file use the other order —
`read_scaledGrid16(216, 3, 6, 1, RSTable5ATOffset + 0x1f38)` for `PllLTIns`,
`read_scaledGrid16i(25, 3, 6, 1, …)` for `Adc25kIns`. Read contiguously as
triples at `RSTable5ATOffset + 0x8bb0` (absolute `0x8405c`, with
`_rs_table_offset` = `0x7b4ac` on this file), the `Outs` base lands **inside a
255-triple run that is coherent under the `(row, col, wire)` convention** and
whose wire field indexes real 138C wire names (`A0`-`D7`, `E210`-`W220`,
`OF3`/`OF4`, `CLK1`). Empty tables do not do that.

The same transposition affects **every** entry at `dat_parser.py:525-546` and
`:601-650` — `MipiIns1/2`, `MipiOuts1/2`, `MipiDPhy*`, `Gtrl12*`, `MDdrDll*`,
`S0DdrDll*`, `S1DdrDll*`, `Cmsera*`, `AdcLRC*`, `AdcULC*`. Every one of those
blocks is silently reading noise on this device.

`dat_parser.py` is **frozen for Phase 2** (Phase 0 and Phase 6 own it), so this
is recorded here and fixed in its owning task under the standing order, not
patched from this phase. It is the single highest-value fix in the phase: it
converts a 149-run discovery campaign into a table read.

## 4. What is resolved and what is not

**Resolved (2 vendor runs):**
- the block instantiates, places and routes with all 911 bits connected;
- its fabric footprint is columns 145-181, 99.99 % of moved bits;
- the 216 candidate interface tiles (ttyp 224 and 228) and their coordinates;
- a single fixed site, no `INS_LOC`;
- the real home of the port map in the shipped data, and the exact defect that
  hides it.

**Unresolved — 911/911 port bits still lack a named wire:**
1. **per-bit binding.** A presence diff localises a block; it does not name a
   wire per port bit. That needs either the `.dat` table (0 runs, after the
   parser fix) or a differential campaign with pinned endpoints.
2. **the `Ae350SocIns` base.** The `Ins` delta `0x86a0` reads all-sentinel at
   every phase tried; `Outs` at `0x8bb0` reads live. One of the two deltas has
   drifted between IDE releases, exactly as `CIB_FABRIC_NODE_DELTAS`
   (`dat_parser.py`) documents for `CibFabricNode`. The fix is the same
   data-driven candidate list.
3. **band polarity.** Which of ttyp 224 / ttyp 228 is the input side.

WIRE-MAP-VERDICT: 0/911 port bits bound; footprint cols 145-181 MEASURED over 2 runs; port map located in dat.gw5aStuff['Ae350SocIns'/'Ae350SocOuts'], blocked on a frozen-file parser defect.
