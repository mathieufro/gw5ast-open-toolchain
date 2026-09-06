# `PLL` `DYN_*` modes in the open bitstream (`P1.T42` follow-up)

`P1.T42` measured the five dynamic-reconfiguration selects on the vendor side
and left one gap: `gowin_pack` built **every** `PLL` static — `get_pll_attrvals`
wrote `A_DYN_DPA_EN`/`A_DYN_ICP_SEL`/`A_DYN_LPF_SEL` as literal `FALSE` and
never wrote `A_DYN_IDIV_SEL`, `A_DYN_FBDIV_SEL`, `A_DYN_MDIV_SEL` or
`A_DYN_ODIV0_SEL` at all, so a design that asked for a dynamic mode got a
static bitstream and no diagnostic. Two of the five ids were also unnamed.

## The fix

* `attrids.pll_attrids` names the two batch-C first sightings:
  `A_DYN_FBDIV_SEL` **124** and `A_DYN_MDIV_SEL` **131**.
* `gowin_pack.DYN_SELECT_ATTRS` lists the seven `DYN_*` selects and
  `GW5A.get_pll_attrvals` encodes each one from the cell parameter
  (`FALSE` when the cell does not name it), exactly as it already did for every
  divider.

## Proof — batch `p1t42b-pll-dyn`, 2 oracle runs, cumulative 218

`FUZZ_PLL_AXIS=dyn`, `--sweep-points 2`, level `E1`: the axis baseline
(`dyn_none`) and one `DYN` point (`dyn_idiv`, `DYN_IDIV_SEL "TRUE"`, the
235-bit sighting of `P1.T22`/`P1.T42`), same site `PLL_L[0]`, same operating
point (`Fpfd` 25 MHz, `FVCO` 900 MHz).

```
BATCH_COMPLETE p1t42b-pll-dyn runs=2 ok=2 diff=0 aborted=0
```

Both rows: `verdict ok`, `level E1`, `diff_count.cells/attrs/conns = 0/0/0`,
`decode_check {"c1": "ok", "c2": "ok"}`.

Absolute decode of tile `(27,1)` through `decode_pll_attrs_138c.py`
(`pll_attrvals['TRUE'] == 50`):

```
dyn_idiv-VENDOR {'A_DYN_IDIV_SEL': 50, 'A_DYN_FBDIV_SEL': None, 'A_DYN_MDIV_SEL': None, 'A_DYN_ODIV0_SEL': None, 'A_DYN_DPA_EN': 50}
dyn_idiv-OPEN   {'A_DYN_IDIV_SEL': 50, 'A_DYN_FBDIV_SEL': None, 'A_DYN_MDIV_SEL': None, 'A_DYN_ODIV0_SEL': None, 'A_DYN_DPA_EN': 50}
dyn_none-VENDOR {'A_DYN_IDIV_SEL': None, 'A_DYN_FBDIV_SEL': None, 'A_DYN_MDIV_SEL': None, 'A_DYN_ODIV0_SEL': None, 'A_DYN_DPA_EN': 50}
dyn_none-OPEN   {'A_DYN_IDIV_SEL': None, 'A_DYN_FBDIV_SEL': None, 'A_DYN_MDIV_SEL': None, 'A_DYN_ODIV0_SEL': None, 'A_DYN_DPA_EN': 50}
```

The swept select is present in the open bitstream and absent from its own
baseline, on both sides. `A_DYN_DPA_EN` decodes to the same value on all four
bitstreams, baseline included, so it is not a mode this point turns on: it is
this attribute's field decoding identically for both boolean values, and the
two flows agree on it.

Tests: `tests/test_gw5ast138c_plla.py::test_pll_attrids_name_the_two_batch_c_first_sightings`,
`::test_pll_dyn_selects_are_encoded_from_the_cell_not_forced_false`,
`::test_pll_dyn_selects_default_to_false`.
