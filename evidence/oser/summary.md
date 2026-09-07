# OSER4 / OSER8 / OSER10 / OVIDEO on GW5AST-138C

## Row

**`E1`, 5 of 6 points `verdict: ok`.**  `OSER4` at its default, at
`TXCLK_POL=1` and at `HWL="true"`, plus `OSER8` and `OSER10`, all with
`cells` 0, `attrs` 0, `conns` 0, both decode checks `ok` and no unexplained
bit.  `ovideo-default` is `E0` `diff` on the **decode check alone** and is
written up below.

**8 oracle runs**, the task's whole cap: 2 on the bank-2 designs `P3.T13`
spent before `P3.F1` and 6 on the closing sweep (`p3-oser-b`, ledger
`evidence/_budget/iologic-runs.tsv`, cumulative 34/110).  The open half of
those 6 was rebuilt three times after the vendor step, at **no run cost**
(`tools/redo_open_half.py`).

| point | primitive | level | verdict | cells / attrs / conns | decode c1 / c2 |
|---|---|---|---|---|---|
| `oser4-default` | `OSER4` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `oser4-txclk-pol` | `OSER4` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `oser4-hwl` | `OSER4` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `oser8-default` | `OSER8` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `oser10-default` | `OSER10` | `E1` | ok | 0 / 0 / 0 | ok / ok |
| `ovideo-default` | `OVIDEO` | `E0` | diff | 0 / 0 / 0 | **mismatch** / ok |

`OSER4` in `MODDRX21` is the RGMII TX gearbox, so the RGMII-relevant DDR
point is `oser4-default` and it is one of the five that close.

## Sweep

The primitive's own parameter set, one axis per run.  `prim_sim.v` declares
`HWL` and `TXCLK_POL` on `OSER4` (`:10342`) and `OSER8` (`:10912`) and no
parameter at all on `OSER10` (`:11303`) or `OVIDEO` (`:10718`).  Both
parameters are swept on `OSER4` and neither on `OSER8`: `gowin_pack` reads
them in `common_iologic_handler`, one handler for every width, so a second
width would re-measure the same code path with a run the cap does not have.

## The HCLK lane is now part of the match (`D107`)

`P3.F1` left the row one bit short: the vendor picked block-1 lane 2 and
`nextpnr` lane 3, and nothing in the design fixed either.  Both flows are now
pinned by **one line**:

```
INS_LOC "pclk_div" BOTTOMSIDE[2];
```

* **vendor** -- the `{SIDE}[0~7]` convention `P1.T08d` mapped over 24
  positions (SUG1018-1.7E Table 2-2): index = block ordinal along the side x 4
  + lane, so `BOTTOMSIDE[2]` is HCLK block 4, lane 2.
* **open** -- the same line.  `nextpnr-himbaechel`'s `.cst` reader took
  `SIDE[0|1]` only, a one-block-per-side shape, and aborted the run on
  anything else; it now splits the index the same way and orders the
  candidate blocks along the side
  (`himbaechel/uarch/gowin/cst.cc getConstrainedHCLKBel`).  The shape
  therefore carries **no** `(* BEL *)` attribute any more, and
  `gen.OPEN_FLOW_INS_LOC_FORMS` lets the line into `top-open.cst`.

Why that pins the *lane* and not just the divider: a `CLKDIV` takes its input
from `HCLK_MUX_ALPHA<block><lane>`, which is the same wire `HCLK<block><lane>`
drives the IOLOGIC `FCLK` from.  Pinning the divider forces the `FCLK` net on
to that lane, and both flows then decode
`FCLKSEL1=HCLK2`/`FCLKSEL2=HCLK2_`.  **No `§5.3` mask entry was needed**; the
lane is a matched term, not a forgiven one.

### Why the row moved off the RGMII balls

Pinning the lane means placing a `CLKDIV` in the gearbox's own HCLK block.
The dock's RGMII balls are served by block 1, and blocks 0 and 1 have no
modelled clock escape (`D100a`), so that divider's output cannot reach the
gearbox's `PCLK` at all.  MEASURED, not inferred -- the same `oser4-default`
design with the divider moved to `X181Y27/CLKDIV_2`:

```
Warning: Failed to find a route for arc 0 of net pclk.
ERROR: Net fclk_IBUF_I_O has no route to the FCLK of dut (sink wire X181Y50/FCLKA)
```

Bank 5's general-purpose 3.3 V balls all sit in HCLK block 4, which `P1.T08d`
mapped lane by lane, so the row is measured at `AA9` = `IOB53A`, cell
`(row 108, col 52)`, scope tile `(52, 108)`.  Two bottom-edge tile types --
63 and 251, which carry `Y17`, `P20` and `N15` -- have an `IOLOGICA` bel with
**no ports at all**, and a gearbox placed on one fails in `nextpnr`'s global
router with `Net 'pclk' has an invalid sink port dut.PCLK`; that is why the
ball is `AA9` and not the first bank-5 A-half ball on the list.

## `TXCLK_POL` is fuse-backed on this die, and now reaches the bitstream

`D107`'s second branch is **refuted by measurement**: the two vendor `OSER4`
bitstreams that differ in nothing but `TXCLK_POL` are not byte-identical.
They differ by exactly one fuse:

```
TXCLK_POL=0   (0,123) (3,131) (5,129) (8,127) (10,120) (11,133) (11,134)
TXCLK_POL=1   (0,123) (3,131) (5,129) (8,125) (8,127) (10,120) (11,133) (11,134)
                                             ^^^^^^^
```

and `(8,125)` decodes as the IOLOGIC attribute `TXCLK_POL=1` -- **attrid
116**, the Arora V spelling.  The parameter reached `nextpnr`'s output JSON
all along (`{"OUTMODE": "ODDRX2", "TXCLK_POL": "1"}`); what lost it was
`gowin_pack`: `GW5AST_138C` inherited the pre-5A `common_iologic_handler`,
which moves the parameter to `TSHX` (attrid 6) -- an attribute this die
spends no bit on.  `HWL` had the same fault, moved to `UPDATE=SAME` instead
of attrid 117.  Both now use the Arora V attributes, and the `ODDR`, `IDDR`
and `IDDRC` fuse sets `P3.T11` closed are unchanged (re-measured: 0
over-emitted, 0 missing on all three).

## What the audit says, per point

`audit_gearbox_attrs.py` decodes **both** bitstreams at the shape's own scope
tile and compares the two attribute dictionaries.  It no longer re-invokes the
packer with parameters of its own: `FCLKSEL*`, `TXCLK_POL` and `HWL` all
depend on the placed cell's parameters and on the lane the router took, none
of which a stub call can know.  No oracle run is spent -- decoding a file is a
pure function of it.  Four of the six points are attribute-identical; the two
that are not:

| point | attribute | vendor | open | note |
|---|---|---|---|---|
| `oser10-default` | `HWL` | `TRUE` | -- | GowinSynthesis sets `HWL` on a 10:1 gearbox by itself; `OSER10` declares no such parameter, so nothing in the design asks for it and `gowin_pack` emits nothing.  No unexplained fuse survived the residual analysis, so it is inside a masked class -- named here, not dismissed. |
| `ovideo-default` | `ISI` | -- | `ENABLE` | Emitted by the open flow only.  Same disposition: no unexplained fuse survives, and the row's set-level counts are all 0. |

## The `OVIDEO` point, and why it is `E0`

Every set-level count is 0 and `c2` (the bit round-trip) is `ok`; the point is
`diff` because `c1` -- does the decode recover every placed cell? -- cannot
name the cell.  MEASURED: an `OVIDEO`'s `OUTMODE` is written by `gowin_pack`
as `VIDEOTX` (value id 50) and by the vendor identically, and **both** decode
back as value id **74**, which `attrids` names `LVDSOUT`.
`gowin_unpack._iologic_mode` has no entry for that spelling, and adding one
would rename a genuine differential output on the GW5A-25A, where
`gowin_pack` really does emit `OUTMODE=LVDSOUT`
(`gowin_pack.py:6461,6473`).  So the collision is named and left: on this die
the video-gearbox output mode and `LVDSOUT` are one fuse pattern, and no
decoder can tell them apart from the bitstream.  The missing `VIDEOTX` key
itself **is** fixed -- `_iologic_mode` carried only `VIDEORX`, so a device
whose id 50 resolves cleanly would also have failed.

## Two decode defects fixed, both measured here

1. **The IOLOGIC aux half.**  A gearbox wider than a DDR pair takes both
   halves of its tile: the primitive on the A half and an `IOLOGIC_DUMMY` on
   the B half whose whole configuration is `OUTMODE`/`INMODE = DDRENABLE`.
   `gowin_unpack` skips exactly that value by design, so no bitstream on any
   device decodes it -- and `OSER8` and `OSER10` failed `c1` and fell back to
   `E0` on a cell the format cannot carry.  It is now recovered through the
   main cell's wide mode at the same site (`equiv.decode_check_c1`), and left
   out of the `E1` bel export (`equiv.bitstream_bel_exported`), each with the
   same justification and each refused when no gearbox decodes beside it.
2. **`IDES8`** -- see `evidence/ides/summary.md`.

## Artefacts

| artefact | sha256 |
|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `df0ae17df04eeb3ce23a9edf56d37adcd5fc5d231ebccfc7fd1d3daf7613a958` |
| `chipdb-GW5AST-138C.bin` | `3df1431840852dbdb9f22953c584927d7f3e5bf259f902ff7cd8be5b53c82d18` |
| `nextpnr-himbaechel` | `f33f1ca9ee9dfa23b54a807e824bb1abc66e1508d533389b728209e36e63c6a1` |

The `.bin` is unchanged from `P3.F1` (no constids change); only the binary
moved.  The pair is installed at all **four** locations the harness and the
tools read, `$DATASTORE/chipdb/std/` included -- `openflow.DEFAULT_CHIPDB`
points there, it still held the pre-`P3.F1` `.bin`, and the mismatch aborted
all six runs of `p3-oser-b`'s first open half with
`Assertion failure: ... idstring_idx_to_str`.  The vendor bitstreams survived
that and were reused.

* `runs.jsonl` -- the six measured rows.
* `attr-audit.json`, `attr-gap.tsv` -- the per-point vendor/open attribute
  comparison above.
* `audit_gearbox_attrs.py` -- the audit, shared with the `ides` row
  (`--slug ides`).
* `archive/runs-bank2-block1.jsonl` -- the row `P3.T13`'s first two runs
  produced on the bank-2 pad, kept because it is what measured the
  consequence of not pinning the lane.
