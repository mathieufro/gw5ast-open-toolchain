# P1 clocking — checkpoint

## Entry

- Edition: 1.9.12.03 Standard
- installs_available: 1
- edu-provisional: false
- gowinhome.selected: /Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
- chipdb sha256 (apycula/GW5AST-138C.msgpack.xz): fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb
- Full detail: $OTC/evidence/_runs/p1-entry.log

## Oracle runs (D62 box = 290 for Phase 1)

| task | runs | cumulative | ledger |
|---|---|---|---|
| P1.T04 | 14 | 14 | `$OTC/evidence/clocking/oracle-runs.jsonl` (13 rows in the batch ledger + 1 exploratory `clkdiv24` recorded in `hclk-topology.md` §9) |

P1.T03's `$OTC/evidence/_budget/clocking-runs.tsv` did not exist when P1.T04
ran; T04's rows are in `evidence/clocking/oracle-runs.jsonl` per the task
instruction. Whoever lands T03 must fold this row into the .tsv, not
re-count it.

## Checkpoint 145

Written at the `D62` trigger (`cumulative >= 145`, first crossed by
`p1t27-dhce-e1` at 145) and refreshed at the phase close. The box for Phase 1
is **290** oracle runs; the ledger's final `cumulative` is **221**, so the
phase closes **69 runs inside the box** and no re-scope is needed.

| slug | runs | blueprint line | verdict |
|---|---|---|---|
| `plla` | 102 | 55-80 (+`P1.T19`'s 14 tracing runs, pre-authorised at 82 by `F14`) | over the sweep line by 20, all of it the four-batch split `F33` created (`P1.T23`/`T41`/`T42`/`T43`) plus the pump campaign no document publishes; pre-authorised |
| `dhcen` | 47 | greenfield, no published line | within budget; 28 of them are the control-pin trace (`P1.T25`) that had no prior art |
| `hclk` | 27 | 60-100 shared with CLKDIV/CLKDIV2 | 49 with `clkdiv`+`clkdiv2`, under the line |
| `clkdiv` | 14 | shared with `hclk` | as above |
| `clkdiv2` | 8 | shared with `hclk` | as above |
| `dqce` | 17 | 20-40 | under |
| `dcs` | 5 | 25-40 | under, and the row does not close: the remaining budget was not spent because the blocker is a device measurement (the `P{26,27,36,37}` input side), not more sweep points |
| `clocking` | 1 | the `P1.T40` E2E run | as planned |

Total 221 of 290. The `D62` stop rule was never triggered.

The PLL timing slice is a recorded absence, not a spent run:
`$OTC/evidence/plla/timing-l0-pll.md` carries one `NO-DATA:` line and `## Timing`
below says why.

## Family regression

`S3`/§7.4, run at the phase close on the one install this box has
(`installs_available: 1`, Standard 1.9.12.03; the Education install was
removed under `C9`, so the Education half is owed to the Phase-8 Licence
Gate). Three builds, no `FAIL` line:

| device | sha256 | vs P0.T40 baseline |
|---|---|---|
| `GW5AST-138C` | `8bb0932efc776ff2961d5f7a590774ec9f229a9670d82208bfec808da9e39886` | moved (this phase's clocking work); reproduces the installed `.bin` pair exactly |
| `GW5A-25A` | `5ad9184d5ae2ece33277d9003f3b94b215a616b93949ebb0d43139be10abe4d2` | moved from `6311219d…` — **explained below** |
| `GW5AT-60B` | `615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8` | unchanged |

**Why the 25A moved.** The two chipdbs were loaded and compared field by
field: the only differing field is `extra_func`, in exactly the six cells
that carry a PLL, and the only difference inside each is one **new key**,
`primitive`, whose value is `'PLLA'`. That is `D96`: the vendor cell type is
data in the chipdb now (`PLLA` on the 25A, `PLL` on the 138C) instead of a
device gate in the code. Additive, no key removed, no value changed — the
25A's PLL model is otherwise byte-identical.

## Timing (`V12a --classes pll`)

The PLL slice of the L0 band is a **recorded absence**, not a skipped check:
`$OTC/evidence/plla/timing-l0-pll.md` carries exactly one `NO-DATA:` line —
the `GW5AST-138C` `.tm` publishes no PLL timing group at all (chunks 0-2 carry
a GW2A-18 rPLL block naming outputs this die does not have), and the vendor
SDF emits every `CLKIN->CLKOUTn` IOPATH as `0.000`. `P1.T33` therefore asserts
the slice as "no arcs by design", 7/7.

## Landed

Phase-1 branch → commit map at the phase close (`P1.T38`). Every
`clocking/*` branch is an ancestor of its fork's `integration/p1-clocking`,
and that branch is an ancestor of `epic/gw5ast138c`; the merges are ordinary
merge commits, no rebase, no history rewritten.

| repo | branch | sha |
|---|---|---|
| apicula | `clocking/plla-138c` | `973b31b` |
| apicula | `clocking/gw5a-hclk-6block` | `20451cb` |
| apicula | `clocking/dhcen-gw5a` | `e4efd41` |
| apicula | `clocking/dqce-dcs-quadrants-138c` | `a2179ca` |
| apicula | `clocking/iologic-guard-spelling` | `39e5976` |
| apicula | `clocking/pll-timing-138c` | `d88235a` |
| apicula | `integration/p1-clocking` | `b2aba7a` |
| apicula | `epic/gw5ast138c` | `ab350d4` |
| nextpnr | `clocking/gw5a-hclk-6block` | `af8e8c03` |
| nextpnr | `clocking/dhcen-gw5a` | `39859bea` |
| nextpnr | `integration/p1-clocking` | `d90fa528` |
| nextpnr | `epic/gw5ast138c` | `7dd337bb` |

Attribution, scoped the way `V10` scopes it (never `--all`):
`git log --grep='Co-Authored-By' --grep='Generated with'
upstream/master..epic/gw5ast138c` returns **0** in apicula,
`upstream/main..epic/gw5ast138c` returns **0** in nextpnr, and the whole
`open-toolchain` history returns **0**.
