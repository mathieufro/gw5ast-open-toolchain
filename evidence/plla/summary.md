# `evidence/plla/` — GW5AST-138C PLL sites (`P1.T17`, `P1.T18`, `P1.T19`, `P1.T20`)

## Row

12 rows in `runs.jsonl` — one vendor run per PLL site, batch `pll-trace-pilot2`,
shape `clocking_pll_trace`, level `E1`. Every row's **vendor** half completed
and produced `run/impl/pnr/run.fs`; every row's verdict is `aborted` because
the **open** half has no PLL bel in the installed nextpnr `.bin` yet. The
measurement this slug owes is on the vendor side, and it is complete.

## Sweep

The swept axis is the **placement**, not a parameter: one hard `PLL`, pinned by
`INS_LOC "dut_pll" PLL_<side>[<n>];`, over all twelve sites
`PLL_L[0..3]`, `PLL_R[0..3]`, `PLL_B[0..3]`. Dividers are held at one legal
point (FCLKIN 50 MHz, IDIV 1, FBDIV 1, MDIV 16 -> FVCO 800 MHz, ODIV0 8 ->
CLKOUT0 100 MHz), inside every bound of the `P1.T20` five-tuple.

## Verdict

**MEASURED, and three blueprint assumptions refuted.**

1. **Twelve sites, twelve anchors, a bijection** (`sites-138c.md` §8.1). Each
   constrained site lights up exactly one of `P1.T17`'s twelve three-tile
   `shortval[35]` groups (~120 bits per tile) and leaves the other eleven
   all-zero. `chipdb._gw5a_pll_slots['GW5AST-138C']`'s `slot_idx` is now that
   measured vendor site index, and both of `P1.T17` §3's ASSUMED items — the
   anchor tile, and the `pll_idx` ordering — are settled.
2. **The cell type is `PLL`, not `PLLA`** (§8.2). A `PLLA` instantiation is
   refused outright: `ERROR (RP0008) : There is no PLLA resource in current
   device`. `UG306-1.0.1E` Table 5-11 lists GW5A-25 as the only PLLA part.
   `PLL` has no MDIO/DRP ports and adds the dynamic-divider ports, matching
   this device's `.dat` exactly.
3. **The `.dat` names zero sites**, against the blueprint's expected 5-6
   (`sites-138c.md` §4/§6, `P1.T17`).

Open and named, not papered over (§8.3): the ~108 populated `PllIn` rows that
carry `PLL`'s `ENCLKn`/`FBDSEL`/`IDSEL`/`MDSEL`/`ODSELn`/`DTn` ports sit at
indices apicula has no table for, and `gowin_pack`'s
`get_pll_slot_fuses`/`set_pll_slot_fuses` still address a pseudo-ttyp 1024 that
does not exist on this device.

## Artefacts

| File | What |
|---|---|
| `sites-138c.md` | the site table; §8 is the `P1.T19` trace |
| `sites-138c.json` | machine-readable form of §3 |
| `attrids-138c.tsv` | 37-row attribute-id census |
| `gen_sites_138c.py` | `P1.T17` enumerator (`.fse`/`.dat`) |
| `gen_trace_138c.py` | `P1.T19` analyser (`.fs` -> per-tile bits -> site) |
| `runs/trace-138c.json` | its output: per-run bit counts for all twelve groups |
| `runs.jsonl` | the 12 evidence rows |

Oracle runs charged to `D62`: **13** (1 refused `PLLA` probe + 12 `PLL` sites);
see `evidence/_budget/clocking-runs.tsv`.

## Chipdb built from these tasks (`apicula clocking/plla-138c`)

| device | before | after | verdict |
|---|---|---|---|
| `GW5A-25A.msgpack.xz` | `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca` | `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca` | **byte-identical**, as `P1.T18` requires |
| `GW5AST-138C.msgpack.xz` | `fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb` | `b2a9d40969ac7ddd1f681c3ad5e7e6875070a9387383b3fefa3960c5d429634b` | +12 PLL `extra_func` entries |

Built in the task's own worktree only; nothing was installed into `$DATASTORE`
(the HCLK branch owns the datastore regeneration).
