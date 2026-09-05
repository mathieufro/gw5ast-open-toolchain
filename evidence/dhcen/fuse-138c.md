# GW5AST-138C `DHCE` — fuses, bels and the open flow (P1.T26)

Task: `blueprints/P1-clocking.md` P1.T26 (read as `DHCE` per `D97`). Device
`GW5AST-138C`, part `GW5AST-LV138PG484AC1/I0`, `device_version C`. Oracle:
Gowin IDE **1.9.12.03 Standard, licensed** (`edu-provisional: false`).
`P1.T25` measured *where* the 24 sites are and which wire is `CEN`; this task
measures what a site *does to the bitstream*, and implements it.

Machine-readable twin: `fuse-138c.json`, rebuilt by `build_fuse_table.py`.

## 1. What a DHCE actually sets

**One fuse, in its own HCLK block cell.** Not an `HCLK` shortval attribute —
the pre-5A model (`gowin_pack.get_DHCEN_fuses`) keys on `HSB*MUX*_HSTOP` /
`BRGMUX*_BRGSTOP` attributes, and on this device those attributes have no
`(attr, val)` entry in `logicinfo['HCLK']` at all, so that path emits the empty
set for every site. What a DHCE sets is the **output-enable fuse of the HCLK
input multiplexer it sits on**: the one fuse that all three of that
multiplexer's sources have in common.

Each HCLK block has exactly four such multiplexers, at local table-48
destination ids `64..67` (i.e. `wnames.hclknames[64 + idx + hclk_idx * 187]`,
`187` being `gw5_hclk_wire_offset`), which on the six blocks are

| block | side | multiplexer destinations |
|---|---|---|
| (27, 0) | L | `HCLK_UNK64 65 66 67` |
| (27, 181) | R | `HCLK_UNK251 252 253 254` |
| (81, 0) | L | `HCLK_UNK438 439 440 441` |
| (81, 181) | R | `HCLK_UNK625 626 627 628` |
| (108, 64) | B | `HCLK_UNK812 813 814 815` |
| (108, 117) | B | `HCLK_UNK999`, `HCLKMUX0`, `LWSPINETL0`, `LWSPINETL1` |

Every one of the 24 is a three-source multiplexer whose source fuse sets share
exactly one fuse — the check `test_dhce_gate_fuses_match_the_vendor_138c` makes
that assertion for all six blocks, not just the measured one.

## 2. Method — four vendor compiles

Batch `p1-dhce-fuse`, driver `fuse_probe.py`, log `../_runs/p1-dhce-fuse.log`
(`BATCH_COMPLETE p1-dhce-fuse runs=4 ok=4 diff=0 aborted=0`), watchdog
`../_runs/p1-dhce-fuse.watchdog.log` (`WATCHDOG_ARMED` … `WATCHDOG_COMPLETE`).

`n_div = 4` and `tie_resetn` held constant, `n_dhce = 0, 1, 2, 3`. All four
`CLKDIV` land in the first-filled block `(108, 64)` (`P1.T25` §3.2), so the
only difference between adjacent points is one more DHCE, and the moved fuses
of that block tile are that DHCE's.

| step | site idx | multiplexer | vendor's moved gate bit | model predicts | `DIFF_COUNT` | residual bits | unattributed |
|---|---|---|---|---|---|---|---|
| n=0→1 | 0 | `HCLK_UNK812` | `(20, 2)` | `(20, 2)` | **0** | 6 (`C2`, `E130` pips) | **0** |
| n=1→2 | 1 | `HCLK_UNK813` | `(20, 48)` | `(20, 48)` | **0** | 10 (`C5`, `S260`, `X05` pips) | **0** |
| n=2→3 | 2 | `HCLK_UNK814` | `(21, 32)` | `(21, 32)` | **0** | 2 (`C7` pips) | **0** |

`RESIDUAL` is 18 bits over the three steps and **every one of them is an
ordinary CIB pip fuse of the enable net** — the pips whose destination is that
site's own `CEN` wire (`C2`, `C5`, `C7`) plus the two hops feeding it. Those
are emitted by apicula's normal pip path, not by the DHCE model, which is why
they are residual here and not a defect. `build_fuse_table.py` re-derives the
attribution, so `unattributed = 0` is checkable, not asserted.

Site **3** is not in the sweep (the four-run budget bought three increments and
the `n=0` baseline). Its fuse is the same-shaped gate bit of the block's fourth
multiplexer, `(20, 99)` for `HCLK_UNK815` — **derived, not measured**, and
flagged `site3_measured: false` in `fuse-138c.json`.

Two things this also settles, both of which `P1.T25` could only hypothesise:

* the vendor's **allocation order inside a block is the multiplexer order** —
  `idx` really is `HCLK_IN{idx}`, because the n-th DHCE lights the n-th
  multiplexer's gate bit and nothing else;
* the four measured `CEN` wires of a block correspond one-for-one to those four
  multiplexers, in the same order.

## 3. What was implemented

**apicula** (`clocking/dhcen-gw5a`):

* `chipdb.py` `_dhcen_ce['GW5AST-138C']` — `P1.T25`'s table, eight entries on
  each of `L`/`R`/`B`, no `'T'`, no interbank entries.
* `chipdb.py` `gw5a_create_dhce` / `gw5a_dhce_gate_pip` / `gw5a_dhce_gate_fuses`
  — four sites per HCLK block cell, each carrying the **real** multiplexer pip
  it gates, so the nextpnr wire→bel map resolves and the fuse is derivable from
  the chipdb alone. `fse_create_dhcen` keeps its early return (and its
  `No DHCEN for {device} for now.` line) for every device with no table.
* `gowin_pack.py` `ChipDB.is_gw5a_dhcen` / `ChipDB.get_gw5a_dhce_gate_fuses`
  and `GW5AST_138C.get_DHCEN_fuses` — emits the gate fuse **in the block cell
  only**. The pre-5A override sweeps a whole die edge, which is right when a
  side has one HCLK block and wrong here: this die has two blocks on each of
  `L`, `R` and `B`, and an edge sweep would gate the neighbour as well.

**nextpnr** (`clocking/dhcen-gw5a`, branched from `clocking/gw5a-hclk-6block`
because the DHCE bels sit on the six-block HCLK network that branch builds):

* `constids.inc` — `X(DHCE)`, `X(CEN)` appended. **Appending constids
  invalidates every older chipdb `.bin`**; the `.bin` below was regenerated
  with this binary.
* `pack.cc` `pack_dhcens` — renames `DHCE`→`DHCEN` and its port `CEN`→`CE`
  before the existing packer runs, so the bel, the packer and
  `globals.cc::route_dhcen_net` stay spelling-agnostic instead of growing a
  second cell type. No other C++ file changed.

## 4. Open flow — how far it gets, and where it stops

`yosys` 0.63 accepts `DHCE` unchanged: `gowin/cells_xtra_gw5a.v` already
declares `module DHCE(CLKIN, CEN, CLKOUT)`, so `synth_gowin -family gw5a`
keeps it (`1 DHCE`, `4 CLKDIV` in the cell report). No blackbox stub needed.

`nextpnr-himbaechel` loads the rebuilt chipdb with **0 errors** and reports a
non-empty DHCEN bel bucket — `DHCEN: 25/24 104%` in the utilisation table: the
24 hardware bels `pack_dhcens` binds, plus the design's own pseudo cell. Every
one of them is placed in an HCLK block cell.

It then **fails to route**:

```
Warning: Failed to route net 'hclk[0]' from X91Y108/CLK1 to X64Y108/CLKDIV_I43 using dedicated routing.
ERROR: Can't route the hclk[0] network.
```

That is **not** the DHCE. The DHCE-free control — the same design at
`n_dhce = 0`, four `CLKDIV` driven straight from the pin — fails in the same
place for the same reason:

```
Warning: Failed to route net 'div[3]' from X64Y108/CLKDIV_O40 to X55Y107/A1 using dedicated routing.
ERROR: Routing design failed.
```

This is the already-recorded `D98` / `P1.T11` gap: `clknames_5ast138c` defines
none of the 16 `{T,B,R,L}BDHCLK{0..3}` backbone names, so no HCLK net can be
routed on this device yet (`P1.T08c`). Consequently **no open `.fs` exists for
any CLKDIV/DHCE design**, and a whole-design `E0` is not computable — which is
why §2's `E0` is scoped to the block tile and to the DHCE-attributable bits,
and says so. That is a dependency, not a defect in this row: the model is
proved against the vendor bitstream bit-for-bit where it has anything to say.

Not re-checked here: `gowin_unpack` decodes no CLKDIV/HCLK cell on this device
(`D98`), so a netlist-level decode of a DHCE is still absent — the same
`P1.T16`-prereq that `P1.T11` recorded.

## 5. Downstream fact (UG306E p.19)

A `DHCE` may drive `DQS.FCLK`, `CLKDIV.HCLKIN` and `DDRDLL.CLKIN`. The first
and third are Phase 5b dependencies; only the second is exercised here.

## 6. Artefacts and reproduction

* `fuse_probe.py` — the four-compile driver
* `build_fuse_table.py` — the deterministic reduction to `fuse-138c.json`
* `../_runs/p1-dhce-fuse.{log,watchdog.log,stdout.log}`
* `oracle-runs.jsonl` — raw per-run ledger; `runs.jsonl` — the four evidence rows
* chipdb `GW5AST-138C.msgpack.xz` `3b275d4f312cfcc09e1b5dcdb5ffb74536f0c619f75154c29fa70d1f04008294`
  (25A unchanged at `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca`)
* nextpnr chipdb `chipdb-GW5AST-138C.bin`
  `15869ffb926b8f976af40bd1ddf25dc039e4840f6d0ddf1cf08df7a586e0d4c2` — pairs
  with the binary built from `clocking/dhcen-gw5a`, **not** with the installed
  one (the installed `nextpnr-himbaechel` was deliberately not replaced; it
  must be reinstalled together with this `.bin` when the branch lands)
* Tests: `tests/test_gw5ast138c_dhce.py` (8 tests) on apicula
  `clocking/dhcen-gw5a`

```sh
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
cd <apicula worktree on clocking/dhcen-gw5a>
PYTHONPATH=$PWD python $OTC/evidence/dhcen/fuse_probe.py \
    --out-root $DATASTORE/clocking/dhcen/fuse \
    --log $OTC/evidence/_runs/p1-dhce-fuse.log \
    --ledger $OTC/evidence/dhcen/oracle-runs.jsonl \
    --budget $OTC/evidence/_budget/clocking-runs.tsv \
    --pidfile $OTC/evidence/_runs/p1-dhce-fuse.pid --points 0,1,2,3 --n-div 4
PYTHONPATH=$PWD python $OTC/evidence/dhcen/build_fuse_table.py
```

## 7. Budget

**4 oracle runs** (dispatch cap 4), cumulative 45. Booked to
`../_budget/clocking-runs.tsv` as one batch row.
