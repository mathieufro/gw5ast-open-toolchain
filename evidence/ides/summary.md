# IDES4 / IDES8 / IDES10 on GW5AST-138C

## Row

**`E1` on all six points**, `cells` 0, `attrs` 0, both decode checks `ok`, no
unexplained bit.  All six are `verdict: diff` on **`conns` alone**, which is
the row's one open item and is written up below.

**6 oracle runs**, the task's whole cap (`p3-ides`, ledger
`evidence/_budget/iologic-runs.tsv`, cumulative 40/110).  The open half was
rebuilt once afterwards at no run cost (`tools/redo_open_half.py`).

| point | primitive | level | verdict | cells / attrs / conns | decode c1 / c2 |
|---|---|---|---|---|---|
| `ides4-reset-pad` | `IDES4` | `E1` | diff | 0 / 0 / 10 | ok / ok |
| `ides4-reset-tied` | `IDES4` | `E1` | diff | 0 / 0 / 10 | ok / ok |
| `ides8-reset-pad` | `IDES8` | `E1` | diff | 0 / 0 / 20 | ok / ok |
| `ides8-reset-tied` | `IDES8` | `E1` | diff | 0 / 0 / 16 | ok / ok |
| `ides10-reset-pad` | `IDES10` | `E1` | diff | 0 / 0 / 14 | ok / ok |
| `ides10-reset-tied` | `IDES10` | `E1` | diff | 0 / 0 / 12 | ok / ok |

`IDES4` is the RGMII RX gearbox, so the RGMII-relevant point is
`ides4-reset-pad`.

## Sweep

The **reset source**, one change per run: `prim_sim.v` declares no parameter
at all on `IDES4` (`:8258`), `IDES8` (`:8461`) or `IDES10` (`:8675`), so there
is no `defparam` to move, and the reset is the one input that changes the
cell's configuration -- it is what `LSRIMUX_0`/`LSRMUX_LSR` select.  Three
widths x a pad-driven and a constant-tied `RESET`.

`PCLK` is `FCLK / (width / 2)` (UG304E p.62-69) and the shape carries that
ratio into every design through `_io_base.GEARBOX_DIV_MODE` and the rendered
`CLKDIV`.  It is asserted on the generated artefacts
(`test_ides_pclk_ratio_ides4`, `..._ides8`) and not on a `create_clock` line:
`gen.render_sdc` is Phase 0's and frozen, it emits one `create_clock` per
top-level **port**, and `PCLK` is internal to the design and divides
differently at every point.  That deviation from the blueprint's literal test
text is recorded here rather than worked around.

## Placement, and the pinned HCLK lane

Same ball, same block and the same single `INS_LOC "pclk_div" BOTTOMSIDE[2];`
line as the `oser` row -- see `evidence/oser/summary.md` for the mechanism
(`D107`), for the measurement that rules the RGMII balls out (block 1 has no
modelled clock escape, `D100a`), and for the two bottom-edge tile types whose
`IOLOGICA` bel has no ports.  The deserialiser sits at `AA9` = `IOB53A`, cell
`(row 108, col 52)`, scope tile `(52, 108)`, the A half.  The open flow places
it at `X52Y108/IOLOGICAI` with `IOLOGIC_FCLK=HCLK_OUT2`.

## The input fast-clock selection is NOT fuse-backed on this die

This is the question `spec-primitives.md` said this row's first vendor
bitstream would settle, and it settles it in the negative.  Decoded at the
gearbox's own tile, on all six vendor bitstreams:

| width | vendor `IOLOGICA` attributes |
|---|---|
| `IDES4` | `INMODE=IDDRX2 CLKIMUX=ENABLE LSROMUX_0=0` |
| `IDES8` | `INMODE=UNK76 CLKIMUX=ENABLE LSROMUX_0=0` |
| `IDES10` | `INMODE=IDDRX5 CLKIMUX=ENABLE LSROMUX_0=0` |

There is **no `FCLKSEL*` and no `WRFCLKSEL`** on the input path, where the
output path sets three of them on the same tile type in the same batch.  So
the GW5A-25A's `FCLKSEL5`/`6`/`7` emission is correctly **absent** from
`GW5AST_138C.get_in_iologic_attrs` rather than missing from it, and nothing
was implemented ahead of the measurement.

The open flow's attributes are **identical** on all three `-reset-pad` points.
The three `-reset-tied` points differ by one attribute: the vendor writes
`LSRIMUX_0=0` and the open flow writes nothing.  `0` is that attribute's zero
code, no fuse moves, and the row's `attrs` count and residual are both zero --
recorded, not forgiven silently.

## `gowin_unpack` could not name an `IDES8` at all

MEASURED: `gowin_pack` writes `INMODE = IDDRX4` (value id 11) for an `IDES8`,
the vendor writes the same fuses, and **both** decode back as value id 76,
which the shipped attribute-value table leaves unnamed (`UNK76`).
`_iologic_mode` is keyed by name, so no `IDES8` was recovered from any
bitstream and the point failed `c1`.  A single alias now names it, on the
**input** path only -- the same id in `OUTMODE` is a different mode and must
keep failing to resolve rather than acquire a wrong name
(`gowin_unpack._iologic_inmode_alias`, `tests/test_unpack_iologic_modes.py`).

The IOLOGIC **aux half** (`IOLOGIC_DUMMY` on the B half of every gearbox wider
than a DDR pair) was the other decode blocker; it is written up in
`evidence/oser/summary.md` and is fixed in `equiv.decode_check_c1` and
`equiv.bitstream_bel_exported`.

## Open: the `conns` difference, and what this row owed the `ODDR`/`IDDR` row

Every point differs on `conns` and on nothing else.  All of it is inside the
pad tile `(52, 108)` -- `per_tile` is a single entry -- and the first
difference of every point is the IOB's own `OE` port bound to a different net
on the two sides:

```
tile (52,108) bel 0: port vendor=OE->net:7652d7eef353ff16
                          open=OE->net:27cc987c19fa1aa3
```

The counts (10, 10, 20, 16, 14, 12) scale with the width, which is what the
`ODDR`/`IDDR` row's open item predicted: it closed the `ODDR` half at
`verdict: ok` and left the `IDDR` half differing on four `conns` because the
vendor takes the deserialised output out of the tile on wire `F7`
(`IOLOGIC.Q14`) where `nextpnr` takes it out on `F0` (`IOLOGIC.Q8`).  This row
puts three widths on ten pads each and reproduces the same class across all of
them, so the mapping question is now measured at width 4, 8 and 10 rather than
only at width 2.  Naming which of the two maps is right needs the vendor's
whole fabric-wire -> `Q_i` correspondence read out of these six bitstreams,
which is a decode task with no oracle-run cost and is left as this row's named
open item rather than guessed at.

## Artefacts

Toolchain pair, installed at all four locations the harness reads:

| artefact | sha256 |
|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `df0ae17df04eeb3ce23a9edf56d37adcd5fc5d231ebccfc7fd1d3daf7613a958` |
| `chipdb-GW5AST-138C.bin` | `3df1431840852dbdb9f22953c584927d7f3e5bf259f902ff7cd8be5b53c82d18` |
| `nextpnr-himbaechel` | `f33f1ca9ee9dfa23b54a807e824bb1abc66e1508d533389b728209e36e63c6a1` |

* `runs.jsonl` -- the six measured rows.
* `attr-audit.json`, `attr-gap.tsv` -- the per-point vendor/open attribute
  comparison above (`evidence/oser/audit_gearbox_attrs.py --slug ides`).
* Designs and logs: `$DATASTORE/p3t14/`, batch log
  `evidence/_runs/p3-ides.log`.
