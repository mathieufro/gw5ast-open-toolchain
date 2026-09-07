# OSER4 / OSER8 / OSER10 / OVIDEO on GW5AST-138C

Status: **not closed.** `E1` is unreachable through the open flow as the
database stands, for a reason measured here rather than guessed, and the
reason is a bigger finding than the row: **`G-FCLK-138C` does not generalise
from the DDR pair to the gearboxes.**

## RUNS SPENT

**2** of `P3.T13`'s 8 (`evidence/_budget/iologic-runs.tsv`, cumulative 28/110).
The batch was stopped after the first row rather than spending the other six
on a design the open flow cannot route. Batch log
`evidence/_runs/p3-oser.log`; designs under `$DATASTORE/p3t13`.

## THE SHAPE

`shapes/io_ser.py` renders one serialiser per point with **no fabric cell**
(`D105`): the parallel word comes off two package balls, even bits from one
and odd bits from the other, and `Q`/`Q0` drives a third. The divider's reset
and the gearbox's reset are two balls rather than one inverter, because an
inverter is a fabric cell on a net that reaches the scoped tile. `PCLK` comes
from a `CLKDIV` in HCLK block 5, pinned in **both** flows (`INS_LOC
BOTTOMSIDE[4]` for the vendor, `(* BEL = "X117Y108/CLKDIV_0" *)` for
`nextpnr`) so the `PCLK` net has one endpoint set.

The serialiser sits on `E21` = `IOR51A`, cell `(181,50)`, the **A** half:
`db.shortval[ttyp]['IOLOGICB']` holds 3 fuse coordinates against
`IOLOGICA`'s 100 on tile types 245, 247 and 87 alike, so an IOLOGIC is
configurable on the A half only (`P3.T11`'s named gap, re-measured here for
the bank-2 tile types). `F20`, the board's `RGMII_GTXCLK`, is a `B` ball and
would have had no fuse table to compare.

The sweep is the primitive's own parameter set, one axis per run:
`prim_sim.v` declares `HWL` and `TXCLK_POL` on `OSER4` (`:10342`) and `OSER8`
(`:10912`) and **no parameter at all** on `OSER10` (`:11303`) or `OVIDEO`
(`:10718`). A `defparam` naming a parameter the primitive does not declare is
a GowinSynthesis error, so the eight points are three on each parameterised
width and the default on each of the other two.

## THE BLOCKER, MEASURED

`p3-oser-io_ser-0000` (`oser4-default`): **the vendor built it** -- `gw_sh`
returned 0 and the bitstream decodes to `MODE=OSER4` at `IOLOGICA` of
`(181,50)`. The **open flow** did not:

```
Warning: Failed to find a route for arc 0 of net fclk_IBUF_I_O.
libc++abi: terminating due to uncaught exception of type std::out_of_range: dict::at()
```

Root cause, read straight out of the database:

```
db.tiles[245].pips['FCLK']  ->  KeyError (no sources at all)
db.tiles[247].pips['FCLK']  ->  KeyError
db.io2hclk                  ->  {}
```

The IOLOGIC `FCLK` wire has **no driver in the 138C chipdb**, so no gearbox
can be clocked in the open flow on this die. `ODDR`/`IDDR` are unaffected
because they clock from `CLK0`, whose mux does carry the eight `GB*` globals.
The `GW5A-25A` has no `FCLK` tile pip either; it reaches `FCLK` through
`io2hclk`, which has four entries there and none here.

`P3.T09`'s crash class is also still live: a failed route is reported as a
`Warning` and then `dict::at()` throws out of `router1`, so the run aborts
instead of returning a routing failure. That is a second, independent
nextpnr defect worth a separate fix.

## `G-FCLK-138C` IS REFUTED FOR THE GEARBOXES

`P3.T08` measured that this die has no HCLK->FCLK edge in the model and that
twelve vendor bitstreams set no `FCLK*` pip, and concluded that the vendor
clocks IOLOGIC over `BUFG`/global. All twelve of those designs were
`ODDR`/`IDDR`. The **first** vendor gearbox bitstream on this die says
otherwise. Decoded through apicula's own `IOLOGIC` shortval table
(`audit_gearbox_attrs.py`, no oracle run spent -- decoding a file is a pure
function of it):

| | `OSER4` at `IOLOGICA` of `(181,50)`, ttyp 245 |
|---|---|
| vendor attributes | `OUTMODE=MODDRX21`, `CLKOMUX=ENABLE`, `LSRIMUX_0=0`, **`WRFCLKSEL=UNK102`**, **`FCLKSEL1=HCLK2`**, **`FCLKSEL2=HCLK2_`** |
| vendor fuses (7) | `(0,123) (3,131) (5,129) (8,127) (10,120) (11,133) (11,134)` |
| `gowin_pack` attributes | `OUTMODE=ODDRX2`, `CLKOMUX=ENABLE`, `LSRIMUX_0=0`, `LSROMUX_0=1`, `TSHX=SIG`, `CLKODDRMUX_WRCLK=ECLK0`, `CLKODDRMUX_ECLK=UNKNOWN` |
| `gowin_pack` fuses (5) | `(5,129) (8,127) (10,120) (11,133) (11,134)` |

The packer's set is a **strict subset** of the vendor's: nothing is
over-emitted, and the two bits it misses -- `(0,123)` and `(3,131)` -- are
exactly the fast-clock selection. `OUTMODE`'s two spellings reach the same
bits, the same naming difference `P3.T11` recorded for `MODDRX1`/`ODDRX1`;
`LSROMUX_0=1`, `TSHX=SIG` and the two `CLKODDRMUX_*` are worth zero fuses
here, so they are the encoding artefact of a zero code and not an
over-emission.

So on the GW5AST-138C the vendor **does** feed a gearbox's `FCLK` from an
HCLK, and names the lane in the fuse: `FCLKSEL1=HCLK2`/`FCLKSEL2=HCLK2_`.
That is the same shape `GW5A_25A.get_out_iologic_attrs`
(`gowin_pack.py:6334-6363`) already models, keyed on `bel.fclk` in
`SPINE10..13`. `G-FCLK-138C` stands for `ODDR`/`IDDR`, which need no
fast-clock selection, and is refuted as a statement about the die.

## THE FIX, AND WHY IT IS NOT IN THIS ROW

Three pieces, in order:

1. **`apycula/chipdb.py`** -- populate `io2hclk` for the `GW5AST-138C` from
   the measured pin -> HCLK-block table (`P3.T07`, `evidence/pin-to-hclk/`),
   so an HCLK output reaches every IO tile of its block. `gw5_make_pin_to_hclk`
   is in Phase 3's owned function list; `io2hclk` is what
   `gowin_arch_gen.py` reads to create the `FCLK` arc.
2. **`nextpnr` chipdb regeneration** -- `.bba` + `.bin` and the installed
   pair re-recorded, because a new arc changes the database.
3. **`gowin_pack.py`** -- `GW5AST_138C.get_out_iologic_attrs` /
   `get_in_iologic_attrs`, emitting `WRFCLKSEL`/`FCLKSEL*` off `bel.fclk` the
   way the 25A does and dropping the zero-code attributes above.

Only (3) is a Phase-3-local edit; (1) and (2) are a chipdb change and a
database rebuild, and (2) invalidates every `.bin` measured before it. That
is more than `P3.T13`'s remaining six runs can validate, so it is escalated
rather than started half-way: the row stays open with its cause named.

## FILES

* `runs.jsonl` -- the one measured row (`verdict: aborted`, the open flow's
  own return codes in `notes`).
* `attr-audit.json`, `attr-gap.tsv` -- the vendor/apicula attribute and fuse
  comparison above.
* `audit_gearbox_attrs.py` -- the audit, shared with the `ides` row
  (`--slug ides`); it imports `P3.T11`'s decode instrument rather than
  copying it, and spends no oracle run.
