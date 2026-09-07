# IDES4 / IDES8 / IDES10 on GW5AST-138C

Status: **not started, blocked on the same defect as the `oser` row.**
**0** oracle runs spent of `P3.T14`'s 6.

An input deserialiser is clocked from `FCLK` exactly as an output serialiser
is, and `evidence/oser/summary.md` measures that the IOLOGIC `FCLK` wire has
no driver in the 138C chipdb (`db.tiles[245].pips` has no `FCLK` key,
`db.io2hclk == {}`), so `nextpnr` cannot route it and the open half of every
row would abort. Spending six oracle runs to record six `aborted` rows would
buy nothing the `oser` row has not already established, so they are not
spent; the fix is written up there.

## WHAT IS READY

`shapes/io_des.py` renders one deserialiser per point with **no fabric cell**
(`D105`): the deserialised word leaves on ten package balls rather than being
reduced in fabric, a width narrower than ten drives the balls it does not use
from `rst`, and `rst` always leaves on its own ball, so no point carries a
top-level port the vendor could prune out from under its `IO_LOC`. The
gearbox sits on `E22` = `IOR49A`, cell `(181,48)`, the **A** half, for the
reason the `oser` row gives.

The swept axis is the **reset source**, one change per run: `prim_sim.v`
declares no parameter at all on `IDES4` (`:8258`), `IDES8` (`:8461`) or
`IDES10` (`:8675`), so there is no `defparam` to move, and the reset is the
one input that changes the cell's configuration -- it is what `LSRIMUX_0` /
`LSRMUX_LSR` select, the pair the 138C override exists for (`P3.T11`
finding 2). Three widths times a pad-driven and a constant-tied `RESET` is
six points.

`PCLK` is `FCLK / (width / 2)` (UG304E p.62-69) and the shape carries that
ratio into every design through `_io_base.GEARBOX_DIV_MODE` and the rendered
`CLKDIV`. It is asserted on the generated artefacts
(`test_ides_pclk_ratio_ides4`, `..._ides8`) and **not** on a `create_clock`
line: `gen.render_sdc` is Phase 0's and frozen, it emits one `create_clock`
per top-level **port**, and `PCLK` is internal to the design and divides
differently at every point -- so a per-point slow-clock period cannot reach
the `.sdc` through `ShapeSpec.clocks` at all. The ratio is asserted where the
design really carries it. That is a deviation from the blueprint's literal
test text and is recorded here rather than worked around.

## THE MEASUREMENT THIS ROW OWES ANOTHER ROW

`evidence/oddr-iddr/summary.md` closes the `ODDR` half at `verdict: ok` and
leaves the `IDDR` half differing on four `conns`, because the vendor takes
the deserialiser's output out of the tile on wire `F7` (`IOLOGIC.Q14`) where
`nextpnr` takes it out on `F0` (`IOLOGIC.Q8`) -- one of the two has `Q0` and
`Q1` the wrong way round. This row's six designs put three widths on ten pads
each and decode the vendor's whole fabric-wire -> `Q_i` map for free, which
settles it. It is the first thing to do once the `FCLK` route exists.
