# DHCEN control-pin tracing on GW5AST-138C — method and evidence (P1.T25)

Task: `blueprints/P1-clocking.md` P1.T25 (greenfield: `_dhcen_ce` has no GW5A
entry at all, `apycula/chipdb.py:2374-2413`, and `fse_create_dhcen` returns
early for every device without one). Oracle: Gowin IDE **1.9.12.03 Standard,
licensed** (`edu-provisional: false`). Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`. Chipdb
`fa35df4fa0ccfa23fdd8626b50c887f080a76bfaa9ff9a9a3ca120c1bdd78a70`.

The result table is `ce-wires-138c.md` / `ce-wires-138c.json`. This file is how
it was obtained and why each step is entitled to its conclusion. **No
`chipdb.py` change is made here** — that is P1.T26.

## 1. The first refutation: there is no `DHCEN` on this family

The task, the blueprint and `_dhcen_ce` all say `DHCEN`. On `GW5AST-138C` that
primitive does not exist:

| instrument | reading |
|---|---|
| GowinSynthesis, `DHCEN` instantiated | `ERROR (EX3937) : Instantiating unknown module 'DHCEN'` (run `feas1`) |
| `IDE/ipcore/DHCEN/dhcen.ipspec` `<devices>` | 57 `GW1*`/`GW2*` entries, **zero** `GW5*` entries |
| `IDE/bin/prim_syns/gw5a/primitive.xml` | `<name>DHCE</name>` with `CLKIN`, `CEN`, `CLKOUT`; also `DCE(CLKIN, CE)` where the older families have `DQCE` |
| GowinSynthesis, `DHCE` instantiated | compiles, places, routes; `run.fs` produced (run `feas2`) |

So the GW5A spelling is **`DHCE`** and the enable port is **`CEN`**. Every run
of this campaign instantiates `DHCE`. `P1.T26` and the nextpnr side must use
that spelling on the vendor-facing edge; apicula's internal name for the
mechanism (`dhcen`, `_dhcen_ce`) is unaffected.

## 2. The second refutation: the capacity is stated by the vendor

Every successful run's `run.rpt.txt` carries a `Clock Resource Usage Summary`
with a `DHCE` line. It reads `1/24 ... 24/24` as the sweep advances, and the
`25` point is refused:

```
ERROR  (PA2017) : The number(25) of CLKDIV in the design exceeds the resource
limit(24) of current device
```

**24 DHCE sites**, matching the 24 CLKDIV that P1.T04 measured as 6 HCLK blocks
x 4. The blueprint's assumed shape — 4 sides x 6 entries, one block per side —
does not hold: this die has **six** HCLK blocks and **no top-edge block**
(P1.T04), so the table is 6 blocks x 4 sites, i.e. 8 entries on each of `L`,
`R` and `B` and no `T` key at all.

## 3. Method

The maintainer's own, quoted in the `_dhcen_ce` comment: build vendor images
with the maximum allowable number of instances whose enable ports are driven
from IO, then trace the route from the IO to the final wire — that wire is the
enable port.

Design (`fuzz/gw5ast138c/shapes/clocking_dhcen_trace.py`, apicula branch
`clocking/dhcen-gw5a`): `n` x `DHCE`, each feeding the `HCLKIN` of its own
`CLKDIV`, so the vendor must allocate a distinct HCLK input per instance. All
`n` enables share **one** package pin (`cen`, `AA11`, bank 5), so the whole
fan-out is a single connected component of the routing graph and one pin
suffices for 24 instances. Pins are bank 4/5 only, never 6/7 (`D20c`, `D54`).

The trace itself (`probe_dhce.py::trace_enable_wires`) unpacks the vendor `.fs`
with the harness' own `unpack_netlist` (the frozen `gowin_unpack` path), groups
wires into nets by the pip graph, and reports each net's wires that lie in an
HCLK block cell and drive nothing further — the ends of the route.

### 3.1 Why the naive trace is ambiguous, and what fixes it

Three IO-fed nets end **once per instance** inside the HCLK block cells, so a
structural rule alone cannot pick the enable:

| net | end wires per block | separated by |
|---|---|---|
| `CLKDIV.RESETN` | `D4 D5 D6 D7` | the `tie_resetn` variant (`RESETN` tied to `1'b1`; the `rst_n` pin is kept and xor-ed into the output so the `.cst` is unchanged) — the set disappears |
| `CLKDIV.CALIB` | `B6 B7 C0 C1` | the **control run** `dhce00_tr_div24`: 24 `CLKDIV`, **zero** `DHCE` — the set is still there with 24 ends |
| `DHCE.CEN` | `C2 C5 C7 D2` (`C2 A5 C7 A4` in block `(81, 0)`) | what is left |

That is the whole identification argument, and it is the reason the campaign
needed a control point rather than the sweep alone.

### 3.2 Second, independent instrument: the fuse presence diff

`attribute.presence_diff` against the `n = 0` baseline, counting moved fuses in
the six HCLK block cells. It never sees a wire name, so it is independent of
the routing trace — and it lights exactly the same blocks in exactly the same
order:

| n | (108,64) | (27,181) | (81,181) | (108,117) | (81,0) | (27,0) | tiles touched |
|---|---|---|---|---|---|---|---|
| 1 | 7 | 0 | 0 | 0 | 0 | 0 | 2 |
| 2 | 32 | 0 | 0 | 0 | 0 | 0 | 21 |
| 3 | 51 | 0 | 0 | 0 | 0 | 0 | 22 |
| 4 | 81 | 0 | 0 | 0 | 0 | 0 | 28 |
| 6 | 83 | 38 | 0 | 0 | 0 | 0 | 111 |
| 12 | 85 | 82 | 88 | 0 | 0 | 0 | 138 |
| 24 | 87 | 88 | 100 | 90 | 85 | 84 | 247 |

Fill order `(108,64) -> (27,181) -> (81,181) -> (108,117) -> (81,0) -> (27,0)`,
four instances per block, is the same order the routing trace reports. (The
counts include the accompanying `CLKDIV`'s own fuses; the diff is used here for
block affiliation, which is what `chipdb.py:1509-1515` uses it for, not for
per-bit attribution.)

## 4. Fuse -> pin table

| HCLK block cell | side | vendor fill order | DHCE sites | enable wires | moved fuses at n=24 |
|---|---|---|---|---|---|
| (108, 64) | B | 1st | 4 | `C2 C5 C7 D2` | 87 |
| (27, 181) | R | 2nd | 4 | `C2 C5 C7 D2` | 88 |
| (81, 181) | R | 3rd | 4 | `C2 C5 C7 D2` | 100 |
| (108, 117) | B | 4th | 4 | `C2 C5 C7 D2` | 90 |
| (81, 0) | L | 5th | 4 | `C2 A5 C7 A4` | 85 |
| (27, 0) | L | 6th | 4 | `C2 C5 C7 D2` | 84 |

`(81, 0)` is the one block that does not use `C5`/`D2`. It is not a routing
accident: three independent builds (`p1-dhcen-trace-1` `n=24`,
`p1-dhcen-trace-2` `n=24`, `p1-dhcen-trace-4` `n=20`) report the same four
wires, and the per-pip dump of that tile shows all four are genuine dead ends
(`A4 <- X05`, `A5 <- X05`, `C2 <- R83C1_N26`, `C7 <- R83C1_N20`, with `X05`
itself fed from `N26`); `C5` and `D2` are **not in the net at all**. Its
`CLKDIV.CALIB` ends are the uniform `B6 B7 C0 C1`, so the asymmetry is specific
to the enable, not to the block's routing in general. `(81, 0)` is the block
whose `.fse` `ttyp` is `275` (P1.T04).

## 5. What was NOT found: interbank entries

The GW1N/GW2A tables have six entries per side — four input multiplexers plus
two interbank inputs (`HCLK_BANK_OUT0/1`). On this die the vendor allocates
**exactly four** DHCE per block and refuses the 25th, so no interbank entry can
be produced by this method. Either the 138C has no DHCE on its interbank
inputs, or the vendor tooling will not place one there; this campaign cannot
tell those apart and does not claim to. `P1.T26` inherits a 4-per-block table.

## 6. Evidence rows

| batch | log | runs | ok | refused | what it settled |
|---|---|---|---|---|---|
| feasibility | `../_runs/p1-dhcen-feas.md` (this file §1) | 2 | 1 | 1 | `DHCEN` refused / `DHCE` accepted |
| `p1-dhcen-trace` | `../_runs/p1-dhcen-trace-1.log` | 9 | 8 | 1 | capacity 24, fill order, three end-sets |
| `p1-dhcen-trace-2` | `../_runs/p1-dhcen-trace-2.log` | 7 | 7 | 0 | `tie_resetn`: `D4-D7` is `RESETN` |
| `p1-dhcen-trace-3` | `../_runs/p1-dhcen-trace-3.log` | 1 | 1 | 0 | control: `B6 B7 C0 C1` is `CALIB` |
| `p1-dhcen-trace-4` | `../_runs/p1-dhcen-trace-4.log` | 2 | 2 | 0 | `(81,0)` reproduced at `n=20` |
| `p1-dhcen-trace-5` | `../_runs/p1-dhcen-trace-5.log` | 7 | 7 | 0 | per-index order for `(81,0)` and `(27,0)` |

**28 oracle runs** total (budget for this dispatch: <= 30; blueprint estimate:
24). Every run is a row in `oracle-runs.jsonl` and is counted in
`../_budget/clocking-runs.tsv`. Every batch was detached with the
out-of-process watchdog armed first and ended with its own
`BATCH_COMPLETE ... aborted=0` line (the `p1-dhcen-trace` batch has
`aborted=1`: the deliberate `n=25` over-subscription, which is a measurement,
not a failure) and a matching `WATCHDOG_COMPLETE`.

The one refusal in each of the two refusing runs is recorded verbatim, because
a vendor refusal is the deliverable here: `EX3937` states that `DHCEN` is not a
GW5A primitive, and `PA2017` states the capacity.

## 7. Reproduction

```sh
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib
export DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
cd <apicula worktree on clocking/dhcen-gw5a>
PYTHONPATH=$PWD python $OTC/evidence/dhcen/probe_dhce.py \
    --out-root $DATASTORE/clocking/dhcen/batchN \
    --log      $OTC/evidence/_runs/p1-dhcen-trace-N.log \
    --ledger   $OTC/evidence/dhcen/oracle-runs.jsonl \
    --result   $OTC/evidence/dhcen/trace-result.json \
    --batch-id p1-dhcen-trace-N --tie-resetn \
    --points 1,2,3,4 --trace-points 1,2,3,4
python $OTC/evidence/dhcen/build_ce_wires.py       # rebuilds ce-wires-138c.*
```

`build_ce_wires.py` is deterministic and re-derives the committed table from
the committed `trace-result*.json` files, so the reduction is auditable without
re-running the oracle.

## 8. Handover to P1.T26

* Add `'GW5AST-138C'` to `_dhcen_ce` in the shape printed in
  `ce-wires-138c.md` §"The shape P1.T26 needs" — **8 entries per side over two
  blocks, no `'T'` key**.
* `fse_create_dhcen`'s `idx < 4 -> HCLK_IN{idx} else HCLK_BANK_OUT{idx-4}` rule
  assumes one block per side and six entries. It does not carry over: here
  `idx` is per-block, `0..3`, and there is no interbank entry.
* It also indexes `_hclk_to_fclk[device][side]['hclk']`, which has no
  `GW5AST-138C` entry yet, and `dev.hclk_pips[hclk_loc]` — which on this device
  is empty for blocks 4 and 5 and fuse-less throughout (`gw5_hclk_idx` returns
  `-1`, P1.T05-T09 FINDINGS, and `gw5_make_hclk_pips`' default-PIP section is
  `range(4)`). Both are prerequisites P1.T26 must confront; this task changed
  neither.
* The vendor primitive name is `DHCE` with port `CEN`.
