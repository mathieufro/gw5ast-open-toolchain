# GW5AST-138C HCLK port — VERIFICATION of P1.T05-T09

Skeptic verify-and-finish pass over the four HCLK commits an interrupted
dispatch left on `clocking/gw5a-hclk-6block`, plus the missing `P1.T09`.
Everything below is measured on this box on 2026-09-05; the topology it is
checked against is `evidence/clocking/hclk-topology.md` (P1.T04): **6 blocks,
2 top / 4 bottom, `gw5_ihclk_wire_num` 38, offset 187, span 1274**.

Branch state verified: `clocking/gw5a-hclk-6block` rebased on epic `df304ad`;
the four commits named in the dispatch (`c4a30db 2831001 6183dc5 acae32e`)
are the rebase's `6740861 0853bec 52e98e6 21dc004`, plus `2cfe8fc`
(heavy-marking). Same content, new sha1s.

## Verdicts

| Task | Verdict | Evidence |
|---|---|---|
| P1.T05 `gw5_ihclk_wire_num` | **PASS** | `{'GW5A-25A': 65, 'GW5AST-138C': 38}`, no `.get()` default; the derivation `(max_ihclk_srcid - offset + 1) // 4` is written out in the comment and reproduces the 25A's 65 with no residue. `GW1N-9` / `GW5AT-60B` still raise `KeyError`. |
| P1.T06 `_gw5a_hclk_locs` | **PASS** | six distinct locs `0:(27,0) 1:(27,181) 2:(81,0) 3:(81,181) 4:(108,64) 5:(108,117)`, exactly §1 of the topology; the five bridge cells are excluded and the exclusion is stated in the comment. 25A entry byte-identical. |
| P1.T07 `gw5_add_hclk_bels` | **PASS, with one deviation** | block count comes from `_gw5a_hclk_locs[device]`, the three 25A wire literals moved into `_gw5a_hclk_ctrl_wires` (a table, not an `if`), and the half comes from `gw5_hclk_half(dev, row)` — a pure function of `dev.rows`, no per-device literal. Built db: 6 blocks x 4 = **24 CLKDIV + 24 CLKDIV2**, halves `[top, top, bottom, bottom, bottom, bottom]` = the MEASURED 2/4, refuting the blueprint's 3/3. |
| P1.T08 un-gate | **PASS as specified; the 138C HCLK network is NOT complete — see Findings** | `add_hclk_bels` and `fse_create_hclk_nodes` both `{'GW5A-25A', 'GW5AST-138C'}`; `_hclk_to_fclk` untouched; `python -m apycula.chipdb_builder GW5AST-138C` exits 0 with 0 `KeyError`/`Traceback` in the log. |
| P1.T09 `HAS_5A_HCLK` | **FIXED (was missing)** | the four commits never touched the flags block. Appended here. Built 138C db: `chip_flags = ['HAS_SP32','HAS_PINCFG','HAS_DFF67','HAS_CIN_MUX','NEED_BSRAM_RESET_FIX','NEED_CFGPINS_INVERSION','HAS_5A_DSP','HAS_5A_HCLK']`, `HAS_PLL_HCLK` absent, length grew by exactly 1. Crosses to nextpnr as `CHIP_HAS_5A_HCLK = 0x10000` (asserted by reading `gowin_arch_gen.py`, not by restating the constant). |

## Regression fixed during this pass — the 25A chipdb

The `half` field, as landed, was **written into `extra_func`**, which changed
the GW5A-25A chipdb: `010e0654…` instead of the Phase-0 family-regression
baseline `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca`.
The only delta was the four `half` keys — nothing else moved. `half` is a pure
function of data the db already carries (the block's row and `dev.rows`), so it
is now **derived, not stored**: `chipdb.gw5_hclk_half(dev, row)`. Consumers call
it; no device's serialised db changes.

- `GW5A-25A.msgpack.xz` built on `clocking/gw5a-hclk-6block` : `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca`
- `GW5A-25A.msgpack.xz` built on `origin/epic/gw5ast138c` (`df304ad`) : `6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca`
- **identical**, and equal to the value `evidence/phase0/phase-report.md` records.

## Built GW5AST-138C chipdb

- `GW5AST-138C.msgpack.xz` 819,604 B, sha256 `fa35df4fa0ccfa23fdd8626b50c887f080a76bfaa9ff9a9a3ca120c1bdd78a70`
- 6 HCLK blocks, 24 CLKDIV bels, 24 CLKDIV2 bels, `hclk_div2` 6 blocks x 4 slots
- 373 `HCLK*` nodes, 244 hclk pips over 7 tiles
- grid 109 x 182, `HAS_5A_HCLK` set

## nextpnr chipdb .bin (recipe: `evidence/_runs/chipdb-bin.txt`)

- `gowin_arch_gen.py -d GW5AST-138C -o …bba` (219,356,414 B, ~110 s) -> `bbasm --le` (3 s); `.bba` deleted
- `chipdb-GW5AST-138C.bin` **63,860,996 B**, sha256 `0227f0914c615cf6858c8cb4e0e1e17afbe7d2c399d705a9c01dd12bc5ac14b3`
  (supersedes P0.T40's `929efdf8…`, 63,856,432 B)
- installed byte-identical to `$DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/`
  and `$DATASTORE/chipdb/std/`

## Openflow smoke on `$DATASTORE/oracle-smoke`

`python -m fuzz.gw5ast138c.harness.openflow --design-dir $DATASTORE/oracle-smoke`:
`ok: true`, yosys/nextpnr/gowin_pack returncodes `0/0/0`, **`top.fs` 34,668,145 B**
(byte-count identical to the P0.T40 record), `chipdb_sha256=0227f091…`,
`timing_allow_fail_needed=false`. It still routes. Log: `evidence/_runs/hclk-port-138c-openflow.log`.

## Tests

`tests/test_gw5ast138c_clocking.py`, all 8 pass (4 of them `heavy`, i.e. they
parse the real vendor `.fse`): `test_gw5_ihclk_wire_num_has_138c`,
`test_gw5a_hclk_locs_138c_six_blocks`,
`test_gw5_add_hclk_bels_138c_block_and_wire_counts`,
`test_gw5_add_hclk_bels_25a_unchanged`, `test_hclk_nodes_138c_not_pre5a_path`,
`test_hclk_138c_takes_gw5a_branch`, `test_chip_flags_138c_has_5a_hclk` (new,
T09), `test_chip_flags_138c_maps_to_nextpnr_bit` (new, T09).
Fast scope `pytest tests -q -m "not heavy and not gate_proof"`: **248 passed,
2 failed, 12 skipped, 44 deselected**. The two failures are UNRELATED and
PRE-EXISTING: `test_batch.py::test_the_real_measured_budget_is_readable` and
`test_openflow.py::test_openflow_records_provenance` (`nextpnr_sha` is `None`)
fail identically on `origin/epic/gw5ast138c` (`df304ad`) with these commits
absent. Not fixed here — they are not this branch's. (Both are
checkout-location sensitive: they pass in the pipeline's own apicula
checkout.)

## FINDINGS — the 138C HCLK network is a six-block *bel* model on a four-block *routing* model

These are **not** regressions introduced by T05-T09; they are pre-existing
25A-shaped code that T08 newly routes the 138C into. Both are recorded rather
than fixed, because a correct fix needs a measurement nobody has made
(topology-138c.md §6: "which fabric/IO cells each block serves — NOT
MEASURED") and inventing it would put pips that may not exist into the routing
graph, which is worse than their absence.

1. **`gw5_hclk_idx(dev, device, row, col)` returns `-1` for anything that is
   not `GW5A-25A`** (`chipdb.py`). Its only caller is `gw5_make_hclk_pips`,
   whose entire table-48 walk is `if hclk_idx >= 0`. So on the 138C **no
   fuse-bearing HCLK pip is created at all**, and `dev.io2hclk` stays empty.
   Every one of the 244 pips in the built db is a default (fuse-less) pip.
2. **`gw5_make_hclk_pips`'s default-PIP section is `for hclk_idx in range(4)`**,
   with the in-tree comment *"XXX This section will need to be modified for the
   138C — it has more HCLKs"*. Measured consequence, per-block `HCLK<i>_*` node
   counts in the built 138C db: blocks 0-3 get 70/71/70/70, blocks **4 and 5
   get 26** — they have no `HCLK`, `HCLK_BUF_A*`, `HCLK_HUB`, `HCLK_FROM_IHCLK`,
   `HCLK_TO_IHCLK`, `HCLK_GCLK_MUX` or `HCLK_MUX_DELTA/EPSILON/GAMMA` wires.
   The inter-HCLK default tables below it are 4-block literals too.
3. **`gw5_make_pin_to_hclk` and `gw5_make_hclk_to_clk_gates` carry 25A board
   and tile literals** — `{'row': 36, 'col': 11, 'wire': 'F5'}` (the
   TangPrimer25k quartz pin) and `spec_ttyp = {B:(36,46,ttyp 393), T:(0,59,410),
   R:(27,91,187), L:(10,0,257)}` — and take no `device` guard. On the 138C
   (109x182) those coordinates are meaningless. They currently emit nothing
   harmful (no 138C `clock_pips` entry matches, so `make_node_and_gate_pip`
   never fires and the pin node lands on an unrelated tile), but they are the
   next thing to bite. Phase 1's blueprint assigns `pin -> HCLK routing` to
   Phase 3 (the `S10`/`S12` seam), which is where 1 and 3 belong; 2 is
   mechanical but pointless without 1.

Consequence for the phase: `S8`'s "nextpnr creates CLKDIV/CLKDIV2 bels" half is
met (24 + 24 on six blocks) and `HAS_5A_HCLK` is set; the "HCLK->FCLK pips"
half cannot be met from this chipdb, and **P1.T14-T16's shapes will fail to
route a real HCLK unless P1.T10/T11 or a new task takes `gw5_hclk_idx` and the
`range(4)` default block.** `gw5_make_hclk_pips` and `gw5_hclk_idx` are **not**
in Phase 1's owned-function list (`blueprints/P1-clocking.md` File ownership),
so this is raised, not silently taken.

## Scope notes (deviations recorded, not hidden)

- `gw5_logic_to_hclk_wires` was rewritten by the landed commits to read
  `_gw5a_hclk_locs` instead of its own duplicate 25A literal. That function is
  **not** in Phase 1's owned list, but the change is required — without it
  `gw5_make_hclk_pips` KeyErrors on the 138C — and it is provably neutral for
  the 25A (same dict, same order; the 25A sha256 above proves it).
- `_gw5a_hclk_ctrl_wires['GW5AST-138C']` is **ASSUMED equal to the 25A**, and
  says so in the code. P1.T04 measured the block topology, not the control-pin
  trace, and no oracle budget was allocated for one. All twelve wire names do
  exist in `wirenames_5ast138c`, which is necessary, not sufficient. Promoting
  it to MEASURED needs a shape run exercising `CLKDIV.CALIB` / `RESETN`
  (P1.T14/T15).
- The `hclknames_5ast138c` append adds 347 names in `701..1273`; the remaining
  indices in that span were already named `UNK<n>` by `clknames_5ast138c`, so
  the span was never short and the KeyError it guards against could not fire.
  Harmless, and the names are better; the commit message overstates it.
- The blueprint's T07 test text asks for a stored `half` on
  `extra_clkdiv`/`extra_clkdiv2`; it is a derived function instead, for the 25A
  byte-identity reason above. The test asserts the halves through
  `chipdb.gw5_hclk_half` and asserts that the field is *not* stored.

## Reproduction

```sh
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
cd $FL_WT/apicula   # branch clocking/gw5a-hclk-6block
$FL/vendor/venv/bin/python -m pytest tests/test_gw5ast138c_clocking.py -q
$FL/vendor/venv/bin/python -m apycula.chipdb_builder GW5A-25A     -o /tmp/25a.msgpack.xz
$FL/vendor/venv/bin/python -m apycula.chipdb_builder GW5AST-138C  -o /tmp/138c.msgpack.xz
$FL/vendor/venv/bin/python $FL_WT/nextpnr/himbaechel/uarch/gowin/gowin_arch_gen.py \
    -d GW5AST-138C -o /tmp/chipdb-GW5AST-138C.bba
$FL_WT/nextpnr/build/bba/bbasm --le /tmp/chipdb-GW5AST-138C.bba /tmp/chipdb-GW5AST-138C.bin
$FL/vendor/venv/bin/python -m fuzz.gw5ast138c.harness.openflow \
    --design-dir $DATASTORE/oracle-smoke --json
```
