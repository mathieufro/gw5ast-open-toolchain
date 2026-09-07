# `evidence/dcs/` — DCS on the GW5AST-138C

Two rows live here.

## `P1.T28` — the tile-type cross-reference

No oracle campaign of its own: the DCS builder searches the same four grid
values the DQCE probe measured. Artefacts `tiles-138c.md` / `tiles-138c.json`.

## `P1.T31`/`P1.T32` — the quadrants, the ports and the open flow

**Full artefact: `ports-138c.md`.** Headline: the shipped 138C chipdb carried
**zero** DCS entries; the die has **four** DCS, two in each of the two
clock-bridge cells that carry a spine multiplexer — (54, 93) with `P26*`
(`SPINE14`) and `P27*` (`SPINE15`), (54, 88) with `P36*` (`SPINE22`) and
`P37*` (`SPINE23`). Both DCS of a quadrant share a cell on this die, which the
pre-5A `q // 2` sub-entry key cannot express, so `fse_create_dcs` keys by
`dcs_idx` when a quadrant's two tile types are equal.

### Rows

| batch | runs | ok | aborted | what it measured |
|---|---|---|---|---|
| `p1t31-dcs` | 2 | 2 | 0 | capacity and port occupancy: `n = 1, 4` `DCS` |
| `p1t31-dcs-e1` | 1 | see below | | the open flow at E1 |

```
BATCH_COMPLETE p1t31-dcs runs=2 ok=2 diff=0 aborted=0
```

### Sweep

| batch | axis | points |
|---|---|---|
| `p1t31-dcs` | `n_dcs` simultaneous `DCS` | `1, 4` |
| `p1t31-dcs-e1` | the open flow on one quadrant | `q1` (`P26*`, `SPINE14`) |

The axis is deliberately short: with four bels on the die the only occupancy
questions are "one" and "all of them", and the second point is what showed both
DCS of a quadrant sharing one cell.

### Verdict

The DCS half does **not** close. The chipdb and `gowin_pack` halves land — the
vendor builds the design, and nextpnr reports `DCS: 5/4 125%` (four hardware
bels plus the virtual user cell), where the shipped pair had no DCS bel at all
— but the open flow cannot route the mux output:

```
Warning: Failed to route net 'muxed_clk' from X91Y108/CLK1 to X87Y107/CLK0 using dedicated routing.
ERROR: Can't route the muxed_clk network.
```

**Cause, MEASURED.** `globals.cc route_dcs_net` routes the `CLKOUT` net from
the *clock source*, through the DCS's fake `CLKIN`->`CLKOUT` pip, to the
loads, using global resources only. On this die a DCS output reaches exactly
one half of the clock plane — `SPINE14`/`SPINE15` the top, `SPINE22`/`SPINE23`
the bottom — and every measured-good I/O location on this part is in banks 4
and 5, i.e. on the **bottom** edge, so the loads the placer puts next to them
are in the bottom half while the DCS the router picks (`P26*`) is in the top.
The clock cannot cross halves, and nothing in `route_dcs_net` chooses the DCS
by which half the loads are in.

One necessary fix was found and made while chasing this, and it is worth
recording on its own: `fse_create_dcs` used to give a DCS output a node of its
own named after its spine, which on this die is an **island** — the bridge
cell's spine wires are not the clock network, the half's
`CBRIDGEOUT_<half><n>` node is, and the DQCE-gated spines only belong to theirs
because they are multiplexer destinations the fse tables name. `dcs_clkout_node`
now joins a 138C DCS output to `CBRIDGEOUT_TOP6/7` / `CBRIDGEOUT_BOTTOM6/7`.
Pre-5A devices keep the spine name. That removed the island; it did not remove
the half boundary.

**Owner of the remainder:** a follow-up DCS row. What it needs is either a
half-aware DCS choice in `route_dcs_net`, or a shape whose loads are pinned
into the half its DCS feeds. Neither is a device fact in dispute — the vendor
compiles the same design — so this is an open-flow gap, recorded, not a
refutation.

### Known gap

`SELFORCE` and `CLKSEL[0..3]` are **UNVERIFIED** on this die: no vendor
bitstream in this campaign routes an external net into either bridge cell for
those ports, so the wire names in the model are the pre-5A ones, chosen only so
that two DCS sharing a cell name different wires. A 138C design that drives
`CLKSEL` dynamically is not yet modelled. See `ports-138c.md`.

### Artefacts

`ports-138c.md`, `tiles-138c.md`, `tiles-138c.json`,
`runs/capacity-runs.jsonl`, `runs/capacity-result.json`,
`_runs/p1t31-dcs.log`.

## `P1.F2` — the input side, closed

**Full artefact: `input-side-138c.md`.** The half boundary the section above
owns was fixed by `P1.T40` (the spine permission set is derived from the
database); what remained was the **input** side, and it was one hardcoded
literal: `chipdb.get_logic_clock_ins` returned a single logic-to-clock gate
for this die (`# XXX for now only one gate: BRMDCLK1`) instead of the 24 per
half the `.dat` `CMuxTopIns` / `CMuxBotIns` tables describe. With no gate node,
the bare `*MDCLK*` / `*BDCLK*` wires the DCS input multiplexers select had no
driver anywhere on the die.

Both halves now come from the tables, and the bare gate name the **central**
multiplexer uses (fse table 38) is aliased onto the half MEASURED to own it —
four differential vendor compiles (`p1f2-dcsin` a/b/c/d: fabric net, two DCS,
four DCS on four clocks, PLL output) plus the `P1.T31` baseline all resolve it
to the `CMuxBotIns` gate. `nextpnr` needed no source change; it gained the
gate check that would have caught the hole (16 of 16 DCS input multiplexers
had no source with a driver before, 0 after).

### Sweep

`clocking_dcs` gained a third point, `sel4`, whose four `CLKIN` carry four
different clocks so `CLKSEL` selects among distinct sources — the design the
input side exists for.

### Known gap, narrowed

`SELFORCE` and `CLKSEL[0..3]` stay **UNVERIFIED**: the four-DCS bitstream
routes no external net into either bridge cell for them either. What would
close it is named in `input-side-138c.md` §6, together with the `PCLK*` half
of the input multiplexer, which is still driverless and which no bitstream in
this campaign selects.

## `P1.T38` second pass — the row closes as a refusal, not at `E0`

**Full artefact: `refusal-138c.md`.** Re-run on the pair this phase lands on,
all three sweep points: `BATCH_COMPLETE p1t38c-dcs runs=3 ok=0 diff=0
aborted=3`, `BATCH_SKIPPED … refused=3`, each row `verdict: "refused"` with
`gowin_pack`'s exact words. `P1.F4`'s `reject_untraced_dcs_control` (`D30`)
refuses every design that drives `CLKSEL`/`SELFORCE`, which is every design
the `clocking_dcs` shape builds — so it refuses exactly what `P1.F2` closed at
`E0`. The refusal is right and is kept: `E0`/`E1` mask routing (`D32`) and the
`CLKSEL`/`SELFORCE` fuses are pip fuses, so the equivalence check could not
see the untraced part. Status is `refused:<named error>` (`A12`); `S9` stays
NOT REACHED. The vendor half of each run completed and left its `.fs`.

## `P1.F5` — the control side, traced; the refusal is lifted

**Full artefact: `control-138c.md`.** The `refused:<named error>` status the
section above records was correct on the evidence it had and is now
**superseded by measurement**, not by weakening the guard: the twenty
`SELFORCE`/`CLKSEL[0..3]` wires of the four DCS are traced, so
`gowin_pack.reject_untraced_dcs_control` (`D30`) no longer has anything to
refuse on this die.

Three things had to be settled in order.

1. **Is the control dynamic at all on Arora V?** Yes, and the vendor's own
   documents say so — `UG306-1.0.9E` §3.2 Table 3-2 lists `CLKSEL` and
   `SELFORCE` as `Input` ports with no tie-off note, the prose says `CLKOUT`
   *"can be dynamically switched"*, `DCS_MODE`'s sixteen values are a
   switching-mode enumeration, and Gowin's own `prim_sim.v`, shipped in a
   **GW5AST138** reference design, samples `CLKSEL` on clock edges. So
   `refused:not-a-dynamic-input-on-GW5AST-138C` was **not** available.
2. **Why five campaigns found nothing.** They searched the bridge cells. The
   control wires are not there — on the 25A they are not in the DCS's cell
   either — they are ordinary fabric wires of the cell *beside* the bridge,
   `(54, 89)`, reached through the fabric crossbar and carrying ordinary pip
   fuses rather than clock-mux fuses.
3. **The wires.** Two orthogonal differential axes, both against an
   all-constant baseline that still places `DCS 4/20`: five runs each making
   one control bit dynamic on all four DCS (bit identity) and four runs each
   making one instance's whole control bus dynamic (site identity). The two
   axes agree on all twenty wires; the `n{1..4}` sweep confirms the site
   order independently, `n1dyn` most sharply — the vendor put one logical DCS
   on two hardware DCS and drove exactly those two sites' wire groups.

### Sweep

18 vendor attribution runs, batch `p1f5-dcsctl`
(`base`, `sel0..sel3`, `force`, `n{1..4}{dyn,con}`, `inst0..inst3`), all
`gw_sh` rc 0. Then the `clocking_dcs` shape's own three points (`q1`, `q2`,
`sel4`) through the open flow at `E1`, batch `p1f5-dcs`.

### Verdict

See `control-138c.md` §7.
