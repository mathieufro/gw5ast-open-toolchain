# `GW5AST-138C.tm` — chunks 0, 1 and 2 dumped and identified (`P0.T36`, `D49b`)

First `W-TIMING` measurement. Source file
`$GOWINHOME/IDE/share/device/GW5AST-138C/GW5AST-138C.tm`
(Gowin EDA Standard 1.9.12.03, `/Applications/GowinIDE.app/...`),
3,139,786 B = **201** whole 15,552-B chunks + a 13,834-B tail, no header, no index.
Parsed with `apycula.tm_parser.parse_chunk` at commit `b198967` (branch
`epic/gw5ast138c`). Datasheet of record: **DS1239E** (`DS1239-1.0.3E`), Table 3-13
(CFU) — the **only** speed grades it publishes for GW5AST-138 are **C2/I1** (fastest)
and **C1/I0** (slowest, §4.1 Figure 4-2). There is no `A0`, no `ES` and no `A`-grade
column anywhere in DS1239E; the sibling sheets DS981E (GW5AT) Table 3-34 and DS1105E
(GW5AS) Table 3-21 publish the *same two columns with byte-identical numbers*.

## 1. Identification table

| chunk | declared length | md5 (12) | identification | matches DS1239E to 3 dp? | confidence |
|---|---|---|---|---|---|
| 0 | 15,552 (= `chunklen`) | `02634de18c33` | **C2/I1** (DS1239E Table 3-13, C2/I1 column) | yes — `tSR_CFU` exact, `tCO_CFU` ±0.002 | **high** |
| 1 | 15,552 | `7c6360ec205f` | `unidentified` (`unidentified_1`) | no — no grade column | **high that it is *not* a grade**; positive id low |
| 2 | 15,552 | `6d5f7bce7f74` | `unidentified` (`unidentified_2`) | no — no grade column | **high that it is *not* a grade**; positive id low |

No chunk is `C1/I0`. `C1/I0` therefore stays **derived** (`1.25 x` chunk 0,
`tm_parser.C1_I0_FROM_C2_I1`); `P0.T35`'s derivation is confirmed, not replaced.
`tm_parser.py` is unchanged by this task (`P0.T36` "Files it may touch": this file only).

## 2. The measured numbers (ns)

Ranges are min..max over the four corner slots of each path.

| quantity | chunk 0 | chunk 1 | chunk 2 | DS1239E C2/I1 | DS1239E C1/I0 |
|---|---|---|---|---|---|
| `lut.{a,b,c,d}_f` (tLUT4_CFU) | 0.232..0.570 | 0.256..0.440 | 0.200..0.491 | 0.297..0.539 | 0.371..0.674 |
| `dff.lsr_q` (tSR_CFU) | **1.075..1.148** | **1.075..1.148** | 0.927..0.990 | **1.075..1.148** | 1.344..1.435 |
| `dff.clk_qpos` (tCO_CFU) | 0.201..0.232 | 0.201..0.232 | 0.173..0.200 | 0.200..0.230 | 0.250..0.288 |
| `wire.X0` | 0.1070..0.1420 | 0.1180..0.1280 | 0.0922..0.1224 | not published | not published |
| `wire.X2` | 0.1190..0.2370 | 0.1620..0.1880 | 0.1026..0.2043 | not published | not published |
| `wire.X8` | 0.1470..0.2660 | 0.1720..0.2140 | 0.1267..0.2293 | not published | not published |

Per-path 4-tuples for the three arcs the datasheet names:

| path | chunk 0 | chunk 1 | chunk 2 |
|---|---|---|---|
| `lut.a_f` | 0.384 0.344 0.549 0.517 | 0.429 0.397 **0.429 0.397** | 0.331 0.297 0.473 0.446 |
| `dff.lsr_q` | 1.097 1.075 1.148 1.132 | 1.097 1.075 1.148 1.132 | 0.946 0.927 0.990 0.976 |
| `dff.clk_qpos` | 0.202 0.201 0.231 0.232 | 0.202 0.201 0.231 0.232 | 0.174 0.173 0.199 0.200 |

Groups decoded in all three chunks (identical set):
`alu bram dff fanout glbsrc hclk iodelay lut sram wire` — 656 scalars
(648 floats + 8 integer fanout counts). `dl`, `iddroddr`, `pll`, `dll`, `dsp`,
`io`, `iregoreg` are stub parsers upstream and yield nothing.

## 3. Evidence per chunk

### Chunk 0 = C2/I1 — high confidence
- `dff.lsr_q[1] = 1.0750` and `dff.lsr_q[2] = 1.1480` are **exactly** DS1239E
  `tSR_CFU` C2/I1 Min/Max. A scan of all 1,944 float scalars of chunks 0-2 finds
  those two literals **nowhere else** (chunk 1 shares chunk 0's DFF group verbatim;
  chunk 2 has 0.927/0.990).
- `dff.clk_qpos` 0.201..0.232 against a published 0.200..0.230 — agreement to
  0.002 ns (datasheet rounding), two orders of magnitude tighter than the 25 % gap
  to the C1/I0 column (0.250..0.288).
- The discriminator against chunk 1 is the LUT: DS1239E `tLUT4_CFU` C2/I1 Max is
  **0.539**, which chunk 1's LUT4 arcs never reach (their max is 0.440) but chunk 0's
  do bracket (0.549 on `a_f`, 0.570 on `b_f`). Caveat recorded honestly: the exact
  literals 0.297 / 0.539 appear in **no** chunk, so `tLUT4_CFU` is a bracket check,
  not an equality; the identification rests on `tSR_CFU` and `tCO_CFU`.
- Not C1/I0: `1.25 x` chunk 0 `lsr_q` = 1.371 1.344 1.435 1.415, which is the
  published C1/I0 band — i.e. chunk 0 is the C1/I0 *source*, not C1/I0 itself.

### Chunk 1 — not a speed grade; positive identity unknown
- **540 of the 648 float scalars are byte-equal to chunk 0.** The differing 108
  are exactly the combinational/routing groups: `lut` 44/44, `alu` 32/32,
  `sram` 16/68 (the four `rad*_do` read arcs), `wire` 16/32. `dff` 0/84,
  `bram` 0/244, `glbsrc` 0/68, `hclk` 0/16, `iodelay` 0/28, `fanout` 0/32 —
  **identical**. A speed grade or a voltage/temperature corner changes the
  sequential arcs too; this one does not.
- Of the 27 four-tuples it does change, **all 27 collapse**: slot[2] == slot[0] and
  slot[3] == slot[1] (e.g. `lut.a_f` = 0.429 0.397 0.429 0.397), against 50/162
  collapsed tuples in chunks 0 and 2. Chunk 1 carries **no min/max spread** on the
  combinational paths — the signature of a single-corner ("typical") model, not of
  a corner table.
- The LUT mux delay is **redistributed**, not scaled: chunk 0 has
  `lut.m0_ofx0` 0.189/0.269 with `lut.fx_ofx1` 0.060/0.105; chunk 1 has
  `m0_ofx0` 0.076 with `fx_ofx1` 0.213 — the same F-to-OFX1 path split at a
  different internal node. That is a different *model of the same silicon*, which no
  speed grade can be.
- Its values sit **between** chunk 0's slot[0..1] and slot[2..3] (0.429 vs
  0.384/0.549), consistent with a single averaged corner.
- Best hypothesis (**low** confidence, not asserted): a spread-less / alternate-mux
  combinational model used by an early estimator. Label stays `unidentified_1`.

### Chunk 2 — not a speed grade; a uniform derate of chunk 0
- Chunk 2 is **exactly `0.862 x` chunk 0** on **607 of 608** non-zero, non-`fanout`
  float scalars (to 1e-7 relative), with the 8 zero scalars zero in both. The single
  exception is `iodelay.SDTAP_DO[0]` = 0.0125 in all three chunks (a tap constant,
  not a delay). The whole `fanout` group (32 scalars) is **not** scaled and is not a
  simple function of chunk 0.
- A uniformly scaled table is a **derived** table, not an independently characterised
  grade — the same construction `tm_parser` now uses for C1/I0 (`1.25 x`).
- No published grade fits: the only ratios DS1239E admits are 1.00 (C2/I1) and 1.25
  (C1/I0). `0.862 x` C2/I1 is **faster than the fastest grade GW5AST-138 ships**
  (§4.1: "C2/I1 Fastest"), so chunk 2 cannot be C1/I0, and it cannot be a slower
  automotive/ES grade either.
- Two unfalsified hypotheses, both **low** confidence, listed with the experiment
  that would separate them:
  1. **A higher core-voltage corner.** `pn_voltage.csv` gives GW5AST-138C a
     0.9 V / 1.0 V core; the GW1N chunk order in this same parser alternates
     `<grade>` / `<grade>_LV` voltage variants, so a voltage pair is precedent in
     this file format. ~11 % more Vdd giving ~14 % less delay is the right order.
  2. **A typical/best-case process corner** (the vendor STA "fast" corner).
  Discriminator (`S17b`/L1, Phase 6): run vendor STA on this part and compare the
  reported fast-corner arcs, and/or a 1.0 V run, against `0.862 x` chunk 0.
- Label stays `unidentified_2`.

## 4. Chunks 3+ — what they contain

Not chunk-formatted, and **not** all-denormal or constant either:

| | chunks 0-2 | chunks 3..200 (198 chunks) |
|---|---|---|
| floats in a plausible delay range 0..100 | 3,886 / 3,888 (99.9 %) | 30.9 % min, 51.8 % median, 56.7 % max — **none above 90 %** |
| denormals | 13 | 652..1,017 per chunk |
| non-finite | 0 | 0..35 per chunk |
| values >= 1e6 | 0 | 857..1,248 per chunk |
| distinct md5 | 3 | **198 / 198 — every chunk distinct** |

So the tail is neither constant nor garbage: it is **device-specific payload on a
different record layout** (chunk 3's md5 differs for every device — see §5), which
the 15,552-B stride simply mis-slices. `read_tm`'s `if i >= 3 ... break`
(`tm_parser.py:344`) is therefore correct as a stop, and opening the tail stays out
of scope per `D24` ("not attacked speculatively") — it is `S17b`/Phase 6's call.

## 5. Cross-device comparison (the decisive structural fact)

`md5` of chunks 0/1/2 for every GW5-family `.tm` in Gowin EDA Standard 1.9.12.03:

| device | size | chunks | chunk 0 | chunk 1 | chunk 2 | chunk 3 | published grades (`device_info.csv`) |
|---|---|---|---|---|---|---|---|
| GW5AST-138C | 3,139,786 | 201 | `02634de1` | `7c6360ec` | `6d5f7bce` | `f99ad88d` | C1/I0, C2/I1 |
| GW5A-25A | 2,285,913 | 146 | `02634de1` | `7c6360ec` | `6d5f7bce` | `c95b9475` | ES, C1/I0, C2/I1, **A0** |
| GW5AT-60B | 3,698,397 | 237 | `02634de1` | `7c6360ec` | `6d5f7bce` | `85ece636` | ES, C1/I0, C2/I1, **A0** |
| GW5AT-60ES | 3,698,397 | 237 | `02634de1` | `7c6360ec` | `6d5f7bce` | `32c6656a` | **ES only** |
| GW5ART-15A | 3,871,722 | 248 | `02634de1` | `7c6360ec` | `6d5f7bce` | `d0794c3b` | ES, C1, C1/I0, C2/I1 |
| GW3A-20A | 3,225,036 | 207 | `02634de1` | `7c6360ec` | `6d5f7bce` | `6daae1fe` | (different family) |

…and the same three hashes for all 22 GW5* devices the install ships, plus the two
GW3A devices. The 1.9.11.03 archive
(`$DATASTORE/ide-share-device/edu-1.9.11.03`) gives the identical three hashes for
GW5A-25A/25B, GW5AS-25B, GW5ART-15A, GW5AST-138B/138C and GW5AT-60B —
**chunks 0-2 did not change between IDE 1.9.11.03 and 1.9.12.03.**

Answers to the questions `P0.T36` asks of the sibling files:
- **Do GW5A-25A.tm and GW5AT-60B.tm also have 3 decodable chunks?** Yes — exactly
  three, and they are the *same three bytes* as GW5AST-138C's.
- **Do their chunk-0 values match their own datasheet's C2/I1?** Yes, trivially:
  DS981E Table 3-34 (GW5AT) and DS1105E Table 3-21 (GW5AS) publish `tLUT4_CFU`
  0.297/0.539, `tSR_CFU` 1.075/1.148, `tCO_CFU` 0.200/0.230 — **identical numbers to
  DS1239E Table 3-13**. The published CFU table is itself family-generic, so one
  family-generic chunk 0 satisfies all three datasheets.

**Consequence.** Chunks 0-2 cannot be a per-device speed-grade array: GW5AT-60ES
(one grade, ES) and GW5A-25A (four grades, incl. A0) carry the identical three
chunks, and so does a GW3A part. They are a **family-generic three-model preamble**;
the per-device data begins at chunk 3, on a layout this parser does not yet know.
That is also why chunk 0 can be labelled `C2/I1` for `GW5AST-138C` without the label
being device-specific — the datasheet column it matches is family-generic too.

## 6. Parking lot for Phase 6 (`S17b`)

1. Identify chunk 2's `0.862 x` derate against vendor STA (voltage corner vs process
   corner) — the L1 measurement (`D49c`) is the discriminator.
2. Identify chunk 1's spread-less/alternate-mux combinational model.
3. Open the chunk 3+ device-specific region (`D24` gate: only if L0 shows the shared
   tables are inadequate for the 138K die).
4. No rename of `unidentified_1` / `unidentified_2` is warranted by this
   measurement; neither is a DS1239E column. A rename remains Phase 6's to make.

## 7. Reproduction

```
python -m pytest tests -k "timing_chunks" -q          # in apicula, epic/gw5ast138c
```
`tests/test_timing_chunks.py` re-derives every number quoted above from the shipped
`.tm` and asserts this file's three rows against it.
