# gowin_unpack decodes CLKDIV / HCLK on the GW5AST-138C — P1.T08c

apicula `clocking/gw5a-hclk-6block`. The second half of D98: before this,
`gowin_unpack` had no CLKDIV decoder for this device, so an HCLK-scoped E0 was
vacuous by construction (`../hclk/clkdiv-138c.md` §4).

## What changed (`apycula/gowin_unpack.py`, table-driven, no fuse literal)

New `_hclk_block_devices` (`{'GW5AST-138C'}`), `hclk_attrname_table`,
`hclk_val_name`, `_hclk_block_pips`, `parse_hclk_block`,
`hclk_decode_completeness`; one added line in `parse_tile_`; `tile2verilog`'s
`belre` extended with `CLKDIV2_|CLKDIV_|HCLK` plus a branch that emits a real
primitive from `extra_func[...]['bels'][slot]`. The inputs are exactly the ones
`gowin_pack.get_CLKDIV_fuses` -> `chipdb.get_hclk_fuses` writes: the `HCLK`
shortval table, `db.hclk_pips`, `db.extra_func`. `attrids.py`, `chipdb.py` and
`wirenames.py` are untouched.

## Decode proof — P1.T11 vendor bitstream (`run.fs` `3d36f0aa…`, verified)

```
block cell (108, 117) ttyp 379: CLKDIV_0 ['DIV_MODE="2"'],
    HCLK5 ['HCLK_UNK969="HCLK_UNK965"', 'HCLK_UNK991="HCLK_UNK969"',
           'LWSPINEBR2="LWSPINETR3"']
decoded cell counts: {'CLKDIV': 1, 'HCLK': 1}
```
The other five block cells decode as "(nothing configured)", which is correct —
the design has one CLKDIV. Through the harness's own entry point:
```
CELL TYPES: {'BANK': 8, 'CLKDIV_': 1, 'DFF': 138240, 'HCLK': 1, 'IOB': 324, 'LUT': 28}
TOTAL CELLS: 138602
   Cell(x=117, y=108, z=0, type='CLKDIV_') ['DIV_MODE="2"']
```
(was 138,600 cells of four types, no CLKDIV at any tile). `DIV_MODE="2"` is the
design's own `defparam`. Bel names are nextpnr's (`CLKDIV_0`), so
`equiv.split_bel_name` / `decode_check_c1` match a placed cell with no
translation table.

## S6b completeness — 1284 / 1284 decoded, 0 undecoded

Per block: 63 `HCLK` shortval entries + 151 fuse-bearing `hclk_pips` = 214;
x 6 blocks = **1284**. Of those `clkdiv_div_entries` = 216 (36 x 6, i.e.
`HCLKDIV0..3_DIV` x 9 values) and `pip_fuses` = 906. 23 of the 63 attribute ids
have no name in `attrids.hclk_attrids`; rather than edit `attrids` they are
named `HCLK_UNK_ATTR<id>` from the device's own logicinfo and emitted onto the
`HCLK<block>` cell, so nothing is silently dropped.

Known-undecoded, each with a measured reason:
1. **CLKDIV2 — `clkdiv2_entries` = 0.** The 138C `.fse` HCLK table carries no
   CLKDIV2 entry at any of the six block ttyps (272/273/275/276/274/379): no
   `BK<s>MUX<h>_OUTSEL`, no `BK<s><h>DIV2_RST`. This mirrors `gowin_pack`'s
   `GW5A_25A.get_CLKDIV2_fuses`, which returns no fuses. The decoder is wired
   for the attribute and fires on any device whose table carries it — it simply
   cannot fire here. Whether the silicon has no CLKDIV2 fuse or the table-48
   walk never emits one is **NOT MEASURED**; it needs a vendor run that
   instantiates a CLKDIV2 and a fuzz diff.
2. **Five per-block default bits** the vendor sets at every HCLK block cell that
   lie in **no** chipdb table at all — verified against every shortval/longval/
   longfuse table, tile pips, clock pips, `hclk_pips` and bel mode/flag bits for
   ttyp 272 and 379. Outside the counted fuse space; **not fuzzed**.

## Regression — GW1N-9C and GW2A-18C UNCHANGED (byte-for-byte)

No `.fs` is checked in for either device, so the diff was taken on the
**unpacker output itself**: `git show HEAD:apycula/gowin_unpack.py` into a
pristine tree, then `parse_tile_` (bels + pips + clock_pips, JSON, sorted) over
**every tile of the whole grid** on both trees with the real chipdbs.

| device | tiles | before == after | sha256 |
|---|---|---|---|
| GW1N-9C | 1363 | **IDENTICAL** | `330282dee36274e565019db7272f59cc1c4ea48e544695effc218c23b83d3136` |
| GW2A-18C | 3080 | **IDENTICAL** | `51e9543fecc1d4a9f95dab719a71589145489d587b6c2f16afb9fa61a14b123f` |
| GW5A-25A | 3404 | **IDENTICAL** | `abbd4ec33859caf50b95a7e0553c3185649774df06985f6fba21eaba73d6441e` |

Belt and braces: `test_unpack_hclk_decode_is_device_gated` asserts the device
gate directly, and neither legacy chipdb has any `extra_func['clkdiv']` tile.

## Tests

`tests/test_gw5ast138c_clocking.py`: `test_unpack_decodes_clkdiv_138c` (heavy),
`test_unpack_hclk_completeness_138c` (heavy),
`test_unpack_hclk_decode_is_device_gated` (fast) — **3 passed**.
Fast scope: **265 passed, 2 skipped, 50 deselected, 1 xfailed**.

## Unmeasured, stated as such

- CLKDIV2 on the 138C (above).
- The `HCLK5` mux state decodes to `HCLK_UNK*` names; what those nodes are
  physically is unmeasured — they come from the chipdb as-is.
- The five per-block default bits are unattributed.
- A whole-device `gowin_unpack` CLI run (`-o unpack.v`) over the 34 MB
  bitstream was **not** completed (killed after ~15 min). `tile2verilog` was
  exercised directly on the decoded HCLK tile instead, so the new bel names are
  proven not to crash the Verilog path, but the full CLI run is unmeasured.

## Stale line noted, not fixed

`fuzz/gw5ast138c/harness/equiv.py:unpack_netlist`'s docstring still says
"`gowin_unpack.py` itself is **frozen** and not edited (§1 Frozen)". This task
edits it, so that sentence is now stale.
