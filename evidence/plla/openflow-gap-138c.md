# What blocks the open flow from packing a `PLL` on the GW5AST-138C (`P1.T23`)

**Status: CLOSED by `P1.T41`** — all four gaps, plus three more the flow only
exposed once it ran end to end. What closed each one, and the `E1` verdict line
of the design that proves it, is in **`pump-138c.md`**. The measurement below is
kept verbatim as the record of what was found; nothing in it has been rewritten.

**Status when written: MEASURED.** Every claim below is a command that was run and its
exact output, except the three marked SOURCE, which are `file:line` reads with
no cheap runtime probe.

`P1.T23` was told to make the open flow pack the PLL, or to report exactly what
blocks. It could not: **four** independent gaps stand between a `PLL` design
and a `.fs`, and the last of them needs a measurement campaign of its own.
`P1.T23`'s twenty sweep rows are therefore vendor-oracle rows with the open
half recorded as `aborted` and the nextpnr exit code in `notes` — the same
shape `P1.T22` landed, and admissible for the same reason.

Toolchain under test: yosys 0.63, `nextpnr-himbaechel` `38dbe2cd` (built from
`integration/p1-clocking` `527c7169`), chipdb `.bin`
`e95f3594ef2f13f564da8fb71712b45922f3456e5f5402f211727a47920792e7` built from
**this** branch's msgpack `899228319ca59a47bea99126efaf2b5eb0ba11c460a2ee1e1c3e6ba2247a70aa`
(the `clocking/plla-138c` + `clocking/gw5a-hclk-6block` merge), pinned with
`--chipdb`. The installed binary/`.bin` pair was not touched.

---

## 0. What now works — the chipdb carries twelve PLL bels

This is the first 138C chipdb in which the PLL exists at all. `P1.T18`-`T20`'s
`_gw5a_pll_slots['GW5AST-138C']` populates `extra_func[(row, col)]['pll']`, and
nextpnr's `gowin_arch_gen.py:1100-1107` turns each of those into a bel. From
the nextpnr resource report of the probe run:

```
Info: 	                PLLA:       0/     12     0%
```

Twelve, matching DS1239E Table 1-1 and `sites-138c.md`. Nothing about the site
table, the port map or the chipdb build is a blocker.

## 1. BLOCKER — `INS_LOC "<inst>" PLL_L[0]` is an unresolved placement macro

Command: the `P1.T23` shape's `top.cst`, unmodified.

```
ERROR: Unknown placement macro PLL_L in INS_LOC for cell dut_pll
ERROR: failed to parse CST file 'top.cst'
nextpnr exit 125
```

`cst.cc:334` — `static const dict<std::string, IdString> macro_bel_type = {};`
— is empty, with the comment "the PLL_* rows land with the PLL work". This is
an intentional, documented extension point, not a defect. Until it is filled
there is **no E1 on the open side for any PLL shape**, because `INS_LOC` is
how E1 pins placement.

## 2. BLOCKER — the cell type is `PLL`, the bel type is `PLLA`

Command: the same design with the `INS_LOC` line removed.

```
ERROR: Unable to place cell 'dut_pll', no BELs remaining to implement cell type 'PLL'
nextpnr exit 125
```

yosys keeps the vendor cell type verbatim (`synth_gowin -family gw5a` emits
`"type": "PLL"`), `pack.cc:162` matches only `id_rPLL`/`id_PLLVR`/`id_PLLA`,
and `getBelBucketForCellType` (`gowin.cc:1089-1121`) falls through to
`return cell_type`, so placement needs cell type == bel type exactly. `id_PLL`
exists in `constids.inc:1268` but is referenced by no `.cc`/`.h`.

`D96` says this device's primitive **is** `PLL`, so the fix is to make the bel
type follow the device rather than to rename the cell: the primitive name
belongs in `extra_func['pll']` beside `slot_idx`, and `gowin_arch_gen.py`
should read it (defaulting to `PLLA`, so the 25A is byte-identical). Renaming
`PLL` -> `PLLA` in the packer would instead route a `PLL` cell into
`get_PLLA_fuses`, i.e. into 25A attribute semantics — wrong for a different
primitive with a different port set.

SOURCE, related and worth fixing in the same change: `gowin.h:107`
`type_is_pll` omits `id_PLLA`, so every `is_pll()` site
(`gowin.cc:648,662,712,995`) already skips GW5A PLLs today.

## 3. BLOCKER — `gowin_pack` has no `get_PLL_fuses`, and its slot path is 25A-only

SOURCE. `Pack.place` dispatches `getattr(device, f'get_{cell.typ}_fuses')`
(`gowin_pack.py:7099`); `belre` (`:405`) already matches a `PLL` bel name.
`GW5A` defines `get_PLLA_fuses` (`:5628`) and nothing defines `get_PLL_fuses`.
Even reaching `get_PLLA_fuses` does not help: it calls `common_pll_handler`
(`:5632`) -> `set_pll_slot_fuses`, and `ChipDB.get_pll_slot_fuses` (`:723-724`)
is hardcoded to `get_shortval_fuses(db, 1024, av, 'PLL')`. Pseudo-ttyp 1024
does not exist on this device (`P1.T17`, MEASURED: no pseudo-ttyp >= 1024 and
no `drpfuse` table); the 138C's PLL fuses are ordinary `shortval[ttyp]['PLL']`
fuses in the site's three grid tiles.

## 4. HARD BLOCKER — the charge-pump constants do not exist for this device

Measured, on this branch:

```python
>>> GW5AST_138C.get_pll_pump(fref=30.769, fvco=861.538)
Exception: get_pll_freq_R is not implemented.
```

`get_pll_freq_R` and `get_pll_coeffs` are defined only on `GW5A_25A`
(`gowin_pack.py:6333`, `:6340`); `GW5A.get_pll_attrvals` calls `get_pll_pump`
unconditionally (`:5586`) to derive `A_ICP_SEL`, `A_LPF_RES_SEL`, `FLDCOUNT`
and `KVCO`. So **no** 138C `PLL` can have its attribute set computed at all,
whatever the dispatch does.

These are loop-filter constants with no datasheet source — `P1.T22` already
recorded this (`attrmap-138c.md` §5.2) and assigned it to "the task that lands
`get_PLL_fuses`". They cannot be copied from the 25A: that device's VCO band
is `[800, 1600]` against this one's `[650, 1300]`, so its pump table is a
different curve. Copying it would emit plausible-looking wrong fuses, which is
worse than refusing. Deriving them is a **fuzz campaign** — sweep `FCLKIN`
and the dividers, read `A_ICP_SEL`/`FLDCOUNT` out of each vendor `.fs` through
the `shortval[35]` table `P1.T22` already validated, and fit the two
piecewise-constant tables — not an edit.

Batch A's twenty rows are exactly the first twenty samples of that campaign:
`sweep-a-138c.json` records, per point, the `(attr_id, value)` every moved bit
resolves to, including `FLDCOUNT` (16) and `A_ICP_SEL` (111).

---

## Recommended shape of the follow-up task

1. `apycula/chipdb.py`: put the primitive name in `extra_func['pll']`
   (`'PLL'` for the 138C, `'PLLA'` for the 25A — the 25A chipdb must stay
   byte-identical).
2. nextpnr `gowin_arch_gen.py`: read it; `cst.cc`: fill `macro_bel_type` with
   `PLL_L`/`PLL_R`/`PLL_B` resolved through the measured `slot_idx` bijection
   (`_gw5a_pll_slots`, `sites-138c.md` §8); `pack.cc`/`gowin.h`: accept
   `id_PLL` and add `id_PLLA` to `type_is_pll`.
3. `apycula/gowin_pack.py`: `GW5AST_138C.get_PLL_fuses` writing ordinary
   three-tile `shortval[ttyp]['PLL']` fuses, no slot, no `extra_slots`.
4. The pump campaign of §4, then `get_pll_freq_R`/`get_pll_coeffs` for the
   138C and a `gowin_pll.device_limits` entry.

Steps 1-3 are mechanical once §4 exists; §4 is the one that needs oracle runs,
so it should be sequenced first.
