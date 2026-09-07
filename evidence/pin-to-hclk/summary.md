# pin → HCLK routing on GW5AST-138C (`P3.T07`, `P3.T08`)

Rows: `runs.jsonl` (14). Batch log: `evidence/_runs/p3-pin-to-hclk.log`.
Sweep tool: `sweep_pin_hclk.py` beside this file. Shape: the HCLK probe of
`fuzz/gw5ast138c/shapes/io_basic.py` on branch `prim/io-iologic-138c`.
Oracle: Gowin Standard 1.9.12.03, part `GW5AST-LV138PG484AC1/I0`,
`device_version C`, `edu-provisional: false`. Chipdb `9cce739d` (`.bin`) /
`6a776c74` (`.msgpack.xz`), nextpnr binary `454714cc`.

## DISPATCH-STATE

`FOUND: (2) — Phase 1 had already routed 138C into the guard.` Recorded in
full by `P3.T06` at `evidence/iologic/pin-hclk-138c.md`; repeated here because
the blueprint asks this file to carry it. `apycula/chipdb.py:2326` reads
`if device in {'GW5A-25A', 'GW5AST-138C'}:` and `:2327` already calls
`gw5_make_pin_to_hclk(dev, device)`, so the blueprint's escape clause applies
and no dispatch line was touched by Phase 3.

## HCLK-CAPABLE PINS

All twelve candidates reach the HCLK network. `block`/`lane` are decoded from
the vendor bitstream's `HCLK` bel (`HCLK_MUX_BETA<block><lane>=<source>`)
paired with the `CLKDIV_` bel whose `DIV_MODE` names the clock.

| ball | bank | vendor CFG role | block | lane | entry wire | verdict |
|---|---|---|---|---|---|---|
| `V19` | 4 | `SGCLKC_4` | 4 | 0 | `L2HCLK40` | reaches |
| `W20` | 4 | `MGCLKC_5` | 4 | 0 | `L2HCLK40` | reaches |
| `P20` | 4 | — | 4 | 0 | `L2HCLK40` | reaches |
| `V22` | 4 | `EMCCLK` (board clock) | 5 | 0 | `L2HCLK50` | reaches |
| `N15` | 4 | — | 5 | 0 | `L2HCLK50` | reaches |
| `F20` | 2 | — (`RGMII_GTXCLK`) | 1 | 0 | `L2HCLK10` | reaches |
| `D21` | 2 | — (`RGMII_TXD[0]`) | 1 | 0 | `L2HCLK10` | reaches |
| `F21` | 2 | — (`RGMII_TXEN`) | 1 | 0 | `L2HCLK10` | reaches |
| `Y17` | 5 | — | 4 | 1 | `L2HCLK41` | reaches |
| `W14` | 5 | — | 4 | 1 | `L2HCLK41` | reaches |
| `AA9` | 5 | — | 4 | 1 | `L2HCLK41` | reaches |
| `G15` | 3 | — (HDMI pair, single-ended) | 3 | 0 | `L2HCLK30` | reaches |

`S10`'s row criterion — *"at least one non-dedicated bank-2 pin proven to reach
FCLK, or the set of HCLK-capable pins enumerated with oracle evidence"* — is
met on **both** halves: `D21` and `F21` are ordinary bank-2 dock pins with no
clock role in the vendor pinout, and the enumerated set is the table above.

## The finding: the block is not a property of the ball

Every one of the twelve entered on `L2HCLK<block><lane>` — the **logic entry**
off the global clock plane, the same wire class `P1.F3` measured for the
PLL→HCLK path (`HCLK_MUX_BETA50 <= L2HCLK50`). None used a dedicated pin→HCLK
edge.

Two controls settle what the sweep alone cannot. A ball landing on a block
when nothing constrains it is a placer preference; the question is whether it
*could* have gone elsewhere.

| run | ball | edge of ball | pinned to | resulting block | routes |
|---|---|---|---|---|---|
| `ctl-v22-rightside` | `V22` | bottom (bank 4) | `RIGHTSIDE[4]` | 3 (right edge) | yes |
| `ctl-f20-bottomside` | `F20` | right (bank 2) | `BOTTOMSIDE[4]` | 5 (bottom edge) | yes |

Both route, in both directions. So **`P3.T06`'s `NEAREST_BLOCK_ON_SIDE`
hypothesis is refuted**: the block a ball's clock lands on is chosen by the
placer over the global clock plane, not fixed by the ball. `bank 4 → block 5`
was the assumed row and it is only half right — bank-4 balls landed on block 4
and on block 5 in the same sweep, whichever lane was free.

`evidence/iologic/pin-hclk-138c.json` now records this: `block_rule` is
`MEASURED_NOT_PIN_DETERMINED`, the twelve measured balls carry
`hclk_block_source: MEASURED` with their run id, every other ball carries
`NOT_PIN_DETERMINED` instead of a guess, and no cell of the artefact reads
`ASSUMED` any more. The old rule survives as `nearest_block_on_side`, a
geometry column, and the two corroborations still hold of it.

**`pin_to_hclk_entries` stays empty, now for a measured reason.**
`chipdb._gw5_pin_to_hclk` entries model a *dedicated* pin→HCLK edge. No
candidate uses one, so an entry here would add a routing edge the silicon does
not have. The 25A entry is untouched.

## Blocks 0 and 2: not measured, and why

The only balls the bank→block geometry places on blocks 0 and 2 are in banks 7
and 6 — the DDR3 banks, where no Phase-3 shape may put a pin (`D20c`, `D54`,
`_io_base.SAFE_PINS`). Stated, not silently omitted.

## The instrument, and the three designs that measured nothing

Recorded because each is a run that was spent, and because the next person
reaching for the obvious design should know it is empty:

1. **`IDDR` clocked from the ball.** Places, routes, returns 0 — and the
   vendor puts the clock on an ordinary global (`CLK0 <= GB10` at the IOLOGIC
   tile, zero HCLK bels lit anywhere on the die). It proves nothing about HCLK.
2. **`IDDR` + an unpinned `CLKDIV` on the same ball.** `WARN (PR1014) Generic
   routing resource will be used to clock signal 'clk_d'`, still zero HCLK
   bels — on `V22`, on `V19` (`SGCLKC_4`) and on `W20` (`MGCLKC_5`) alike.
   `HCLKIN` alone does not force the entry.
3. **`DHCE` → `IDDR` directly.** `ERROR (CK2060) : The connection between
   instance 'gate0' and instance 'dut' is incorrect`.

The instrument that works is `DHCE` → `CLKDIV` (the `DHCE` output *is* an
HCLK, so the entry mux must fire) with an `IDES4` beside it whose `FCLK` is
that same HCLK — `IDES4` has a declared fast-clock port and accepts it where
`IDDR` does not.

A fourth design defect was found and fixed on the way: the landed `io_basic`
`IDDR` point put a fabric flop between the pad and the gearbox, which
GowinSynthesis refuses outright (`ERROR (CK0013) : Instance 'dut' is not
connected to buffer or IODELAY by wire 'din_r'`). `P3.T11`/`P3.T12` would have
hit it on their first run.

## Why the row closes at E0 and not E1 (`EC9`)

`P3.T08` re-ran all five designs through the open flow — no new oracle runs —
and none of them builds:

```
ERROR: It was not possible to completely route the hclk net using only global
resources. This is not allowed for dhcen managed networks.
Info: net 'hclk': no dedicated path to dut.FCLK (bel X82Y108/IOLOGICAI,
      wire X82Y108/FCLKA)
Info:   X82Y108/FCLKA is an IOLOGIC fast-clock pin; this device's database
        carries no HCLK entry for it, so no clock network reaches it
```

nextpnr routes the DHCE-gated HCLK to the `CLKDIV` and stops at the IOLOGIC
fast-clock pin, because **the 138C database has no HCLK → FCLK edge at all**:
`dev.io2hclk == {}` for this device and `chipdb.gw5_create_hclk_iol_pip`
returns `False` for it. There is no open bitstream to compare the vendor's
with, so every row is a vendor measurement at `E0`, and each row says so in
its own `notes` rather than deferring to this file.

The vendor does not use that edge either: **zero** pips into any `FCLK*` wire
decode in any of the twelve bitstreams. Whether the IOLOGIC fast-clock mux is
fuseless on this die or simply unmodelled is not decided by this row.

## Named gap, with an owner

**`G-FCLK-138C` — the HCLK → IOLOGIC-FCLK edge is absent from the 138C model.**
Closing it means building `dev.io2hclk` for this device, which is
`apycula/chipdb.py`'s `gw5_create_hclk_iol_pip` — **not** a Phase-3-owned
function (`P3-io-iologic.md` "Frozen"), and it needs its own attribution
campaign because no vendor bitstream this task produced lights a fuse there.
Until it lands, a board-clocked IOLOGIC on this die is clocked from the global
clock plane, by the vendor and by nextpnr alike.

Owner: this is the second of the two `impl/gestalt-p2.md` `D5` items the
blueprint says "whoever picks up Phase 3's HCLK tasks" must name before Phase 3
closes. Named here: it belongs with **Phase 5b**, the phase that owns the
`_MEM` IOLOGIC and `DQS` paths and is the first consumer that cannot work
around it.

## Budget

12 oracle runs, exactly `P3.T07`'s allocation
(`evidence/_budget/iologic-runs.tsv`). Seven of them found the instrument (the
three empty designs above and the `CK0013`/`CK2060` refusals); five made the
measurement. `P3.T08` spent none.
