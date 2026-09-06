# GW5AST-138C `PLL` charge pump, and the four gaps closed (`P1.T41`)

`openflow-gap-138c.md` recorded four independent gaps between a `PLL` design and
a `.fs` through the open flow, the last of which — the charge-pump constants —
needed a measurement campaign of its own. All four are closed. The verdict line
of the design that closes them:

```
EQUIV E1 ok   level=E1  cells=0 attrs=0 conns=0  decode c1=ok c2=ok  unexplained_bits=0
BATCH_COMPLETE p1-pll-e1 runs=1 ok=1 diff=0 aborted=0
```

## 1. The campaign

Batch `p1-pll-pump`, shape `fuzz/gw5ast138c/shapes/clocking_pll_pump.py`,
**10 oracle runs**, one hard `PLL` at `PLL_L[0]`, `FCLKIN`/`IDIV`/`FBDIV`/`MDIV`
moved together to place the PLL at a chosen `(Fpfd, Ndiv)`. `Fpfd` is bounded to
`[19, 81.25]` MHz and `FVCO` to `[650, 1300]`, so `Ndiv = FVCO/Fpfd` runs over a
wedge, not a rectangle; the ten points are its corners and edges. Batches A and B
supply 35 more points inside it for free.

**Three points were refused by the vendor**, all three of the `FCLKIN` 650 MHz
ones (`f65_n10`, `f65_n20`, `f81_n16`):

```
ERROR (PA2078): Invalid PFD frequency … suitable range is from 19MHz to 81.25MHz
ERROR (PA2078): Invalid VCO frequency … suitable range is from 650MHz to 1300MHz
```

Both derived frequencies are inside those ranges (65 MHz and 650 MHz; 81.25 and
1300), so the refusal is about `FCLKIN` itself, not about what it derives —
recorded as measured, not worked around. The reachable `Fpfd` range is therefore
19 .. 50 MHz on a single-ended input, and everything above is extrapolation.

## 2. What the vendor derives, and from what

`GW5A.get_pll_attrvals` computes four attributes from the operating point alone.
Read back out of the site's `shortval[35]` table
(`decode_pll_attrs_138c.py`; the decode is exact, not a guess — every row of the
138C table that mentions one of these attributes has exactly one positive key,
so an attribute owns a fixed bit field and its value is the unique one whose
fuse set equals `field & set_bits`):

| attribute | id | measured over 45 points |
|---|---|---|
| `KVCO` | 28 | **constant 7** — the 25A ties it to `FLDCOUNT` (`fclkin_idx // 16`); this device does not |
| `FLDCOUNT` | 16 | `(int(Fpfd // 30) + 1) * 16` — the 25A offsets the step by 1 MHz and corrects four high bands; this device does neither (`Fpfd` 28.571 → 16, 30.769 → 32) |
| `A_ICP_SEL` | 111 | `round(a[R] * Ndiv) * 10` |
| `A_LPF_RES_SEL` | 112 | the first `R` of the ladder whose current is ≤ 28 (the vendor's `0.00028` A) |
| `A_LPF_CAP_SEL` | 130 | **never written**, at any of the 45 points |

## 3. The fit

`R` and the 25A's `(Kvco, C1)` parameterisation are **not separately
identifiable** from a bitstream — only their product appears in the current — so
the fit is stated as that product and no fictional resistance is written down.
Each point pins the coefficient to an interval of width `1/Ndiv`; the fit is
their intersection, and an empty intersection would have refuted the
one-coefficient-per-resistor model.

| `r_idx` | `A_LPF_RES_SEL` | points | `Ic`/`Ndiv` interval | fitted |
|---|---|---|---|---|
| 4 | 26 (`R4`) | 36 | `[0.70313, 0.70833]` | **0.705729** |
| 5 | 27 (`R5`) | 9 | `[0.20238, 0.20652]` | **0.204451** |

Their ratio, 3.45, is a resistor step of 1.86 — the same step the 25A's own
`get_pll_freq_R` table steps by. `R3` and `R6` are unreachable on this device
(`R3` would need `Ndiv < 11.5` at a `Fpfd` low enough to keep `FVCO` in band;
`R6` needs `Ndiv > 137` against a maximum of `1300/19 = 68.4`), so neither is
guessed at: an operating point that asked for one raises.

The switch from `R4` to `R5` is predicted at `Ndiv > 39.5 .. 39.8` and measured
between `Ndiv 38` (`R4`) and `Ndiv 40` (`R5`).

**45 of 45 measured points are reproduced exactly** by
`apycula/gw5ast138c_pll_pump.py` — `gen_pump_138c.py` re-derives every one and
`test_pll_pump_reproduces_every_measured_point` asserts it.

## 4. `MDIV_SEL 1` is not a supported value — MEASURED

Three points (`f19_n35`, `f40_n17`, `f50_n13`) asked for `MDIV_SEL 1`. The
vendor validates `FVCO` with the requested 1 and then writes its own default
`A_MDIV_SEL 8`, together with a charge pump consistent with neither divider. No
bitstream built from `MDIV_SEL 1` can agree with the vendor's whatever the
packer does, so `GW5AST_138C.get_pll_attrvals` refuses it by name rather than
emitting a plausible-looking wrong fuse. The three points are excluded from the
fit and listed in `pump-138c.json` under `unsupported_mdiv_points`.

## 5. The other three gaps

| gap | closed by |
|---|---|
| 1. `cst.cc:334` empty macro table | apicula writes each site's vendor handle (`PLL_L[0]` … `PLL_B[3]`, the bijection `P1.T19` measured) into the chipdb; `gowin_arch_gen.py` emits it as a new `macro_bels` table; `cst.cc` resolves `INS_LOC "u" PLL_L[0];` through that table. `cst.cc` carries the three macro **families** and no knowledge of any die's geometry. |
| 2. cell type `PLL` vs bel type `PLLA` | the primitive is in the chipdb too (`PLL` here, `PLLA` on the 25A, which stays byte-identical) and `gowin_arch_gen.py` reads it, so the bel type follows the device rather than the family — not the reverse rename, which would have routed a `PLL` into 25A attribute semantics. `pack.cc` and `gowin_utils.cc` accept `id_PLL`; `gowin.h`'s `type_is_pll` gains both GW5A spellings, which it had been silently skipping. |
| 3. no `get_PLL_fuses` | `GW5AST_138C.get_PLL_fuses` renames the cell parameters the way `get_PLLA_fuses` does and then goes through `Device.common_pll_handler` — the site's own three tiles — instead of `GW5A`'s slot path, which addresses pseudo-ttyp 1024 and this device has none (`P1.T17`). |

Three further defects surfaced only once the flow ran end to end, and are fixed
with the rest:

* **Unwired constant tie-offs.** This die wires no `DT0`..`DT3` on the `PLL`,
  but the primitive's port list still carries them and RTL still has to tie them
  off; the router died with `No wire found for port DT00`. `pack.cc` now drops a
  *constant* tie-off on a port the device does not wire, and leaves a real
  signal connected so the router still reports it.
* **The open `.cst` withheld every `INS_LOC`.** `gen.py` did that because
  nextpnr's reader could not parse the 138C's `…SIDE[0~7]` spelling and
  `log_error`s a line it cannot resolve. It now emits exactly the spellings the
  reader accepts — which, since gap 1, includes the macro form — so the PLL is
  pinned on **both** halves and `E1` has something to assert.
* **`gowin_unpack` decoded no GW5A `PLL`.** The site had no entry in
  `tile.bels`, so the decoder walked past it and the `§5.4` `c1` check reported
  the cell missing. The chipdb now carries the bel and the unpacker decodes it.

## 6. Two harness defects the first `PLL` comparison exposed

Both were latent: the `PLL` is the first primitive whose `E0` scope tiles are
ordinary fabric tiles, and the first with no CLS address *and* no HCLK bel.

1. **`D92` was applied to the global constant nets.** `VCC` and `VSS` can never
   have matching endpoint sets between a vendor bitstream and an open one: the
   vendor ties `ADCEN` on all 400-odd IOBs of the package and the open flow ties
   none (measured here: 191,062 endpoints against 1,686). Every pip feeding them
   was therefore counted as `net_route_endpoint_diff` — 336 bits, the entire
   unexplained residual. Their endpoint set is not a design property but §5.3
   row 3's unused-tile fill seen through a routing fuse, so they are excluded
   from the row-5 test; a pip that ties an input to a constant cannot change a
   design net's connectivity, and if it did the `E0` `conns` set reports it,
   which is the term `D92` requires to stay live.
2. **`E1` had no path for a bel the vendor addresses only in the bitstream.**
   `P1.T14`/`P1.T15` built one for the HCLK bels; the `PLL` is the same case for
   the same reason (`run.tr` names no PLL site). The check is now named for what
   it does rather than for the one class that first needed it, and the `PLL` is
   in its type set.

## 7. Runs and artefacts

| item | value |
|---|---|
| batches | `p1-pll-pump` (`runs=10 ok=0 diff=0 aborted=10`, 3 refused by the vendor, 7 bitstreams), `p1-pll-e1` (`runs=1 ok=1 diff=0 aborted=0`) |
| watchdogs | `WATCHDOG_ARMED` + `WATCHDOG_COMPLETE … (clean exit)` on both |
| oracle-run budget | 10 + 1 charged; `clocking-runs.tsv`, cumulative **180** |
| fit | `gen_pump_138c.py` → `pump-138c.json`; constants in `apycula/gw5ast138c_pll_pump.py` |
| decoder | `decode_pll_attrs_138c.py` |
