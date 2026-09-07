# DCS `SELFORCE` / `CLKSEL[3:0]` on the GW5AST-138C — traced

`P1.F5`, closing the gap `refusal-138c.md` and `input-side-138c.md` §6 named:
the DCS control inputs were the last untraced part of the primitive, and
`gowin_pack.reject_untraced_dcs_control` (`D30`) refused every design that
drove them, so the `DCS` row closed as `refused:<named error>` and `S9` stayed
NOT REACHED.

## 1. Is there a dynamic path at all? — the documentation says yes

The refusal would have been permanent if the control were static on Arora V —
folded into `DCS_MODE` at elaboration. It is not, and the vendor's own
documents say so:

* `UG306-1.0.9E` §3.2 Table 3-2 (*DCS Port Description*) lists `CLKSEL` and
  `SELFORCE` as **Input** ports, with no "reserved" or "tie-off" note
  (`vendor/gowin/ip/ddr3/UG306E.txt:914-927`).
* the same section's prose: *"CLKOUT can be dynamically switched among the
  four clock inputs"*, and *"it is possible to avoid glitch on the output
  clock that you can configure the CLKSEL signal to dynamically switch the
  clock signal by setting DCS_MODE"* (`UG306E.txt:879-891`). `DCS_MODE` sets
  the switching **mode**; it does not replace `CLKSEL`.
* Table 3-3 gives `DCS_MODE`'s sixteen values (`"CLK0".."CLK3"`, `"GND"`,
  `"VCC"`, `"RISING"`, `"FALLING"`, `"CLKn_GND"`, `"CLKn_VCC"`, default
  `"RISING"`) — a mode enumeration, not a four-bit selection
  (`UG306E.txt:930-940`).
* the VHDL instantiation example maps `CLKSEL` and `SELFORCE` to user signals
  (`UG306E.txt:964-986`), and Gowin's own `prim_sim.v`, shipped inside a
  **GW5AST138** reference design, samples `CLKSEL` in `always @(posedge CLKn)`
  blocks and reads `SELFORCE` combinationally
  (`vendor/gowin/ip/ae350/.../src/can/tb/prim_sim.v:14514-14519, 14646-14653,
  14755-14763`).

`DS1239E` and `DS1104E` mention `DCS` only in their abbreviation glossaries;
`SUG283` has no `DCS` entry and defers to `UG306`. So a doc-backed refusal
(`refused:not-a-dynamic-input-on-GW5AST-138C`) is **not** available: the port
is a dynamic input and the wires had to be measured.

## 2. Why five earlier campaigns found nothing

Every earlier search looked *around the bridge cells* — `(54, 93)` and
`(54, 88)`, the two cells that carry the DCS. The control wires are not
there. On the `GW5A-25A`, whose table upstream traced by hand, they are not in
the DCS's cell either: `gw5_dcs_inputs` puts them in columns 44-48 of row 18,
the cells *beside* the bridge. The 138C follows the same shape, and its twenty
control wires are in one cell of the same band — `(54, 89)`, tile type 81,
whose only bels are `DSP_AUX0`/`DSP_AUX1`.

A search restricted to the bridge cells' own pips and to the clock-mux tables
was therefore looking in the wrong place; the wires enter through the ordinary
fabric-side crossbar of a neighbouring cell, and they carry ordinary pip
fuses, not clock-mux fuses.

## 3. The differential set

The vendor cannot constant-fold a `CLKSEL` bit driven from a fabric flop, so
every design here drives its dynamic bits from a four-bit shift register
clocked by the board clock and keeps the register alive through `dout` — the
fabric is the same in every design, and only the DCS connection changes.

| batch member | what is dynamic | why |
|---|---|---|
| `base` | nothing (`CLKSEL=4'b0000`, `SELFORCE=1'b0`) | the fold, and the diff baseline |
| `sel0` … `sel3` | `CLKSEL[k]` of all four DCS, one `k` per run | names the four wires of bit `k` |
| `force` | `SELFORCE` of all four DCS | names the four `SELFORCE` wires |
| `n1dyn`/`n1con` … `n4dyn`/`n4con` | all five, `n` DCS instantiated | the order the vendor fills the four sites |
| `inst0` … `inst3` | all five of **one** instance | the five wires of one site |

All twenty-two runs compile (`gw_sh` rc 0, pre-flight ok) and every one places
`DCS 4/20` (or `n/20`) — the constant-`CLKSEL` baseline included, so the
vendor does **not** optimise a statically-selected DCS away.

## 4. The twenty wires — MEASURED

Every diff below is against `base`, restricted to cell `(54, 89)`; the pip
destination is the wire the vendor drives, and `base`'s source is the local
constant it drives instead.

Which **bit** a wire carries, from the five one-bit-at-a-time runs:

| signal | wires |
|---|---|
| `CLKSEL0` | `A7`, `B3`, `C4`, `D5` |
| `CLKSEL1` | `B4`, `C5`, `D1`, `D6` |
| `CLKSEL2` | `A4`, `B5`, `B7`, `C6` |
| `CLKSEL3` | `A5`, `B6`, `C7`, `D3` |
| `SELFORCE` | `A6`, `C3`, `D4`, `D7` |

Four of the five runs name exactly four wires each and the four sets are
disjoint. `sel2` alone is noisy (18 wires): its placement of the shift
register moved, so its own four are read by elimination — the four of the
twenty no other run claims — and confirmed independently by the `inst*` runs
below, which name `A4`, `B5`, `B7` and `C6` one per site.

Which **site** a wire belongs to, from the four one-instance-at-a-time runs:

| run | wires | bits, in `SELFORCE, CLKSEL0..3` order |
|---|---|---|
| `inst0` | `C3 C4 B4 A4 D3` | one of each |
| `inst1` | `A6 A7 D6 C6 B6` | one of each |
| `inst2` | `D7 B3 D1 B7 C7` | one of each |
| `inst3` | `D4 D5 C5 B5 A5` | one of each |

`inst1`/`inst2`/`inst3` name exactly five wires. `inst0` names eight — its own
five plus `A5`, `A6`, `A7`, which the other runs claim; its five are the five
no other `inst*` run claims, and they are one per bit, as every clean run is.

The four groups are disjoint and exhaust the twenty; each is one wire per
signal. Nothing is inferred twice: bit identity comes from the `sel*`/`force`
axis and site identity from the `inst*` axis, and the two agree on all twenty.

## 5. Which site is which DCS — two independent sweeps agree

`inst0..3` are the design's `g[0..3]`, not chipdb sites. The `n{1..4}con`
sweep programs the DCS input multiplexers in a strictly growing order as
instances are added:

```
n1con  P26
n2con  P26 P27
n3con  P26 P27 P36
n4con  P26 P27 P36 P37
```

so `g[i]` takes the `i`-th of `P26, P27, P36, P37` — that is, `(54, 93)` idx 0
and 1 (`SPINE14`/`SPINE15`, quadrant 1) then `(54, 88)` idx 0 and 1
(`SPINE22`/`SPINE23`, quadrant 2), which is the order `fse_create_dcs` builds
them in.

The `n{1..3}dyn` control-wire diffs confirm it without using that argument:

| run | DCS programmed | control wires driven | matches |
|---|---|---|---|
| `n1dyn` | `P26`, `P37` | `A4 A5 B4 B5 C3 C4 C5 D3 D5` | `inst0` ∪ `inst3` |
| `n2dyn` | `P26`, `P27` | `A4 A6 A7 B4 B6 C3 C4 D3` | `inst0` ∪ `inst1` |
| `n3dyn` | `P26`, `P27`, `P36` | + `B3 C7 D1 D7` | + `inst2` |

`n1dyn` is the sharpest: the vendor implemented one logical DCS on **two**
hardware DCS (`P26` and `P37`) — the case `nextpnr`'s `route_dcs_net` already
knows about — and drove exactly `inst0`'s and `inst3`'s wire groups. So
`inst0` is `P26` and `inst3` is `P37`, independently of the `con` ordering.

Resulting table, as `chipdb.gw5ast138c_dcs_inputs`
(`{(quadrant, dcs_idx): [(col, wire), ...]}`, row 54, `SELFORCE` first then
`CLKSEL[0..3]`):

| quadrant, idx | cell | ports | `SELFORCE` | `CLKSEL0` | `CLKSEL1` | `CLKSEL2` | `CLKSEL3` |
|---|---|---|---|---|---|---|---|
| 1, 0 | (54, 93) | `P26*`, `SPINE14` | `C3` | `C4` | `B4` | `A4` | `D3` |
| 1, 1 | (54, 93) | `P27*`, `SPINE15` | `A6` | `A7` | `D6` | `C6` | `B6` |
| 2, 0 | (54, 88) | `P36*`, `SPINE22` | `D7` | `B3` | `D1` | `B7` | `C7` |
| 2, 1 | (54, 88) | `P37*`, `SPINE23` | `D4` | `D5` | `C5` | `B5` | `A5` |

There is no arrangement to it, which is what upstream's own comment on the
25A table says of that die too.

## 6. What changed in the model

`apycula/chipdb.py`:

* `gw5ast138c_dcs_inputs` — the table above, in the same
  `{(quadrant, dcs_idx): [(col, wire), ...]}` shape `gw5_dcs_inputs` uses for
  the 25A;
* `_dcs_input_tables = {device: (row, table)}` — the branch in
  `fse_create_dcs` that used to read `if device in {'GW5A-25A'}` and compare
  against a literal `row == 18` now takes the die's own row and table, so a
  third traced die is a table entry rather than another branch;
* `GW5AST-138C` joins `_dcs_control_wires_traced`, which is what
  `gowin_pack.reject_untraced_dcs_control` reads (`D30`).

`gowin_pack` and `nextpnr` needed **no** source change: the twenty wires are
ordinary pip destinations with ordinary pip fuses, and the DCS bel pins reach
them through the same `DCS_I` alias nodes the 25A already used. The chipdb
gains 20 nodes; `gowin_arch_gen` consumes them, so the `.bin` moves too
(unlike `A14`'s case, where it did not).

## 7. Verdict

```
BATCH_COMPLETE p1f5-dcs runs=3 ok=3 diff=0 aborted=0
BATCH_SKIPPED  batch=p1f5-dcs n=0 refused=0
```

All three `clocking_dcs` sweep points — `q1`, `q2` and `sel4`, the one whose
four `CLKIN` carry four different clocks and whose `CLKSEL`/`SELFORCE` are
driven from a fabric shift register — through the open flow:

| point | verdict | level | `DIFF_COUNT` | `RESIDUAL_UNEXPLAINED` | decode |
|---|---|---|---|---|---|
| `q1` | `ok` | `E0` | cells 0, attrs 0, conns 0 | 0 entries, 0 bits | `c1=ok c2=ok` |
| `q2` | `ok` | `E0` | cells 0, attrs 0, conns 0 | 0 entries, 0 bits | `c1=ok c2=ok` |
| `sel4` | `ok` | `E0` | cells 0, attrs 0, conns 0 | 0 entries, 0 bits | `c1=ok c2=ok` |

`E1` is not reachable for this shape and never was: it pins no CLS placement,
so there is no `INS_LOC` for `E1` to assert and the level falls back to `E0`
(the same reason `P1.F2` recorded, `EC9`).

**The equivalence ladder is not the argument this time.** `A12` was right that
`E0`/`E1` mask routing (`D32`), so an `E0 ok` alone cannot say the control
fuses are right. The direct check is a **pip-level comparison of the two
bitstreams at cell `(54, 89)`**, on `q1`:

| | wires driven from real routing | wires left at their constant |
|---|---|---|
| vendor `run.fs` | `A4 B4 C3 C4 D3` | the other fifteen |
| open `top.fs` | `A4 B4 C3 C4 D3` | the other fifteen, same constants |

The open flow picked the same DCS site and drove the same five control wires
as the vendor. The sources differ, because the two routers take different
paths to the same sink — which is what `D32` says is not a verdict term. This
is the check `A12` said the ladder could not make, made.

Pair these rows were produced with: `apycula/GW5AST-138C.msgpack.xz`
`100ffd8e…`, `chipdb-GW5AST-138C.bin` `43bea88d…` (the twenty `DCS_I` alias
nodes move it — `gowin_arch_gen` consumes them, unlike `A14`'s keys),
`nextpnr-himbaechel` `f029437e…` unchanged (no constids change, no source
change).

Runs: 18 attribution (`p1f5-dcsctl`) + 3 (`p1f5-dcs`) = **21**, cumulative
**269 / 290**. The task's own budget was 14 — 7 over. The overrun is the two extra
disambiguation axes (`n{1..4}` and `inst0..3`, 12 runs) that the first six
showed were needed, because the four DCS could not be told apart from the
per-bit runs alone.

## 8. Still open

* `PCLK*` as a DCS **clock input** source is still driverless
  (`input-side-138c.md` §6). Unchanged by this row: no `S9` clause names it
  and no bitstream in any campaign selects it.
* `nextpnr` still reports `DCS: 5/4 125%` on a one-DCS design — a
  bel-accounting defect present identically since `P1.T31`, not a placement
  one.
