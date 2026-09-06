# `evidence/clkdiv2/` — CLKDIV2 on the GW5AST-138C (`P1.T15`)

## Row

`spec-primitives.md` §1 row **CLKDIV2**. Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`, oracle Gowin EDA **1.9.12.03
Standard** (licensed — no `edu-provisional` row here).

The cell that row carried before this batch read *"as CLKDIV"*, an inherited
assumption. It is superseded by what was measured here, and the two
primitives do **not** in fact close at the same level.

Two measured facts from `P1.T04` set the shape of the sweep, both departures
from the blueprint's wording:

* **`CLKDIV2` takes no `DIV_MODE`.** `prim_sim.v:13122` gives it exactly
  `(CLKOUT, HCLKIN, RESETN)` and `gowin_pack.GW5A.get_CLKDIV2_fuses()` returns
  `[]`. There is no mode set to sweep, so the swept axis is what the device
  actually varies: which of the four lanes of an HCLK block the CLKDIV2 sits
  on, and how `RESETN` is driven.
* **`CLKDIV2.CLKOUT` cannot drive ordinary fabric** (vendor `CK2060`), so it
  chains into a `CLKDIV` that clocks the counter — the structure of
  `examples/gw5a/clkdiv2_chain-tangmega138k.v`; nextpnr places the pair
  together and the link is non-switchable (`gowin.cc:374-380`).

Shapes:

* `fuzz/gw5ast138c/shapes/clocking_clkdiv2.py` — one CLKDIV2 → CLKDIV chain in
  **HCLK block 5** (`_gw5a_hclk_locs['GW5AST-138C'][5] == (row 108, col 117)`,
  `P1.T04`), on the swept lane, its `CLKOUT` clocking a 4-bit ring counter
  driving four LEDs, so the divided clock must actually escape the block.
  Both flows are pinned to the same site — the vendor by
  `INS_LOC "div0" BOTTOMSIDE[4 + lane];`, the open flow by the RTL
  `(* BEL = "X117Y108/CLKDIV2_<lane>" *)` attribute, because nextpnr's `.cst`
  reader cannot parse the 138C's `SIDE[0~7]` spelling (`P1.T14`, split
  `top-open.cst`). Blocks 0 and 1 are avoided (`D100a`).
* `fuzz/gw5ast138c/shapes/clocking_clkdiv2_free.py` — the same design with
  **both** placement pins removed: the control that says what the two placers
  do unprompted. `E0` and `diff` by construction.

## Sweep

`(lane, RESETN)` over the four lanes with `RESETN` driven from a pin, plus
`RESETN` deasserted at `1'b1` on lanes 0-2: **7 pinned points from 7 oracle
runs** (batch `p1t15-clkdiv2-e1`), plus the unpinned control (batch
`p1t15-clkdiv2-e0`) — **8 rows from 8 oracle runs**, the task's budget.
`RESETN` tied to `1'b0` is deliberately not run: with the divider held in
reset both synthesisers fold the design away, which would measure the
optimiser, not the primitive.

The lane axis is the point: `chipdb.py:1748-1757` gives a CLKDIV2 its `HCLKIN`
from **`HCLK_BUF_BO5<i>` as a fuseless node on even `i`** and from the
**`CLKDIV2_I5<i>` pip on odd `i`** — the two input paths the chipdb builder
distinguishes — so both are only covered by running both parities. Lanes 0
and 2 exercise the node path, lanes 1 and 3 the pip path.

| sweep point | level | verdict | cells | attrs | conns | unexplained residual | decode c1/c2 |
|---|---|---|---|---|---|---|---|
| `lane 0 (HCLK_BUF_BO), RESETN=pin` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 1 (CLKDIV2_I), RESETN=pin` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 2 (HCLK_BUF_BO), RESETN=pin` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 3 (CLKDIV2_I), RESETN=pin` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 0 (HCLK_BUF_BO), RESETN=tied` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 1 (CLKDIV2_I), RESETN=tied` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `lane 2 (HCLK_BUF_BO), RESETN=tied` | E0 | **ok** | 0 | 0 | 0 | 0 | ok/ok |
| `placement=free` | E0 | **diff** | 2 | 3 | 0 | 0 | ok/ok |

pips (whole-device statistic, never a verdict term, `D32`): 2021063, 2021180,
2021063, 2021181, 2020478, 2020829, 2020946, 2020829.

### Fuse attribution

`gen_clkdiv2_fuses.py` differences the HCLK block cell `(108, 117)`
(`ttyp 379`) of each run's vendor `.fs` against the `P1.T14` **CLKDIV-only**
run at the same lane and the same `DIV_MODE`, and against this sweep's own
lane-0 point, then looks the moved bits up in that tile type's
`shortval['HCLK']` table exactly as `../clkdiv/gen_divmode_fuses.py` does.

**The CLKDIV2 writes no attribute fuse of its own, and its bitstream
signature is a bit that is *absent*.** The mux source it drives,
`HCLK_MUX_ALPHA5<i> <- CLKDIV2_O5<i>`, is fuseless in the chipdb (as is
`CLKDIV2_HCLKIN5<i> <- CLKDIV2_I5<i>` on the odd lanes), while the competing
source `HCLK_MUX_ALPHA5<i> <- HCLK_BUF_BO5<i>` has exactly one fuse. So a lane
whose alpha mux is fed by a CLKDIV2 is a lane whose `HCLK_BUF_BO` select bit
is **not** set — measured on all 7 points, and set in the CLKDIV-only
reference.

| lane | input path | alpha-mux `HCLK_BUF_BO` select fuse in cell (108,117) | set with CLKDIV2? | chained CLKDIV `HCLKDIV<lane>_DIV = 2` | `gowin_pack` predicts | agree |
|---|---|---|---|---|---|---|
| 0 | `HCLK_BUF_BO` (node) | `21,41` | **no** (set in the CLKDIV-only reference) | `21,51` | `21,51` | **yes** |
| 1 | `CLKDIV2_I` (pip) | `20,4` | **no** | `20,24` | `20,24` | **yes** |
| 2 | `HCLK_BUF_BO` (node) | `20,79` | **no** | `20,68` | `20,68` | **yes** |
| 3 | `CLKDIV2_I` (pip) | `20,15` | **no** | `20,54` | `20,54` | **yes** |

The right-hand columns are the chained CLKDIV following the swept lane: its
one-hot `HCLKDIV<lane>_DIV` bit moves from lane 0's `21,51` to the lane's own
bit, and agrees with `GW5A.get_CLKDIV_fuses` at every lane — the same
independent-sources agreement `P1.T14` recorded, now across lanes instead of
across modes. Every other bit that moves between two points belongs to that
lane change (the block's beta mux and its `HCLK_TO_GCLK`/`L2HCLK` sources move
with it, visible as `active_hclk_pips` in `clkdiv2-fuses-138c.json`), and the
harness's own masked comparison leaves `0` unexplained bits on every row.

## Verdict

**Verdict re-derived twice, both times from the fields the rows already carry
— no re-run.** First on 2026-09-06, when `equiv.evidence_fields` was fixed to
treat the §5.4 decode check as a verdict term (defect 1 below): that turned
all **7** pinned points from `ok` to `diff` on the `c1` mismatch alone. Then
again under **`D103`**, the owner decision this row asked for: `CLKDIV2` is
now listed in the harness's `NON_FUSE_BACKED_BELS`, so `c1` no longer asks the
decode for a cell the bitstream cannot carry. It asks instead for the chained
`CLKDIV` on the same lane at `DIV_MODE = 2` — recovered on all 7 points — and
the pinned rows close `ok`. The control stays `diff` by construction.

**Set-level `E0` holds on all 8 rows — `cells = 0`, `attrs = 0`, `conns = 0`
and no unexplained residual bit on all 7 pinned points, `0` refused, `0`
aborted — and `E1` is NOT attainable for this primitive on this device.**

That last part is a property of the silicon, not of the flow. `E1` here would
be the `P1.T14` HCLK-bel check: compare the bel nextpnr placed on against the
cell the **vendor's bitstream** decodes to (the vendor's text reports never
name a CLKDIV/CLKDIV2 at all — MEASURED, `P1.T11`). A CLKDIV2 leaves no fuse
anywhere, so `gowin_unpack` cannot recover it: every row's `e1` half reports
`EC9/HCLK: ... 'div2' at X117Y108/CLKDIV2_0 — CLKDIV at the same site`. The
chained `CLKDIV` at the same site **is** recovered and does match, on all 7
points, which is what bounds the claim: the placement of the pair is
confirmed, the CLKDIV2's own occupancy of its lane is inferred from the
absent alpha-mux select bit above, not decoded.

DEL-b status for the `spec-primitives.md` §1 `CLKDIV2` row: **`E0+hw-pending`**
— the set-level comparison is clean, the decode check passes on the terms the
bitstream can answer, and nothing short of hardware can raise the row, because
the bitstream carries no bit that names a CLKDIV2. The reclassification that
got it here is a claim about the device's bitstream format, priced by the owner
as `D103` and narrow by construction: the exemption holds only while a
`CLKDIV` at `DIV_MODE = 2` decodes on the same lane, and
`tests/test_clkdiv2_non_fuse_backed.py` fails if that guard is widened.

Two further results, each measured:

* **The unpinned control** (`clocking_clkdiv2_free`, batch
  `p1t15-clkdiv2-e0`) is `diff` by construction — `cells = 2`, `attrs = 3`,
  `first_diff` `tile (117,108) bel 0: cell vendor=CLKDIV_ open=<absent>`: told
  nothing, the two placers pick different HCLK blocks. It is recorded as its
  own batch beside the sweep, and the row tests exempt it by name rather than
  letting a `diff` verdict pass unnoticed anywhere else.
* **`RESETN` driven from a pin and tied to `1'b1` produce the same HCLK-cell
  configuration** on every lane (identical `active_hclk_pips`, identical
  attributed fuses): `RESETN` is a routed signal, not a configuration bit.

Two defects found while closing this row, both since **fixed** in the harness
(apicula `epic/gw5ast138c`, guarded by
`tests/test_equiv_decode_check_verdict.py`):

1. **`equiv.evidence_fields` drops the §5.4 decode-check verdict.** FIXED —
   `c1`/`c2` are verdict terms; these rows were re-derived above.
   `compare_design` sets `result.verdict = "DIFF"` when `c1`/`c2` fail, but
   the schema `verdict` is recomputed from set diffs and residual alone, so
   these rows say `verdict: ok` while their own `notes` say the decode check
   failed. Here the mismatch is expected and explained (above), but the field
   would hide a real one.
2. **`chipdb_sha256` is not constant across this batch**: runs 0000-0004 ran
   against `3e1e39ea…`, runs 0005-0006 and the control against `986d6989…`
   (the branch's chipdb was rebuilt mid-batch). `P1.T14`'s ten rows split
   5/5 across the same two shas. Both halves give identical verdict terms
   here, but a batch should pin one chipdb. FIXED — `run_batch` now records
   the chipdb sha256 at batch start (`BATCH_CHIPDB`), re-checks it before
   every run and after every row, and refuses to continue on a change
   (`BATCH_CHIPDB_CHANGED`); the mixed shas on these rows are historical and
   are not backfilled, because that would need a re-run.

## Artefacts

* Rows: `runs.jsonl` (this directory), promoted by `promote_rows.py --prune`
  from `$OTC/evidence/_runs/p1t15-clkdiv2-e1.rows.jsonl` (7 pinned points) and
  `$OTC/evidence/_runs/p1t15-clkdiv2-e0.rows.jsonl` (the control).
* Batch logs: `$OTC/evidence/_runs/p1t15-clkdiv2-{e1,e0}.log` and their
  `.watchdog.log` siblings; each ends in its own `BATCH_COMPLETE` line
  (`runs=2 ok=2` after a resume that skipped 5 terminal rows, and `runs=1
  ok=0 diff=1`, `aborted=0` both).
* Fuse attribution: `clkdiv2-fuses-138c.json`, produced by
  `gen_clkdiv2_fuses.py`; the no-oracle-cost probe that first showed the
  vendor writes no CLKDIV2 bit is `clkdiv2_fuse_probe.py`.
* Vendor and open bitstreams, `.tr`, `.sdf` and per-step logs: absolute paths
  with sha256 inside each row, under
  `/Users/alex/fine-line-data/open-toolchain-gw5ast/batch/p1t15-clkdiv2-e1/`
  and `.../p1t15-clkdiv2-e0/`. Each vendor `run/` tree was pruned to
  `run.fs`, `run.tr`, `run.vo`, `run.sdf` (`D99`), recorded in the row's
  `notes`.
* Evidence this row rests on: `../clkdiv/summary.md` (`P1.T14`, the CLKDIV
  row and the shared shape), `../clkdiv/unpack-138c.md` (`P1.T08c`),
  `../hclk/mux38-138c.md` (`P1.T08d`), `../hclk/clkdiv-138c.md` (`P1.T11`,
  the CLKDIV2 placement evidence).
