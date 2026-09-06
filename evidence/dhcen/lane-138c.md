# GW5AST-138C `DHCE` — the lane, the gate, and the open flow (P1.T27)

`P1.T26` measured *which bit* a DHCE sets, by an allocation-order sweep inside
one block. It could not say whether that index is the vendor's allocation
order or the **lane** the gated clock is on, and it left the open flow unable
to set the bit at all (`P1.T38b`'s finding). `P1.T27` settles both.

## 1. Root cause of the open-flow gap

`chipdb.gw5a_dhce_gate_pip` recorded, as the site's `pip`, the table-48 input
multiplexer whose enable fuse the site sets — block 5 lane 0 is
`HCLK_UNK999 <= HCLK_UNK1003`. nextpnr resolves a hardware DHCE by walking the
*routed* clock path and comparing each pip's destination wire against that
recorded one (`globals.cc route_dhcen_net` → `gowin_utils.cc
get_dhcen_bel`). That multiplexer's three sources (`HCLK_UNK1003`,
`HCLK_UNK1007`, `HCLK_UNK985`) are **dangling**: nothing in the modelled
fabric drives them, so no route ever reaches `HCLK_UNK999`, `get_dhcen_bel`
always returned `BelId()`, `DHCEN_USED` was never set and
`GW5AST_138C.get_DHCEN_fuses` emitted nothing. The vendor's own `1007` is not
a different mechanism: `1003` and `1007` carry the *same* fuse `(21, 7)`, so
which of the two `gowin_unpack` names is an artefact of the decode, not a
choice the open flow has to reproduce.

Fix: the entry now carries **two** wires — `pip`, the lane's own entry
multiplexer `HCLK_MUX_BETA<block><lane>`, which every clock entering that lane
is routed over and which nextpnr matches; and `gate`, the input multiplexer
whose shared fuse `gowin_pack` writes. One is a route handle, the other a
fuse; conflating them was the defect.

## 2. Site index is lane index — six vendor compiles

Batch `p1t27-dhce-lane` (5 runs, driver `gate_probe.py`, log
`../_runs/p1t27-dhce-lane.log`, `BATCH_COMPLETE ... runs=5 ok=5 diff=0
aborted=0`) plus the `p1t38b-e2e` compile of the same design on block 5 lane 0.
Each is a single `DHCE` gating a single `CLKDIV` pinned to one lane by
`INS_LOC`; the measurement is which of the block's four gate fuses the vendor
sets.

| point | block cell | lane | vendor sets | model's site | lit lane mux |
|---|---|---|---|---|---|
| `b5l0` | (108,117) | 0 | `(21, 7)` | 0 | `HCLK_MUX_BETA50 <= L2HCLK50` |
| `b5l1` | (108,117) | 1 | `(20, 31)` | 1 | `HCLK_MUX_BETA51 <= L2HCLK51` |
| `b5l2` | (108,117) | 2 | `(20, 94)` | 2 | `HCLK_MUX_BETA52 <= L2HCLK52` |
| `b5l3` | (108,117) | 3 | `(20, 50)` | 3 | `HCLK_MUX_BETA53 <= L2HCLK53` |
| `b4l0` | (108,64) | 0 | `(20, 2)` | 0 | `HCLK_MUX_BETA40 <= L2HCLK40` |
| `b4l2` | (108,64) | 2 | `(21, 32)` | 2 | `HCLK_MUX_BETA42 <= L2HCLK42` |

Six for six, in two blocks, and the control (`p1t38b-e2e2`, the same design
with no `DHCE`) sets **none** of the four. `(20, 2)` and `(21, 32)` are
`P1.T26`'s own block-4 numbers, so the two methods agree where they meet.

## 3. A refuted assumption found on the way — `CLKDIV.RESETN`

`_gw5a_hclk_ctrl_wires['GW5AST-138C']` was ASSUMED equal to the GW5A-25A, and
its own comment named the run that would promote it. These six compiles are
that run, decoded for every ordinary tile pip of the block cell:

* `clkdiv_calib` = `B6 B7 C0 C1` — **confirmed**;
* `clkdiv_resetn` = **`D4 D5 D6 D7`**, not `C4 C5 C6 C7` — **refuted**.

Not harmless: `C5` and `C7` are the `CEN` wires of DHCE sites 1 and 2, so the
wrong table put two bel pins on one wire and nextpnr refused a design holding
both a `CLKDIV` and a `DHCE` on those lanes with `ERROR: Found two arcs with
same sink wire X117Y108/C5`. Fixed on the spot, with
`test_clkdiv_control_wires_do_not_collide_with_dhce_cen_138c` as the guard
that was missing. `clkdiv2_resetn` stays ASSUMED — no `CLKDIV2` point here.

## 4. The open flow — `E1`, batch `p1t27-dhce-e1b`

Shape `clocking_dhce`, scope the block-5 cell, `BATCH_COMPLETE p1t27-dhce-e1b
runs=4 ok=3 diff=0 aborted=1`.

| run | lane | verdict | cells | attrs | conns | unexplained | decode |
|---|---|---|---|---|---|---|---|
| `…-0000` | 0 | **ok** | 0 | 0 | 0 | **none** | c1 ok, c2 ok |
| `…-0001` | 1 | **ok** | 0 | 0 | 0 | **none** | c1 ok, c2 ok |
| `…-0002` | 2 | **ok** | 0 | 0 | 0 | **none** | c1 ok, c2 ok |
| `…-0003` | 3 | aborted | — | — | — | — | — |

`$PACKER_DHCEN_21` at `X117Y108/DHCEN0` now carries `DHCEN_USED`, its `CE` is
the design's `cen` net routed to `X117Y108/C2` — the vendor's own wire, over
the vendor's own pips — and the gate fuse lands in the block cell.

## 5. The lane-3 gap, measured rather than asserted

Lane 3 fails in nextpnr with `Failed to route net 'gated_clk' … using
dedicated routing` / `Can't route the gated_clk network`. It is **not** the
DHCE model: the identical design with the `DHCE` removed (control
`batch/p1t27-nodhce-l3`, open flow only, no oracle cost) routes and packs,
exit 0. The difference is the entry wire. `gw5_make_hclk_pips` joins a block's
four logic→HCLK entries to `CLK0, CLK1, CLK2, LSR2`: lane 3's entry is an
ordinary fabric wire, so a clock reaches it over fabric, and
`route_dhcen_net` rejects a DHCE-managed net that is not routed on global
resources end to end (`ROUTED_PARTIALLY` → `log_error`). The vendor does the
same thing the control does — `b5l3`'s bitstream lights `LSR2 <= W212`, no
`CLK*`/`GB*` pip — so this is nextpnr policy meeting a real asymmetry of the
hardware, not a missing wire. The lane-3 **fuse** is measured all the same
(§2), so the model is complete for all four lanes; only the open flow's E1
point for lane 3 is out of reach, and relaxing that policy is an upstream
trade this task does not make.

## 6. Artefacts

- `gate_probe.py` — the five-run vendor driver; `oracle-runs.jsonl` its ledger
- `fuse-138c.md` / `.json` — `P1.T26`'s gate-fuse attribution, unchanged
- `runs.jsonl` — the four `clocking_dhce` rows appended by `p1t27-dhce-e1b`
- `../_runs/p1t27-dhce-lane.{log,watchdog.log}`,
  `../_runs/p1t27-dhce-e1b.{log,watchdog.log}`
- shape `fuzz/gw5ast138c/shapes/clocking_dhce.py`; tests
  `tests/test_gw5ast138c_dhce.py` (apicula) and `tools/tests/test_dhcen_row.py`
- chipdb `GW5AST-138C.msgpack.xz` sha256 `64c4bfac…`, nextpnr
  `chipdb-GW5AST-138C.bin` sha256 `2a741df7…`, installed as a pair
