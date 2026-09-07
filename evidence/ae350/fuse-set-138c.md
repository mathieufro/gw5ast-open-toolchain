# The `AE350_SOC` fuse set, settled — GW5AST-138C

Supersedes the fuse-set half of `config-fuses-138c.md` and §3 of `e1-138c.md`.
**0 vendor runs**: six bitstreams already banked, decoded by
`$OTC/tools/derive_ae350_band_bits.py`.

## The question

`S19` asks for the bel's fuse count to be zero or for the non-zero set to be
enumerated. Two readings were on the table:

1. the interface band is **port-usage-dependent** — a design's own port set
   picks which column of it is written; or
2. the block is **genuinely fuseless**, like the `EMCU`.

`e1-138c.md` §3 argued (2) from an empty intersection between two designs'
sets. The gestalt gate was right that an empty intersection cannot separate the
two readings: under (1) an empty intersection is the *predicted* outcome.

## What actually happened: the filter, not the silicon

The 77-bit set was formed by keeping the bits that (a) differ between an AE350
design and the AE350-free control, (b) sit in a tile of type 224 or 228, (c)
belong to **no pip and no bel `modes`/`flags` table**, and (d) are set in the
AE350 run. Step (c) is the defect: it never subtracted the tile types'
`shortval` tables.

Tile types 224 and 228 are **ordinary CLS logic tiles**. They carry
`LUT0`-`LUT7`, `DFF0`-`DFF7`, `ALU0`-`ALU7` and `RAM16`, and their `shortval`
tables are exactly `LUT` and `CLS0`-`CLS3`. Those tables live in tile-bitmap
**rows 9-11** — and every one of the 77 bits is in rows 10-11. They are LUT
init and CLS mode bits of ordinary logic the vendor placed in those tiles.
They were never an AE350 configuration band; there is no AE350 configuration
band.

| bitstream | AE350 | filter (c) as run in `P2.T24` | every modelled table subtracted |
|---|---|---|---|
| `p2t26-tilewires` | yes | 77 bits / 9 tiles | **0** |
| `p2t23-ae350-row` (batch 1) | yes | 3 bits at `(145, 10)` | **0** |
| `p2t23-ae350-row2` (batch 2) | yes | **0** | **0** |
| `p2t38-pll-l` | yes | 3 bits at `(159, 10)` | **0** |
| `p2t38-ddr-clk` | yes | **0** | **0** |
| `p2t26-baseline` | no | 0 | **0** |

## Two independent refutations of the port-usage reading

**(a) The bits are modelled.** With the `shortval` tables included, not one of
the 216 tiles of type 224/228 carries a single unmodelled set bit, in any of
the six bitstreams. There is nothing left to attribute to the block.

**(b) The same port set gives different bits.** `p2t23-ae350-row`,
`p2t23-ae350-row2`, `p2t38-pll-l` and `p2t38-ddr-clk` instantiate the *same*
149 ports of the *same* shape — they differ only in the capture fold and in
where the PLL is placed. Under filter (c) they give 3 bits at `(145,10)`, none,
3 bits at `(159,10)`, and none. A set that moves tile when the placement moves
and the port set does not is not a function of the port set.

## What marks the block, then

Nothing in the fuse space. Differencing `p2t26-tilewires` against its
AE350-free control over row 0 columns 145-181 gives **5 101** bits the AE350
design sets and the control does not, over 32 tiles. **5 095 of them belong to
a pip**; the remaining 6 belong to another modelled chipdb table, and **0 are
unmodelled**. The block's whole footprint there is the routing of its port
taps: no bel fuse, no attribute, no configuration bit.

That is the substitute signature the decode side now uses: a port tap of the
block is a dead end for every other cell on the die, so a pip that drives one —
or is driven by one — exists only because the block is there.
`apycula.gowin_unpack.parse_ae350` recovers the `AE350_SOC` cell from exactly
that, and `tests/test_ae350_decode.py` pins it. `AE350_SOC` is therefore **not**
in `NON_FUSE_BACKED_BELS`: `c1` asks for the cell and gets it.

## Consequences

- `GW5AST_138C.get_AE350_SOC_fuses` returns `[]` — now on a measurement, not on
  an empty intersection.
- `AE350_SOC_CONFIG_FUSES` is retracted as evidence *about the AE350*: it is a
  record of one design's LUT and CLS configuration in nine logic tiles.
- The 216 tiles of type 224/228 are ordinary fabric and are correctly outside
  the `E1` scope. There is no un-emitted interface band to carry into Phase 9,
  and the Phase-9 precondition the gate asked for is discharged as void.

FUSE-SET-VERDICT: **zero, measured**. 0 unmodelled set bits in tile types
224/228 over five AE350 bitstreams and one AE350-free control; the 77-bit and
3-bit sets are `shortval:LUT`/`CLS*` fuses of ordinary logic, not block
configuration; presence is carried by the port-tap pips and decoded by
`parse_ae350`. 0 vendor runs.

AE350-FUSE-SET: 0 bits
