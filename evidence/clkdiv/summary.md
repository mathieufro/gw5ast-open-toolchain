# `evidence/clkdiv/` — CLKDIV `DIV_MODE` on the GW5AST-138C (`P1.T14`)

## Row

`spec-primitives.md` §1 row **CLKDIV**. Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`, oracle Gowin EDA **1.9.12.03
Standard** (licensed — no `edu-provisional` row here).

The `138C status` cell that row carried before this batch was a survey of the
*starting* state, and it is superseded rather than lost: it read *"bels not
created — depends on `HAS_5A_HCLK`"*. `P1.T09` set `HAS_5A_HCLK`, `P1.T08b`
completed the HCLK pip network, and `P1.T08d` un-filtered the central clock
mux so a CLKDIV output can leave its block; the cell now carries this row's
measured DEL-b status.

Shapes:

* `fuzz/gw5ast138c/shapes/clocking_clkdiv.py` — one `CLKDIV` in **HCLK block 5**
  (`_gw5a_hclk_locs['GW5AST-138C'][5] == (row 108, col 117)`, `P1.T04`), lane 0,
  its `CLKOUT` clocking a 4-bit ring counter driving four LEDs, so the divided
  clock must actually escape the block onto the global clock network.
  **Both flows are pinned to the same site**, which is what makes `E1` mean
  anything here: the vendor by `INS_LOC "div0" BOTTOMSIDE[4];` (SUG1018-1.7E
  §2.9 Table 2-2, and `P1.T08d` measured `BOTTOMSIDE[4..7]` -> block 5), the
  open flow by the RTL `(* BEL = "X117Y108/CLKDIV_0" *)` attribute.
  Blocks 0 and 1 are deliberately avoided — `D100a` records that they share one
  central-mux row and have no modelled clock escape.
* `fuzz/gw5ast138c/shapes/clocking_clkdiv_free.py` — the same design at the
  documented default `DIV_MODE = "2"` with **both** placement pins removed: the
  control that says what the two placers do unprompted. `E0` by construction.

Baseline is that same design at the documented default
(`gowin_pack.GW5A.get_default_clkdiv_divmode() == "2"`), never an empty design
(`spec-harness.md` §7).

## Sweep

`DIV_MODE` over {1, 2, 3, 3.5, 4, 5, 6, 7, 8} — the nine values UG306E p.25
documents and `gowin_pack.GW5A.get_valid_clkdiv_divmodes()` admits — one
parameter varied per run, plus the one placement-free control:
**10 evidence rows from 10 oracle runs** (the nine `DIV_MODE` points,
batch `p1t14-clkdiv-e1`, plus the baseline run at the documented default,
batch `p1t14-clkdiv-base`). The unpinned control `clocking_clkdiv_free`
(batch `p1t14-clkdiv-e0`) is an eleventh run recorded beside them, not
among them — see `## Verdict`.

| sweep point | level | verdict | cells | attrs | conns | unexplained residual | decode c1/c2 |
|---|---|---|---|---|---|---|---|
| `DIV_MODE=1` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=2` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=3` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=3.5` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=4` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=5` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=6` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=7` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=8` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `DIV_MODE=2 (baseline run)` | E1 | **ok** | 0 | 0 | 0 | 0 | ok/ok |

pips (whole-device statistic, never a verdict term, D32): 2020356, 2020356, 2020356, 2020356, 2020356, 2020356, 2020356, 2020356, 2020356, 2020356

### Fuse attribution

`gen_divmode_fuses.py` differences the HCLK block cell `(108, 117)` of each
run's vendor `.fs` against the `DIV_MODE = "2"` run and looks the moved bits up
in that tile type's `shortval['HCLK']` table, mapping the matching rows'
attrvals back through `logicinfo['HCLK']` and `attrids.hclk_attrids` /
`hclk_attrvals` to a name. The attribution is *searched for*, never taken from
`gowin_pack`'s own formula, so its agreement with
`GW5A.get_CLKDIV_fuses` — which asks for `HCLKDIV<lane>_DIV = <div mode>` — is
evidence and not a tautology.

| `DIV_MODE` | bit set in cell (108, 117), ttyp 379 | bit cleared | attributed to | `gowin_pack` predicts | agree |
|---|---|---|---|---|---|
| `1` | `21,15` | `21,51` | `HCLKDIV0_DIV = 1`, `HCLKDIV0_DIV = 2` | `21,15` | **yes** |
| `2` | — (reference point) | — | — (no bit moves) | `21,51` | **yes** |
| `3` | `21,49` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 3` | `21,49` | **yes** |
| `3.5` | `21,13` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 3.5` | `21,13` | **yes** |
| `4` | `21,12` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 4` | `21,12` | **yes** |
| `5` | `21,47` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 5` | `21,47` | **yes** |
| `6` | `21,11` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 6` | `21,11` | **yes** |
| `7` | `21,52` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 7` | `21,52` | **yes** |
| `8` | `21,10` | `21,51` | `HCLKDIV0_DIV = 2`, `HCLKDIV0_DIV = 8` | `21,10` | **yes** |

Full detail: `divmode-fuses-138c.json`.

## Verdict

**`E1` on every one of the ten rows, `cells = 0`, `attrs = 0`, `conns = 0`, no
unexplained residual bit, `c1`/`c2` decode `ok`, `0` refused and `0` aborted.**

`E1` here is not the CLS-bel check: a `CLKDIV` has no CLS address, and MEASURED
on the `P1.T11` vendor run the vendor's own text reports (`run.tr`, `run.rpt.txt`,
`run.p`, `run.pr`, `run.log`) do not contain the string `CLKDIV` anywhere — only
`run.vo` names the instance, with no location. The vendor's **bitstream** does
carry it, because `P1.T08c` taught `gowin_unpack` to decode the 138C HCLK block
cells, so `E1` for this class of bel compares the bel nextpnr placed on against
the cell the vendor's own bitstream decodes to. That is an address, not a name,
so there is no renaming to excuse a mismatch. All ten rows match at
`X117Y108/CLKDIV_0`.

Three further results, each measured rather than assumed:

* **The `DIV_MODE` fuse is one-hot in row 21 of the block cell**, and all nine
  values agree bit-for-bit with what `gowin_pack.GW5A.get_CLKDIV_fuses` predicts
  (table above). The two figures come from different sources — one from
  differencing vendor bitstreams, one from `apicula`'s own tables — so their
  agreement is evidence.
* **Both flows are deterministic on this design.** The baseline run repeats the
  `DIV_MODE = "2"` sweep point as an independent oracle run: the open `top.fs`
  is byte-identical across the two runs, and the vendor `.fs` differs only in
  its `//Created Time:` comment — `0` differing bits in the bitmap.
* **The unpinned control (`clocking_clkdiv_free`, batch `p1t14-clkdiv-e0`)** is
  `E0` with `cells = 2`, `attrs = 4`, `conns = 0`, `first_diff`
  `tile (117,108) bel 0: cell vendor=CLKDIV_ open=<absent>`: told nothing, the
  two placers pick different HCLK blocks. It is `diff` by construction, which is
  exactly why it is recorded as its own batch beside the sweep instead of inside
  the ten rows the verdict is read from. It reproduces `P1.T08d`'s free-placement
  finding on this shape.

Blocks 0 and 1 are still unmeasured (`D100a`): they share one central-mux row,
so this row's claim is scoped to a CLKDIV in a block with a modelled clock
escape, which is what the shape pins.

DEL-b status for the `spec-primitives.md` §1 `CLKDIV` row: **`E1`**.

## Artefacts

* Rows: `runs.jsonl` (this directory), promoted by `promote_rows.py --prune`
  from `$OTC/evidence/_runs/p1t14-clkdiv-e1.rows.jsonl` (the nine pinned sweep
  points) and `$OTC/evidence/_runs/p1t14-clkdiv-base.rows.jsonl` (the baseline
  run). The free control's row stays in
  `$OTC/evidence/_runs/p1t14-clkdiv-e0.rows.jsonl`.
* Batch logs: `$OTC/evidence/_runs/p1t14-clkdiv-{e1,base,e0}.log` and their
  `.watchdog.log` siblings; every one ends in its own `BATCH_COMPLETE` line.
* Fuse attribution: `divmode-fuses-138c.json`, produced by
  `gen_divmode_fuses.py`.
* Vendor and open bitstreams, `.tr`, `.sdf` and per-step logs: absolute paths
  with sha256 inside each row, under
  `/Users/alex/fine-line-data/open-toolchain-gw5ast/batch/p1t14-clkdiv-e1/` and
  `.../p1t14-clkdiv-base/`, `.../p1t14-clkdiv-e0/`. Each row's vendor `run/`
  tree was pruned to `run.fs`, `run.tr`, `run.vo`, `run.sdf` (`D99`), which the
  row's `notes` records.
* Prior CLKDIV placement evidence this row rests on: `../hclk/mux38-138c.md`
  (`P1.T08d`), `../hclk/clkdiv-138c.md` (`P1.T11`), `unpack-138c.md`
  (`P1.T08c`: the unpacker decodes CLKDIV/CLKDIV2/HCLK on the 138C, which is
  what makes the `E1` check below possible at all).
