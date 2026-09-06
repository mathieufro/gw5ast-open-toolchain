# `evidence/dhcen/` — GW5AST-138C DHCEN control-pin trace (P1.T25)

## Rows

`28` rows in `runs.jsonl`, one per vendor compile: `26` `ok`, `2` `refused`.
Both refusals are the deliverable, not a hole —
`ERROR (EX3937) : Instantiating unknown module 'DHCEN'` (the primitive does not
exist on this family) and
`ERROR (PA2017) : The number(25) of CLKDIV in the design exceeds the resource
limit(24) of current device` (the capacity). Every row is `level: E0`,
`primitive: DHCEN` (the `spec-primitives.md` row id; the vendor spelling `DHCE` is in `sweep`/`notes`), `shape: clocking_dhcen_trace`; there is no `E0`/`E1`
comparison because there is no open-source side to compare against until
`P1.T26` teaches `fse_create_dhcen` about this device.

## Sweep

`n_dhce` = 0..6, 12, 16..24, 25, in two variants (`tie_resetn` on and off) plus
the `0 DHCE / 24 CLKDIV` control point. `28` oracle runs against the D62 budget
(dispatch cap 30, blueprint estimate 24), booked to
`../_budget/clocking-runs.tsv` as six batch rows.

## Verdict

**MEASURED.** 24 DHCE sites = 6 HCLK block cells x 4, enable wires
`C2 C5 C7 D2` per block except `(81, 0)`, which is `C2 A5 C7 A4`. Two
refutations of the blueprint recorded: the primitive is `DHCE` with port `CEN`
(not `DHCEN`/`CE`), and the table is 6 blocks x 4 with no top side and no
interbank entries (not 4 sides x 6). No `chipdb.py` change was made — that is
`P1.T26`, whose handover list is `trace-138c.md` §8.

## Artefacts

- `ce-wires-138c.md` / `ce-wires-138c.json` — the `(side, idx, row, col, wire)`
  table, and the literal `_dhcen_ce` entry `P1.T26` needs
- `trace-138c.md` — method, the two refutations, the identification argument,
  the fuse->pin table, the evidence rows, reproduction
- `probe_dhce.py` — the campaign driver (oracle runs + the routing trace)
- `build_ce_wires.py` — the deterministic reduction from `trace-result*.json`
  to the committed table
- `oracle-runs.jsonl` — the raw per-run ledger the batches append to
- `trace-result*.json`, `fuse-presence-diff.json` — the two instruments' output
- `../_runs/p1-dhcen-trace-{1..5}.{log,watchdog.log}` — batch and watchdog logs
- Shape: `fuzz/gw5ast138c/shapes/clocking_dhcen_trace.py` on apicula branch
  `clocking/dhcen-gw5a`
- Gate test: `tools/tests/test_dhcen_ce_wires.py`

---

## P1.T26 — DHCE implemented (`fuse-138c.md`)

`4` further oracle runs (batch `p1-dhce-fuse`, cumulative `45`), all `ok`,
`aborted=0`. They attribute the **fuse**: a DHCE sets exactly one bit, the
output-enable of the HCLK input multiplexer it sits on, in its **own block
cell** — not an `HCLK` shortval attribute (this device's `HCLK` table has no
`*_HSTOP`/`*_BRGSTOP` entry at all) and not along a whole die edge (this die
has two blocks per side; an edge sweep would gate the neighbour).

Scoped `E0` — block cell `(108, 64)`, DHCE-attributable bits: **`DIFF_COUNT`
0** for sites `0`, `1`, `2` (model bit == vendor bit), **`RESIDUAL` 18 bits,
`0` unattributed** (all of them ordinary CIB pip fuses of the `CEN` net). Site
`3`'s bit is derived from the same rule, not measured. A whole-design `E0` is
**not computable**: the open flow cannot route a `CLKDIV` net on this device at
all (`D98`/`P1.T11`/`P1.T08c`), which the DHCE-free `n=0` control reproduces.

Open flow: `yosys` accepts `DHCE` unchanged (`cells_xtra_gw5a.v` declares it);
`nextpnr-himbaechel` loads the rebuilt chipdb with `0` errors and reports
`DHCEN: 25/24` — 24 hardware bels placed in the six HCLK blocks plus the design
pseudo cell — then stops at the HCLK routing gap above. It also confirms
`P1.T25`'s open hypothesis: allocation order inside a block **is** the
multiplexer order.

---

## P1.T27 — the gate reaches the bitstream (`lane-138c.md`)

`15` further vendor runs (batches `p1t27-dhce-lane` 5, `p1t27-dhce-e1` 6,
`p1t27-dhce-e1b` 4; cumulative `149`).

**Site index is lane index.** Six single-DHCE compiles across two blocks
(block 5 lanes 0-3, block 4 lanes 0 and 2) each set the gate fuse of the input
multiplexer with the *lane's* index, and the DHCE-free control sets none.
`P1.T26`'s allocation-order sweep could not separate that from the vendor's
fill order; it now is.

**The open flow sets the gate.** Root cause of `P1.T38b`'s finding:
`chipdb` recorded the fuse-bearing multiplexer as the wire nextpnr matches a
routed clock against, and that wire is unreachable — its sources are dangling
in table 48. The entry now carries the lane's own entry multiplexer as `pip`
and the gate multiplexer as `gate`. Batch `p1t27-dhce-e1b`, shape
`clocking_dhce`, scope the block-5 cell:

**`E1`, `cells = 0`, `attrs = 0`, `conns = 0`, `unexplained_bits` empty,
`decode_check {c1: ok, c2: ok}` on lanes 0, 1 and 2** — three rows, `0`
`diff`, `0` refused.

**One refuted assumption, fixed on the spot.** `CLKDIV.RESETN` on this device
is `D4..D7`, not the `C4..C7` carried over from the GW5A-25A; `C5` and `C7`
are DHCE `CEN` wires, so the wrong table made nextpnr refuse any design with
both primitives on those lanes. `CLKDIV.CALIB` (`B6 B7 C0 C1`) is confirmed.

**Lane 3 is a stated gap, not a hole.** Its logic→HCLK entry is the fabric
wire `LSR2`, so a clock reaches it over fabric — the vendor's own `b5l3`
bitstream does exactly that — and `route_dhcen_net` refuses a DHCE-managed net
that is not global end to end. The same design without the `DHCE` routes and
packs (control `batch/p1t27-nodhce-l3`, exit 0), which is what makes this
nextpnr policy rather than a missing wire. Lane 3's fuse is measured all the
same, so the model covers all four lanes.

Of the three UG306E p.19 consumers a DHCE may gate, only `CLKDIV.HCLKIN` is
exercised here; `DQS.FCLK` and `DDRDLL.CLKIN` wait on Phase 5's DDR3 work.
