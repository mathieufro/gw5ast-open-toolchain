# Phase 2 — AE350 hard RISC-V core: what closed, what did not

Closed on `epic/gw5ast138c` (apicula `ebef8e9`, nextpnr `97d54b35`),
open-toolchain `main`, Standard 1.9.12.03, one install. **8 vendor runs** of a
box of 90 (`D50`), 16 evidence rows over three slugs. Validation:
`evidence/phase2/validation.md`.

---

## 1. `S19` — reached, except the two halves named below

> **S19 — AE350.** The `McuIns` 265 + `McuOuts` 372 = **637** table entries are
> reconciled against the estimated ~900 AE350 fabric wires as the first
> sub-item, and any shortfall is routed to `EC5`'s differential wire discovery
> for the uncovered buses only; an `AE350_SOC` bel exists, built from the
> `.dat` `McuIns`/`McuOuts` tables; a bare `Emb_TCM`-shaped instantiation is
> **E0**- or **E1**-equivalent to the vendor build of the same design;
> `PLL_R[0].CLKOUT1 → CORE_CLK` is modelled as a fixed, non-routable
> connection; the fuse count set for the bel is zero or the non-zero set is
> enumerated with evidence (EMCU precedent expects zero). At the Hardware
> Gate, a `BUILD_LOAD` ELF loaded over the separate debug TAP prints on UART2.

| sub-clause | verdict | evidence |
|---|---|---|
| the 637-vs-~900 reconciliation, with a verdict | **reached, and it went the other way** (`A24`) | `evidence/ae350/reconciliation.md`, one `RECONCILIATION-VERDICT:` line |
| the shortfall routed to `EC5` discovery | **reached as a zero-run pass** | `rescope.md` rev 3: `P2.T37` VOID — the map came from tables, not a campaign |
| an `AE350_SOC` bel exists, built from the `.dat` | **reached** | `AE350 ok: 4/4` clause 1: 416 in / 495 out bits at `(0, 159)`; 884 of 911 bound |
| a bare instantiation `E0`/`E1`-equivalent to the vendor build | **reached at `E1`** | `EQUIV E1 ok`, `cells=0 attrs=0 conns=0`, `c1` 1780/1780, `c2` byte-identical — re-run at the close tip (`validation.md` §E2E) |
| `PLL_R[0].CLKOUT1 → CORE_CLK` modelled as a fixed, non-routable connection | **NOT reached, and must not be** (`A18`) | `core-clock.md`: the zero-delay hop exists from **both** PLL sites |
| fuse set zero, or the non-zero set enumerated | **reached: zero, measured** | two AE350 designs share **zero** interface-band bits; `get_AE350_SOC_fuses` returns `[]` |
| `S19`(hw): `BUILD_LOAD` ELF + UART2 transcript | **`E0+hw-pending`**, owed to Phase 9 | row `ae350-soc-s19-hw-0001` |

**Verdict: `S19`'s non-hardware half is reached**, with one clause replaced by
the measurement that refuted it (`A18`) and one that turned out to be about an
empty table (`A24`). `V18` — the criterion's own executable form — prints
`AE350 ok: 4/4`, exit 0.

The two rows this phase owns beyond `S19` also closed: **`AE350_RAM`** at a
terminal `refused` (`ERROR (RP0008) : There is no AE350_RAM resource in
current device` — twice, with a control that builds), and **Dual-purpose pins**
at `E1` on all nine points, seven `ok` and two named refusals.

## 2. The hardware-pending halves

Nothing here waits on more simulation; both wait on a board (`P9`, the
hardware gate).

1. **`S19`(hw), `AE350_SOC`.** Owed verbatim: a `BUILD_LOAD` ELF loaded over
   the **separate user-I/O debug TAP** (not daisy-chained behind the
   configuration TAP) and a **UART2 transcript**. Recorded as `E0+hw-pending`
   with the reason `E1` cannot cover it — a bitstream comparison cannot show
   a core executing.
2. **The `cpu` dual-purpose point.** The vendor moves **no** bit for
   `-use_cpu_as_gpio` while apicula sets `CPU_AS_GPIO_0/1`; recorded as a
   `DIFF` rather than reconciled, because which is right is decided by whether
   the CPU pins actually behave as GPIO on silicon.

## 3. Named gaps — what this phase measured and deliberately did not close

| gap | size | owner |
|---|---|---|
| **Used-pin IO configuration.** `IOBA`/`IOBB` longval fuses of pins at least one side instantiates, plus values reachable by `DRIVE`/`PULLMODE`. Not the base mask's unused-IO default class — a used pin's IO config is the PR #423 class and is never masked. | 333 bits / 167 tiles `io_used_pin_config`, 309 bits / 154 tiles `io_nondefault_config`, whole-device | **Phase 3 (W-IO)** |
| **`sspi` moves 20 further used-pin IOB bits** apicula does not emit — same class as the row above, found by the dual-purpose sweep. | 20 bits | **Phase 3 (W-IO)** |
| **`-use_mode_as_gpio` has no apicula flag.** The option exists in `gw_sh`; `gowin_pack` has no counterpart, so the sweep could not reach that point at all. A named absence, not a failure. | 1 option | **Phase 3 or 8** |
| **The `CPU_AS_GPIO` disagreement** (above). | 2 bits apicula sets, 0 the vendor moves | **Phase 9** |
| **27 unmapped port bits** of 911 — all outputs: 26 `.dat` sentinel slots plus one bit past the end of `Ae350SocIns`. They get unroutable placeholder wires so nothing silently binds them. | 27 of 911 | recorded; no owner needed unless a design uses them |
| **Head order: four of seven clock taps stay ordinal.** The map holds **seven** `CLK`-class input taps (`INTEG_TCK` is the seventh). `CORE_CLK` and `APB_CLK` are resolved to their taps by the net's own source; the other four are driven through a global buffer that decodes to no cell, so their port assignment is positional, not proven. Resolving them needs a design that drives them separately *and* a decodable driver per net. | 4 of 7 | **Phase 3** (with the IO/clock work) |
| **No dedicated PLL→`CORE_CLK` edge is modelled at all** — see `A18`. The model is silent, not wrong; what it owes is one dedicated edge **per PLL site**. | 2 sites | **`P2.T10`'s successor, Phase 6** |
| **Per-design AE350 interface-band bits.** Two designs set 77 bits over 9 tiles and 3 bits at one tile respectively, intersecting in zero — so they are a function of the design, not of the block. Recorded as evidence about two designs, not as a fuse set. | 77 + 3 bits | recorded |

## 4. Deviations — amendment lines owed to `spec.md`

Numbering continues from `A17`.

- **`A18` — `S19`'s "`PLL_R[0].CLKOUT1 → CORE_CLK` modelled as a fixed,
  non-routable connection" is refuted by measurement and is restated.**
  `P2.T38` varied the PLL placement (2 vendor runs) and the vendor built at
  `PLL_L[0]` with the **same** zero-delay hop into `CORE_CLK`
  (`tNET 0.000 ns` from either site), so `PLL_R[0]` is the reference design's
  convention, not a property of the silicon, and a chipdb modelling one
  exclusive edge would be **wrong**. Restated as: *the core clock reaches the
  block over a dedicated, zero-delay route from a PLL output, available from
  either PLL site; the fabric tap the `.dat` assigns to `CORE_CLK` exists and
  the vendor never uses it.* The database models the fabric tap and no PLL
  edge; the per-site edge is a named gap (§3). Applied to `S19`, `V18` and
  `spec-primitives.md` §5.
- **`A19` — the fuse-set validation step names a file that does not exist.**
  `evidence/ae350/fuse-set.md` was never written; the measurement lives in
  `e1-138c.md` (the settling observation) and `config-fuses-138c.md` (the
  77-bit table). `check_criteria.py --ae350` already reads those two. The
  `AE350-FUSE-SET: <n> bits` line form is withdrawn — the answer is zero and
  the enumeration is of a *design's* bits, not the block's.
- **`A20` — `D50`'s mandatory checkpoint is `rescope.md`, not
  `checkpoint-45.md`.** The phase finished at 8 vendor runs, far below 45,
  which is `F8`'s "written at phase end if the phase finishes below it" path.
  The re-scope ledger is that document: six numbered `RESCOPE-VERDICT`
  revisions, the last closing at *Runs used 8 of 8*. A test asserts the
  revisions are unique and gapless and that the current one agrees with
  `evidence/_budget/ae350-runs.tsv`.
- **`A21` — the phase-close E2E spends zero vendor runs.** Its scenario is one
  design through both flows and one diff; the vendor half was still on disk
  from `p2t23-ae350-row2`, so the open half was rebuilt at the close tip and
  diffed against the preserved bitstream. Same comparison, one flow
  re-executed. A vendor artefact that is preserved is evidence; re-buying it
  is not more true.
- **`A22` — the E2E's `grep -c 'AE350_SOC'` on the unpacked netlist is void
  by measurement.** It expects `1` on the premise that the block leaves a fuse
  trace; the fuse set is **zero**, so `AE350_SOC` is a non-fuse-backed bel
  (as `EMCU` is upstream) and nothing in the bitstream can name it. The check
  that carries the same weight is `c1`: 1780/1780 placed cells recovered, 6
  not fuse-backed. What the example path does prove is recorded instead —
  yosys `1 AE350_SOC`, nextpnr `AE350_SOC: 1/1 100%`, `make` exit 0.
- **`A23` — DONE-STD clause (d) ships two `tangmega138k` examples, not
  three.** `ae350-emb-tcm.v` (the `AE350_SOC` row) and `dualpin.v` (the
  dual-purpose row). `AE350_RAM` gets none and can get none: its row closed
  `refused` — the die has no such resource — so no example of it can build.
  The Makefile says so at the point where the third target would have been.
- **`A24` — `S19`'s 637 entries are a table *length*, and the tables are empty
  on GW5.** All 637 `McuIns`/`McuOuts` slots in the 138C `.dat` read
  `(-1,-1,-1)` (control: a GW1NS-4 reads 224/302 live), so the legacy
  triple-portmap block is unused on this family and covers 0 of 911 bits. The
  port map that shipped comes from the `Ae350SocIns`/`Ae350SocOuts` tables
  found in the same file, which bind **884 of 911**. `S19`'s bel clause is
  reached; its "built from `McuIns`/`McuOuts`" wording is not literally true
  and is restated as "built from the `.dat`'s AE350 port tables".

**Standing amendments, unchanged from Phase 1** and re-applied here rather
than re-numbered: `check_criteria.py` takes its arguments positionally with
`--phase <n>` and has no `--chipdb` flag; `V20`'s `git -C` target is `$OTC`,
not `$FL`, since `C10` moved evidence into the submodule; the family
regression compares against `evidence/chipdb/chipdb-sha256.txt`. One new
consequence of `C10` worth stating: this phase bumps **three** gitlinks
(`apicula`, `nextpnr`, `open-toolchain`), where the blueprint's tree-clean
check names two.

## 5. What the phase close itself found and fixed

Five defects, none of them in the phase's own measurements — all in the
instruments and the record. Full detail in `validation.md` §Fixes.

1. Three evidence rows the admissibility checker could not read (a
   `diff_count` with non-`§6` keys, an artefact path spelled relative to the
   checkout, nine rows naming the vehicle instead of the primitive), plus the
   `D99` pruned-artefact marker those nine rows were missing. `56e9237`.
2. A **stale `chipdb-GW5AST-138C.bin`** (`0206b922`) at the exact path the
   installed `nextpnr-himbaechel` probes when no `--chipdb` is given. nextpnr
   loads a database by path and answers a `constids` mismatch with an
   assertion, not an error, so a stale twin is silently usable. Deleted and
   replaced by a link to the paired `85701f94`; guarded.
3. The **nextpnr build tree** was stale and aborted on the current database.
   Rebuilt at the close tip. The binary the rows were measured with (the
   installed `d63e552b`) is unaffected.
4. **Five apicula tests were red** — the `ae350` bound-bit constants said 398
   where the code binds 416, and the placeholder vocabulary had grown a
   second reason. Both commits that caused it (`654f5b4`, `6e58e8b`) landed
   red: the phase's one violation of *never land red*, and the phase gate is
   the first step that runs the suite. Fixed on `ae350/wire-map-reconcile-138c`.
5. **The wire map contradicted the database it was measured against** — 867
   bound bits and taps keyed the way the table lists them, against the
   database's 884 and the measured direction rule. Re-derived independently
   from `dat_parser`'s tables and corrected to 884/911; the derivation is now
   a committed tool (`tools/derive_ae350_wire_map.py`) instead of a one-off,
   which is how it went stale.
6. A **routing test pinned a Phase-1 archived `.bin`** against the current
   binary and aborted in the full gate. Repointed at the installed database —
   the only one that can be its pair.

## 6. Reproduction

```sh
export FL=/Users/alex/fine-line
export WT=$FL/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84
export OTC=$WT/open-toolchain
export PIPE=$FL/.atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84
export DS=/Users/alex/fine-line-data/open-toolchain-gw5ast
export PYTHONPATH=$WT/apicula
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib
export DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
export PATH=$FL/vendor/venv/bin:$DS/toolchains/nextpnr/bin:$PATH

# the criterion, and this phase's rows
python $OTC/tools/check_criteria.py --ae350 \
    --chipdb $WT/apicula/apycula/GW5AST-138C.msgpack.xz --evidence $OTC/evidence
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 2
python $OTC/tools/check_evidence.py  $PIPE/spec-primitives.md $OTC/evidence

# the E1 row, re-diffed against the preserved vendor bitstream (no vendor run)
R=$(mktemp -d); D=$DS/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000
cp $D/top.v $R/; cp $D/top-open.cst $R/top.cst; ln -s $D/run $R/run
cd $WT/apicula
python -m fuzz.gw5ast138c.harness.openflow --design-dir $R --shape ae350_soc \
    --chipdb $DS/toolchains/nextpnr/share/himbaechel/gowin/chipdb-GW5AST-138C.bin \
    --nextpnr $DS/toolchains/nextpnr/bin/nextpnr-himbaechel
python -m fuzz.gw5ast138c.harness.equiv --design-dir $R --shape ae350_soc \
    --level E1 --pnr-json $R/top_pnr.json

# clause (d): the examples, through the project's own path
make -C $WT/apicula/examples/gw5a ae350-emb-tcm-tangmega138k.fs dualpin-tangmega138k.fs

# the family regression (S3, §7.4)
python -m apycula.chipdb_builder GW5A-25A  -o /tmp/25a.msgpack.xz   # 60f1ba42…
python -m apycula.chipdb_builder GW5AT-60B -o /tmp/60b.msgpack.xz   # 615d4d03…

# the gates, as the close ran them
( cd $WT/apicula && GATE_SCOPE=full make gate )   # 7:02
( cd $WT/nextpnr && GATE_SCOPE=full make gate )   # 0:38
( cd $OTC        && GATE_SCOPE=full make gate )   # 0:10
( cd $WT         && GATE_SCOPE=full make gate )   # 0:10
```

## 7. The runs

Eight, all `ok`, all Standard 1.9.12.03, none `edu-provisional`
(`evidence/_budget/ae350-runs.tsv`).

| batch | slug | what it bought |
|---|---|---|
| `p2t26-tilewires` | ae350 | the block's footprint: all 149 ports placed and routed at once, in 15 s — which retired `EC5`'s 149-run premise |
| `p2t26-baseline` | ae350 | its differential baseline |
| `p2t23-ae350-row` | ae350 | the first `E1` attempt; found the endpoint-digest defect |
| `p2t23-ae350-row2` | ae350 | **the `E1` row**, and the second design that settled the fuse-set question |
| `p2t25-ae350-ram-soc` | ae350-ram | `AE350_RAM` beside an `AE350_SOC` — refused |
| `p2t25-ae350-ram-solo` | ae350-ram | `AE350_RAM` on an otherwise empty die — refused again, so it is the primitive |
| `p2t38-pll-l` | ae350 | `CORE-CLK-ROUTE: PLL_L[0] also legal` |
| `p2t38-ddr-clk` | ae350 | `DDR-CLK-ROUTE: PLL_R[0].CLKOUT0 -> DDR_CLK`, 2.091 ns over the ordinary network |

Ten further vendor runs were spent on the dual-purpose sweep under its own
sub-ledger (`ae350-dualpins`, 13 of 10 authorised — three bought the shape:
a bare-DFF vehicle cannot reach `E1`, because the `.tr` carries no `CLS`
column without a reg-to-reg path).
