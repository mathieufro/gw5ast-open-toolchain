# `evidence/clocking/` — the Phase 1 integration E2E on the GW5AST-138C (`P1.T38b`)

## Row

`blueprints/P1-clocking.md` §E2E, run against the **merged** pair: apicula
`integration/p1-clocking` and nextpnr `integration/p1-clocking`, both carrying
every `clocking/*` branch of the phase. Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`, oracle Gowin EDA **1.9.12.03
Standard** (licensed — no `edu-provisional` row here).

One design, built twice — once by the vendor oracle, once by the open flow —
and compared at `E1` with placement identity. It is not one of the per-row
sweeps: each of those isolates one primitive on one lane, this one asserts
that the six-block model, the lane mapping and the divider fuses still agree
when two lanes of the same HCLK block are configured **differently in the same
bitstream**.

Shape `fuzz/gw5ast138c/shapes/clocking_e2e.py`, design generated into
`$DATASTORE/batch/p1t38b/e2e2/`:

    clk (V22, board 50 MHz ball) -> HCLK spine
      -> CLKDIV div0  block 5 lane 0  DIV_MODE="4" -> ring_a -> led[1:0]
      -> CLKDIV div2  block 5 lane 2  DIV_MODE="8" -> ring_b -> led[3:2]

Block 5 is `_gw5a_hclk_locs['GW5AST-138C'][5] == (row 108, col 117)`, site
`X117Y108` (`P1.T04`); blocks 0 and 1 are avoided because they have no
modelled clock escape (`D100a`). Both flows are pinned to the same sites —
the vendor by `INS_LOC "div0" BOTTOMSIDE[4]` / `"div2" BOTTOMSIDE[6]`
(SUG1018-1.7E §2.9), the open flow by the RTL `BEL` attribute, because
nextpnr's `.cst` reader cannot parse the 138C's `SIDE[0~7]` spelling
(`P1.T14`, split `top-open.cst`).

## Sweep

None: a single point, `design = two-lane-clkdiv`, **1 oracle run** (batch
`p1t38b-e2e2`), charged to the HCLK/CLKDIV line. The earlier batch
`p1t38b-e2e` is the same task's first attempt and is recorded under
**§ The DHCE finding** below; it cost 1 further oracle run.

| point | level | verdict | cells | attrs | conns | unexplained residual | decode c1/c2 |
|---|---|---|---|---|---|---|---|
| `two-lane-clkdiv` | **E1** | **ok** | 0 | 0 | 0 | 0 | ok/ok |

pips (whole-device statistic, never a verdict term, `D32`): 2020120.

Literal harness output:

```
EQUIV E1 ok
BATCH_COMPLETE p1t38b-e2e2 runs=1 ok=1 diff=0 aborted=0
```

`c1` required 16 fuse-backed placed cells and recovered 16; the five skipped
entries are the usual pseudo-bels (`spine_select$top` unplaced, `PINCFG`,
`GSR`, `$PACKER_VCC_DRV`, `$PACKER_GND_DRV`). `c2` round-tripped the 4 147 478
byte fuse bitmap with `0` differing bytes.

## Verdict

**`E1`, clean on every verdict term** — `cells = 0`, `attrs = 0`, `conns = 0`,
`unexplained_bits` empty, `decode_check` `{c1: ok, c2: ok}`, `0` refused, `0`
aborted. Placement identity comes from the HCLK-bel half of `E1`
(`equiv.level_e1_hclk`): the two `CLKDIV` bels the open flow placed are the
two the vendor's own bitstream decodes to, at the same sites and the same lane
indices. The CLS half is silent, as it is for every CLKDIV design — a CLKDIV
has no CLS address, so there is nothing for it to assert (`P1.T14`).

This is the roadmap's Phase 1 goal stated as one artefact: a real,
open-toolchain clock on the 138C, from an IO ball through a HCLK lane and a
divider onto the global clock network and into fabric, agreeing with the
vendor bit for bit inside the block.

## The DHCE finding (batch `p1t38b-e2e`, `verdict: diff`)

The first version of this design put a `DHCE` gate on the HCLK input mux ahead
of `div0`. It came back `diff` on exactly **one** bit, and the cause is a real
gap in the open flow, measured rather than inferred:

* the vendor's bitstream sets `HCLK_UNK999 = "HCLK_UNK1007"` in the block-5
  HCLK cell; the open bitstream sets nothing there. Device-wide that was the
  **only** difference between the two decoded netlists — `cells = 0`,
  `conns = 0`, `unexplained_bits` empty;
* `gowin_pack.GW5AST_138C.get_DHCEN_fuses` writes the gate only for a cell
  carrying `DHCEN_USED`, which nextpnr's `globals.cc route_dhcen_net` sets by
  matching a wire on the routed path against the `dhcen` pip apicula records.
  For block 5 lane 0 that pip is `HCLK_UNK1003 -> HCLK_UNK999`
  (`db.extra_func[(108,117)]['dhcen'][0]`), a **different source** from the
  `HCLK_UNK1007` the vendor actually selects, and the open route into the
  block never touches that wire at all. So `get_dhcen_bel` returns `BelId()`,
  no placeholder is ever marked, and no fuse is written.

That is `P1.T27`'s row to close (the DHCE sweep and evidence row, not yet
run) — it needs the vendor to be asked which HCLK input mux source the gate
really is, which is a campaign, not a patch. It is recorded here, and the
`clocking_e2e` shape says in its own docstring why no `DHCE` is in the design.

One harness defect **was** in scope and is fixed: `c1` counted nextpnr's 24
`$PACKER_DHCEN_*` placeholders as missing cells. `pack.cc` binds one to every
`DHCEN` bel on the device as soon as a design holds a single `DHCE`, and only
the few `route_dhcen_net` marks write a fuse — so an unmarked placeholder is a
pseudo-cell, and requiring the decode to recover it asserts the absence of a
gate as if it were a missing cell. `c1` now skips them by name; a `DHCE` the
design named keeps its own name and stays required
(`tests/test_packer_dhcen_placeholders.py`).

## Also excluded, each for a measured reason

* **`PLL`** — `P1.T23` recorded four open-flow gaps, one hard:
  `GW5AST_138C.get_pll_pump()` is unimplemented and its constants need their
  own campaign (`../plla/openflow-gap-138c.md`). A PLL here would `ABORT` in
  `gowin_pack` and measure that gap instead of the clock tree.
* **`CLKDIV2`** — cannot drive ordinary fabric (vendor `CK2060`, `P1.T04`) and
  writes no fuse of its own (`P1.T15`, `D103`); `P1.T15` owns that row.
* **`DQCE`/`DCS`** — `P1.T28` derived their 138C tile types from vendor runs,
  but neither has an open-flow bel on this device yet.

## Artefacts

* Row: `runs.jsonl` (this directory), promoted by
  `../clkdiv/promote_rows.py --prune` from
  `$OTC/evidence/_runs/p1t38b-e2e2.rows.jsonl`.
* Batch logs: `$OTC/evidence/_runs/p1t38b-e2e2.log` and its `.watchdog.log`
  sibling; the DHCE attempt is `$OTC/evidence/_runs/p1t38b-e2e.log`.
* Vendor and open bitstreams, `.tr`, `.sdf` and per-step logs: absolute paths
  with sha256 inside the row, under
  `/Users/alex/fine-line-data/open-toolchain-gw5ast/batch/p1t38b/e2e2/`. The
  vendor `run/` tree was pruned to `run.fs`, `run.tr`, `run.vo`, `run.sdf`
  (`D99`), recorded in the row's `notes`.
* The merged pair this ran against: `_runs/p1-integration-2.md`.
