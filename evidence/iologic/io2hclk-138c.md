# HCLK -> IOLOGIC FCLK on the GW5AST-138C (`P3.F1`, `D106`)

`P3.T13` measured that this die's `io2hclk` was empty, that the IOLOGIC `FCLK`
wire therefore had no driver, and that `nextpnr` aborted out of `dict::at()`
rather than reporting the failed route. This closes all three.

## Why the pre-existing code produced nothing

`chipdb.gw5_make_hclk_pips` created the `HCLK<block><lane> -> FCLK{A,B}` pips
inside the branch guarded by `gw5_hclk_idx(...) >= 0`. On the GW5A-25A that
guard is satisfied by every peripheral cell, because its `gw5_hclk_idx` is a
region rule. On every other GW5A device `gw5_hclk_idx` is the *block-cell*
test -- a cell is a block iff it is one of the six measured block locations --
so the guard held for six cells out of 19 838 and for none that carries an
IOLOGIC. `gw5_create_hclk_iol_pip` returned `False` for anything that is not
the 25A on top of that.

The shape difference underneath is real: the 25A has one HCLK block per side,
the 138C has **two on each of left, right and bottom and none on top**, so the
block that serves an IO cell is not the block that *is* that cell.

## The derivation (`chipdb.gw5_hclk_arcs`), and its sources

| ingredient | source | value on this die |
|---|---|---|
| the six blocks | `_gw5a_hclk_locs`, measured `P1.T04` from `.fse` table 48 | (27,0) (27,181) (81,0) (81,181) (108,64) (108,117) |
| per-side block order | vendor `INS_LOC` convention, SUG1018 sec 2.9, measured `P1.T08d` over 24 positions | `LEFTSIDE[0..3]`=block 0, `[4..7]`=2; `RIGHTSIDE`=1,3; `BOTTOMSIDE`=4,5 |
| the boundary between two blocks of one side | the inter-HCLK **bridge** cell between them: a cell carrying `.fse` table 48 that is not a block | left and right: row 63; bottom: none between columns 64 and 117 |
| boundary where the `.fse` puts no bridge | midpoint of the two block cells | bottom: column 90 / 91 |
| which cells have an FCLK at all | `fse_iologic` -- the same test that creates the bel | 164 cells, 326 bels (164 `IOLOGICA` + 162 `IOLOGICB`) |

The eleven table-48 cells of this die, read from the shipped `.fse`, are the
six blocks plus five bridges: (63,0) (63,181) (108,0) (108,118) (108,181).
Five bridges close a ring of six blocks with **one arc left open** -- the top
edge, which carries no block, no bridge and, measured over the whole grid, no
IOLOGIC either. That is the consistency check the derivation passes and a
midpoint-only rule does not have to.

`(108,118)` is *not* read as a boundary: both bottom blocks (columns 64 and
117) lie on the same side of it, and reading it as one would put block 5's own
cell outside block 5's arc. Every block's cell falling inside its own arc is
the property the GW5A-25A's hand-traced arcs have, and it is asserted as
`test_io2hclk_arc_contains_its_own_block_cell`.

The GW5A-25A keeps its literals. Its arcs cross corners -- bottom-edge columns
>= 64 are served by the block on the *right* edge -- and a nearest-block walk
of the ring reproduces them only to 14 cells in 254, so replacing them would
be an unmeasured change to a device this epic does not measure.

## The resulting table

| block | cell | arc | IO cells |
|---|---|---|---|
| 0 | (27,0) | left, rows 1..61 | 29 |
| 1 | (27,181) | right, rows 1..61 | 29 |
| 2 | (81,0) | left, rows 64..106 | 21 |
| 3 | (81,181) | right, rows 64..106 | 21 |
| 4 | (108,64) | bottom, cols 2..90 | 32 |
| 5 | (108,117) | bottom, cols 91..178 | 32 |

164 cells, each in exactly one block.

## Cross-check against the vendor bitstream

`P3.T13`'s one vendor `OSER4` sits at `IOLOGICA` of cell (50,181) -- ball
`E21` / `IOR51A`, a bank-2 A-half pad -- and sets `FCLKSEL1=HCLK2`,
`FCLKSEL2=HCLK2_`, `WRFCLKSEL=UNK102` (fuses `(0,123)` and `(3,131)`, the two
by which `gowin_pack`'s set was a strict subset of the vendor's). The walk
puts that cell in **block 1**, whose `FCLKA` sources are exactly
`HCLK10 HCLK11 HCLK12 HCLK13` -- the block whose lane 2 the vendor named.
`P3.T07`'s independent pin sweep put the same bank-2 pad's clock on block 1.

## The chain, built end to end in the open flow

The design `P3.T13` could not route (`$DATASTORE/p3t13/p3-oser-io_ser-0000`:
board pin -> HCLK -> `CLKDIV` in block 5 -> `PCLK`, HCLK -> `FCLK` ->
`OSER4` at (50,181)) now builds through the whole open flow with no change to
the design:

```
yosys      rc=0
nextpnr    rc=0   22.7 s   timing_allow_fail_needed=False
gowin_pack rc=0
top.fs     25a0a40e5c6f64e006ee43094e96a7efb18d37a4607547ebd4659ebf33b21e5e
```

Decoding both bitstreams through the `P3.T11` instrument, at the same cell:

| | vendor | open flow |
|---|---|---|
| attributes | `OUTMODE=MODDRX21 CLKOMUX=ENABLE LSRIMUX_0=0 WRFCLKSEL=UNK102 FCLKSEL1=HCLK2 FCLKSEL2=HCLK2_` | `OUTMODE=MODDRX21 CLKOMUX=ENABLE LSRIMUX_0=0 WRFCLKSEL=UNK102` |
| fuses | `(0,123) (3,131) (5,129) (8,127) (10,120) (11,133) (11,134)` | `(0,123) (5,129) (8,127) (10,120) (11,133) (11,134)` |

Six of the vendor's seven bits now match, `OUTMODE` included. The one
remaining bit is `(3,131)`, and it is **not** a modelling gap: `nextpnr` chose
`IOLOGIC_FCLK=HCLK_OUT3`, the vendor lane 2, and lane 3's selection is the
zero code on this table. Which of a block's four lanes carries a clock is a
router choice on both sides, fixed by no constraint in the design -- the same
class as a pip choice, which is never a verdict term (`E2` is bonus only).
Closing the `oser` row at `E1` therefore needs the lane either pinned in both
flows or masked as routing; that decision belongs to `P3.T13`, which still
holds 6 of its 8 runs.

## Artefacts

| artefact | sha256 |
|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `df0ae17df04eeb3ce23a9edf56d37adcd5fc5d231ebccfc7fd1d3daf7613a958` |
| `chipdb-GW5AST-138C.bin` | `3df1431840852dbdb9f22953c584927d7f3e5bf259f902ff7cd8be5b53c82d18` |
| `nextpnr-himbaechel` | `8eeb3efb9693eaff8c39935f225395e19011acc5a403f31feb608183b58a2e03` |

Installed as one pair to every location: `$DATASTORE/toolchains/nextpnr/bin`,
`.../share/nextpnr/himbaechel/gowin`, `.../share/himbaechel/gowin` and
`$DATASTORE/p3`. The installed msgpack now holds **326 IOLOGIC bels**.

## The 326-vs-zero disagreement, settled

`P3.T05` counted 326 IOLOGIC bels; `P3.T19` read zero from "the chipdb". Both
were right about the file they read. There are two:

* `apicula-wt/p3io/apycula/GW5AST-138C.msgpack.xz` -- the Phase-3 branch's,
  `6a776c74...` at the time, 326 bels;
* `apicula/apycula/GW5AST-138C.msgpack.xz` -- the `epic/gw5ast138c` submodule
  checkout's, `7f3c64c9...`, **0 bels**, built before `P3.T03` deleted the
  blanket IOLOGIC gate.

The venv's editable `apycula` install resolves to the *submodule checkout*, so
any run that does not set `PYTHONPATH` to the task's worktree reads the second
one. Every command in this row exports `PYTHONPATH=<apicula worktree>`.

## Two findings this proof hands to `P3.T13`, both at zero run cost

**1. The lane is each flow's own choice, and only one of them is stable.**
Both vendor bitstreams already on disk -- `oser4-default` and the
`TXCLK_POL=1` point -- select `FCLKSEL1=HCLK2`/`FCLKSEL2=HCLK2_`, lane 2 of
block 1. `nextpnr` selects `IOLOGIC_FCLK=HCLK_OUT3` for the same design.
Nothing in the design constrains it: `INS_LOC` and `BEL` pin the `CLKDIV`
(block 5 lane 0, for `PCLK`), not the block lane the `FCLK` net lands on,
and each flow's own HCLK-section allocator picks it. Closing the row at `E1`
needs that named -- either a constraint that pins the lane in both flows, or a
seventh `dontcare.mask` entry for the fast-clock selection attributes under
the §5.3 rules (`Mask.masks()` returns `False` for every attribute today, so
the entry alone would not change a verdict: the attribute comparison would
have to consult it). It is a claim about the hardware either way and belongs
in `P3.T13` with its remaining 6 runs, not in this fix.

**2. `TXCLK_POL` never reaches the open bitstream.** The two sweep points
differ only in `TXCLK_POL`; the vendor bitstream carries `TXCLK_POL=1` on the
second, and the two open-flow bitstreams are byte-identical
(`25a0a40e5c6f64e006ee43094e96a7efb18d37a4607547ebd4659ebf33b21e5e` both
times). Neither `nextpnr`'s `pack_iologic` nor `gowin_pack` moves the
parameter. That is a genuine `P3.T13` gap, now measured before its first new
run rather than after it.

## Runs spent here

**Zero.** Both vendor bitstreams were already on disk from `P3.T13`'s two
runs; everything above is the open flow, which is not an oracle run, and
decoding a file, which is a pure function of it. Ledger unchanged at 28/110.
