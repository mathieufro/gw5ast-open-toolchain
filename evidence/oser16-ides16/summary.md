# `OSER16` / `IDES16` on the GW5AST-138C — adjudicated (`P3.T16`)

## Verdict: **the vendor accepts both.** The blueprint's expected refusal is REFUTED.

Two vendor runs, one per primitive, on bank-5 ball `AA9` (`IOB53A`, cell
`(108,52)`, HCLK block 4 — the same ball `io_ser`/`io_des` measure the 4/8/10-bit
gearboxes on). `gw_sh` returned 0 with **zero** errors and wrote a full `run.fs`
in both, and the PnR resource report names the primitive it built:

| run | primitive | vendor | IOLOGIC cells used |
|---|---|---|---|
| `p3-oser16-io_ser16-0000` | `OSER16` | **accepted** | `2/285` — the A+B pad pair |
| `p3-ides16-io_des16-0000` | `IDES16` | **accepted** | `1/285` |

So the 138C silicon has a 16-bit gearbox in both directions, and the two
primitives are *asymmetric in cost*: `OSER16` occupies two IOLOGIC cells and
`IDES16` one. That asymmetry is a measured fact a future implementation needs
and could not have been guessed from `cells_xtra_gw5a.v`, which declares
`OSER14`/`IDES14`/`IDES32` and neither 16-bit form.

Where the expectation came from, and why it was wrong: `cells_xtra_gw5a.v` is
yosys' GW5A cell list, not the device's. The *vendor's own* GW5A simulation
library declares both — `$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:11595` (`OSER16`)
and `:8906` (`IDES16`) — and yosys elaborates `OSER16` fine (`RTLIL module
\OSER16`, one instance) because the generic Gowin cell library carries it.

## The open flow, before `P3.T17`

Both runs die in `nextpnr-himbaechel`, and both die on the *wrong* message:

```
ERROR: OSER16 dut can not be placed at X52Y108/IOBA
ERROR: IDES16 dut can not be placed at X52Y108/IOBA
```

That text is raised by `pack_oser16`/`pack_ides16`
(`himbaechel/uarch/gowin/pack_iologic.cc:780`, `:854`) when
`GowinUtils::get_tile_io16_offs(x, y)` returns `(0,0)`, which it does for
**every** IO tile of the 138C: the `io16` aux-offset table is populated for the
GW1N/GW1NS families only. The refusal is therefore real, but its wording blames
the ball, which sends a reader hunting for a better ball that does not exist.
`P3.T17` replaces it with a refusal that names the device and the primitive.

## Consequence (coordination note, not absorbed here)

`P3.T16`'s Done-when flips to **implement**, and the blueprint says an
acceptance raises a follow-up rather than being silently absorbed. The follow-up
is recorded in `impl/PROGRESS.md` as **P3.T16a — implement `OSER16`/`IDES16` for
the 138C in both tools** (bels + `io16` aux offsets in `chipdb.py`, the GW5A
`get_tile_io16_offs` table in `himbaechel/uarch/gowin/globals.cc`/`gowin_utils`,
the packer's fuse emission, and an `E1` shape whose sixteen output bits each
land on their own ball). It is out of this task's four-run budget.

## Shape caveats

* `io_des16` XOR-reduces `Q10..Q15` onto one ball through a fabric LUT, because
  bank 5 brings out eleven balls this shape has not already claimed, not
  sixteen. A fabric LUT is placed freely by each flow, so this shape can never
  close `conns` at `E1` (`D105`); it is an adjudication vehicle only. The
  follow-up task owns the `E1` shape.
* Both rows are recorded `verdict: refused`, `level: E0`, with the vendor's
  acceptance and the open tools' exact text in `notes` and in
  `vendor-refusal.txt`. `refused` here is the **open flow's** verdict — it is
  the terminal verdict the vocabulary has for "one flow would not build it"
  (`D30`), and the row says in full which flow refused and which accepted.

## `P3.T17` — what the refusal now says, and the deviation it records

The blueprint's literal wording — `OSER16 is not supported on GW5AST-138C` —
is a claim about the *silicon*, and `P3.T16` measured it false. Both tools
therefore refuse with **"is not implemented on GW5AST-138C"**, which names the
device and the primitive (`D30`, `V16`) and is true: the gap is in the open
tools' database, not in the die. The refusal says so in its own text so a
reader is not sent hunting for a better ball.

* `nextpnr-himbaechel` — `pack_io16` gates on the GW5A family before either
  `pack_oser16`/`pack_ides16` can reach `check_io16_placement`.
* `gowin_pack` — `GW5A._refuse_io16`, reached through `get_OSER16_fuses` /
  `get_IDES16_fuses`, raises `PackRefused` (exit `3`, a verdict rather than a
  crash) and quotes the vendor's measured IOLOGIC cost.

`apycula/chipdb.py`'s standing comment that "OSER16 / IDES16 were only in three
chips and these primitives simply do not exist in the latest series" is
corrected in the same change: it is refuted by these two runs.
