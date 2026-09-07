# Phase 2 (AE350) — Validation

`blueprints/P2-ae350.md` §5, run at the phase close on `epic/gw5ast138c`
(apicula `45a5a19`, nextpnr `97d54b35`, open-toolchain `main`), Standard
1.9.12.03, `installs_available: 1`. Every command below was run verbatim
except where an **Amended** note says otherwise and why; each amendment is
also an `A`-line in `phase-report.md`.

Preamble: `spec.md` §12 (`GOWINHOME` Standard, both `DYLD_*`, `$OTC` the
open-toolchain submodule, the `vendor/venv`). Two deviations standing since
Phase 0/1: the venv is `/Users/alex/fine-line/vendor/venv`, and `$FL` for
submodule work is the pipeline **worktree**
`/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84`,
not the umbrella checkout (`C10`). **Zero vendor runs were spent by this
validation** — the one step that would have needed one is answered from the
preserved vendor bitstream instead (§E2E).

| step | criterion | exit | verdict |
|---|---|---|---|
| 1 | `V18` — `S19` non-hardware half | 0 | PASS `AE350 ok: 4/4` |
| 2 | `V14` — this phase's rows (`--phase 2`) | 0 | PASS `CRITERIA ok: 3/3` |
| 3 | reconciliation verdict present and unique | 0 | PASS (`1`) |
| 4 | the core clock is not routable | 1 | **FAIL as written** — the model carries no such edge, by measurement (`A18`) |
| 5 | the fuse set is measured, not assumed | 2 | **FAIL as written** — path amended, result PASS (`A19`) |
| 6 | no row blank, "pending" or `blocked:` | 0 | PASS (`0 0 0`, then `EVIDENCE ok`) |
| 7 | the dual-purpose row has nine `E1` points | 0 | PASS (`9 9`) |
| 8 | the unit-test suites | 0 | PASS |
| 9 | `S3` family regression | 0 | PASS (25A and 60B byte-identical) |
| 10 | `V20` storage hygiene | 0 | PASS |
| 11 | budget box (`D50`) | 0 | PASS (16 rows, 8 vendor runs, box 90) — checkpoint path amended (`A20`) |
| E2E | one design, both flows, one diff | 0 | PASS `EQUIV E1 ok`, 0 vendor runs (`A21`) |
| E2E | the same design through the example path | 0 | PASS build + place; unpack grep void by measurement (`A22`) |

---

## 1. `V18` — `S19`'s non-hardware half

```sh
python $OTC/tools/check_criteria.py --ae350 \
    --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz --evidence $OTC/evidence
```

```
ok: bel exists: 416 in / 495 out bits at (0, 159)
ok: CORE_CLK non-routable: modelled tap present; evidence records the fixed PLL_R[0] route
ok: fuse set: e1-138c.md: no bit marks the block's presence (zero, measured)
ok: reconciliation: reconciliation.md records the 637-entry reconciliation
AE350 ok: 4/4
```

exit 0. **PASS**, with one thing the line does not say and step 4 below does:
this checker's second clause asserts that a modelled `CORE_CLK` tap exists and
that the evidence *records* a fixed route. It does not assert an exclusive
`PLL_R[0]` edge in the database, because `P2.T38` measured that no such
exclusivity exists.

## 2. `V14` — this phase's rows

**Amended**, the same way Phase 1 amended it: the blueprint's invocation
passes `--chipdb`/`--evidence`; `check_criteria.py` takes the pair
positionally and has no `--chipdb` flag (`spec.md` §12 as corrected by
`F31(blueprints)`), and every phase runs the scoped `--phase <n>` form.

```sh
python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence --phase 2
```

```
clause-d: deferred to Phase 7 (D65)
CRITERIA ok: 3/3
```

exit 0. **PASS** — `AE350_SOC`, `AE350_RAM` and Dual-purpose pins. Clause (d)
is deferred to Phase 7 by `D65` even though this phase authored the examples
(§E2E); `--enable-clause-d` is Phase 7's switch, not this phase's bar.

## 3. The reconciliation verdict exists and is unique

```sh
grep -c '^RECONCILIATION-VERDICT: ' $OTC/evidence/ae350/reconciliation.md
```

```
1
```

**PASS.** The verdict reads `0/911 wires covered` — the `McuIns`/`McuOuts`
triple tables that `S19` names are **empty on GW5** (`P2.T03`: 637 slots, all
`(-1,-1,-1)`, against a live GW1NS-4 control), so the legacy block covers
nothing. The port map that the phase actually shipped comes from the
`Ae350SocIns`/`Ae350SocOuts` tables `P2.T08`/`P2.T08b` found instead. Both
facts are recorded; the verdict line is about the first.

## 4. The core clock is not routable

Run verbatim, the blueprint's snippet **fails at its first assertion**:

```
KeyError: 'fixed_clk'
```

exit 1. **FAIL as written, and the failure is the truth.** There is no
`fixed_clk` entry in `extra_func[(0, 159)]['ae350']` (its keys are
`config_tiles`, `config_ttyps`, `ins`, `outs`, `unmapped`) because `P2.T38`
measured the premise away: the dedicated zero-delay hop from PLL output to
`CORE_CLK` exists from **both** PLL sites —

```
  68.107   6.569   tCL   RR  1   PLL_L[0]   u_pll/CLKOUT1
  68.107   0.000   tNET  RR  1   R0C160     u_ae350/CORE_CLK
```

— so `PLL_R[0]` is the reference design's convention, not a property of the
silicon, and a chipdb that modelled one exclusive edge would be wrong. The
model is **silent** here, not wrong; what it owes is one dedicated edge per
PLL site, which is a named gap (`phase-report.md`). The substituted check,
which does pass, is the one the shipped checker makes: the `CORE_CLK` fabric
tap is modelled and reaches `(0, 87, 'CLK1')`, and the vendor never uses it.

```sh
python $OTC/tools/check_criteria.py --ae350 ...   # clause 2, above
grep -E '^CORE-CLK-ROUTE: |^DDR-CLK-ROUTE: ' $OTC/evidence/ae350/core-clock.md
```

```
CORE-CLK-ROUTE: PLL_L[0] also legal
DDR-CLK-ROUTE: PLL_R[0].CLKOUT0 -> DDR_CLK
```

## 5. The fuse set is measured, not assumed

**Amended path.** `evidence/ae350/fuse-set.md` does not exist: the
`P2.T24`/`P2.T23` measurement is recorded in `e1-138c.md` (the settling
observation) and `config-fuses-138c.md` (the 77-bit table of the one design
that has bits). Run verbatim, `grep` exits 2 (`No such file or directory`).

```sh
grep -c 'no bit marks the block.s presence' $OTC/evidence/ae350/e1-138c.md
```

Result: the two AE350 designs' interface-band bit sets intersect in **zero**
bits (77 over 9 tiles against 3 at one tile), so no bit marks the block's
presence, `get_AE350_SOC_fuses` returns `[]` as `EMCU`'s does, and
`AE350_SOC` is a non-fuse-backed bel. **The fuse set is zero, measured.**
`check_criteria.py --ae350` reads exactly this and reports it as clause 3.

## 6. No row is blank, "pending", or `blocked:`

```sh
grep -c 'blocked:' $OTC/evidence/ae350/runs.jsonl \
    $OTC/evidence/ae350-ram/runs.jsonl $OTC/evidence/dualpin/runs.jsonl
python $OTC/tools/check_evidence.py $PIPE/spec-primitives.md $OTC/evidence
```

```
.../ae350/runs.jsonl:0
.../ae350-ram/runs.jsonl:0
.../dualpin/runs.jsonl:0
EVIDENCE ok: 190 rows, 30 pending, 0 blank, 0 missing artifacts
0 admissibility findings
```

**PASS**, and only after four defects this validation found and fixed — a
`diff_count` carrying non-`§6` keys, an artefact path the resolver could not
follow, nine rows naming the vehicle instead of the primitive under it, and
the pruned run trees those nine rows still pointed at. Each has a guard in
`tools/tests/test_evidence_admissibility_guards.py`; the fixes are commit
`56e9237`.

## 7. The dual-purpose row has nine `E1` points

```sh
python -c "import json; rows=[json.loads(l) for l in open('$OTC/evidence/dualpin/runs.jsonl')]; \
print(len(rows), sum(1 for r in rows if r['level']=='E1'))"
```

```
9 9
```

**PASS.** Seven `ok`, two `refused` — `reconfign` refused by the vendor,
`i2c` refused by `gowin_pack` (no I2C configuration pin on this device) —
both terminal verdicts with the tool's exact error text, which is a
deliverable and not a hole.

## 8. The unit-test suites

```sh
cd $FL/apicula && python -m pytest tests -k "ae350 or dualpin" -q
```

```
82 passed, 476 deselected in 7.39s
```

**PASS — 0 failed**, against the blueprint's bar of at least 30 collected;
82 is what the phase's named tests amount to. Five of them were **red at the
start of this validation** and are the fourth defect it forced (§Fixes): the
`ae350` constants said 398 bound input bits where the code binds 416, and the
placeholder vocabulary had grown a second reason. Both commits that caused it
(`654f5b4`, `6e58e8b`) landed red — the phase's one violation of "never land
red", found here because this is the first step that runs the suite.

The two dual-purpose namespace tests `P2.T30` locks in are inside that run:

```sh
cd $FL/apicula && python -m pytest tests -k dualpin -q     # 0 failed
```

## 9. Family regression (`S3`, §7.4)

```sh
python -m apycula.chipdb_builder GW5A-25A  -o /tmp/25a.msgpack.xz
python -m apycula.chipdb_builder GW5AT-60B -o /tmp/60b.msgpack.xz
shasum -a 256 /tmp/25a.msgpack.xz /tmp/60b.msgpack.xz
```

```
60f1ba427f964feab3048f5dca82dc075acf9374a456476919202626d1335564  /tmp/25a.msgpack.xz
615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8  /tmp/60b.msgpack.xz
```

**PASS — 0 differences.** Both equal the values recorded at the Phase-1 close
in `evidence/chipdb/chipdb-sha256.txt` (`GW5A-25A 60f1ba42…`,
`GW5AT-60B 615d4d03…`). No AE350 edit leaked out of its device gate. Build
times 4.6 s and 5.5 s.

**Amended**, in the same way Phase 1 amended it: the blueprint's `diff`
against `evidence/ae350/chipdb-sha256.md` names a file this phase never
created; the recorded baseline lives in the one ledger `P0.T15b` established,
`evidence/chipdb/chipdb-sha256.txt`, and that is what the comparison is
against.

## 10. `V20` — storage hygiene (`D41`)

```sh
git -C $OTC check-ignore -q $OTC/evidence/_runs/x.fs && echo OK-evidence-gitignore
test -f $OTC/vendor-gowin.sha256 && test -f $OTC/ide-share-device.sha256 && echo OK-manifests
git -C $OTC ls-files evidence | grep -E '\.(fs|vo|tr|sdf|fse|dat|tm)$' \
  && echo FAIL-binaries-committed || echo OK-no-binaries
```

```
OK-evidence-gitignore
OK-manifests
OK-no-binaries
```

**PASS.** **Amended**: `git -C $FL …` in the blueprint is `git -C $OTC …`
here — evidence and its ignore rules moved into the open-toolchain submodule
at `C10`/`D80`, so the umbrella no longer indexes those paths.

## 11. Budget box (`D50`)

```sh
python -c "n=sum(len(open(f'$OTC/evidence/{s}/runs.jsonl').readlines()) \
    for s in ['ae350','ae350-ram','dualpin']); print(n); assert n <= 90"
```

```
16
```

**PASS**, well inside the box: 16 evidence rows over **8 vendor runs**
(`evidence/_budget/ae350-runs.tsv`, cumulative 8), against a cap of 90 and a
`P2.T26` re-scope cap of 8. **Amended**: `evidence/ae350/checkpoint-45.md`
does not exist and cannot — the phase never reached 45 runs, which is the
`F8` "finished below it" path. The mandatory written checkpoint is
`evidence/ae350/rescope.md`, a numbered ledger whose latest entry closes it:

```sh
grep -c '^RESCOPE-VERDICT' $OTC/evidence/ae350/rescope.md   # 4
```

`RESCOPE-VERDICT (rev 6, … the phase close): … Runs used 8 of 8, 0 remaining.`
`tools/tests/test_ae350_wire_map.py` asserts the revisions are unique and
gapless and that the current one's count equals the ledger's.

## E2E — one design, both flows, one diff

**Amended, and the amendment is what makes it free.** The blueprint's E2E
spends a vendor run to rebuild the `ae350_soc` design under `gw_sh`. That
run's output is still on disk from `p2t23-ae350-row2`
(`$DATASTORE/ae350-row/batch2/p2t23-ae350-row2-ae350_soc-0000/run/`), so the
open half was rebuilt at the phase-close tip and diffed against the preserved
vendor bitstream — the same comparison, one flow re-executed instead of two:

```sh
python -m fuzz.gw5ast138c.harness.openflow --design-dir <repro> --shape ae350_soc \
    --chipdb $DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/chipdb-GW5AST-138C.bin \
    --nextpnr $DATASTORE/toolchains/nextpnr/bin/nextpnr-himbaechel
python -m fuzz.gw5ast138c.harness.equiv --design-dir <repro> --shape ae350_soc \
    --level E1 --pnr-json <repro>/top_pnr.json
```

```
STEP yosys returncode=0 wall_clock_s=0.567
STEP nextpnr returncode=0 wall_clock_s=5.396
STEP gowin_pack returncode=0 wall_clock_s=1.929
BITSTREAM top.fs 34668145 f623fd894f2bdac88c6327d92800fa590ec297ee9041d48dbd726128913dc892
PROVENANCE apicula_sha=45a5a192 nextpnr_sha=97d54b35 chipdb_sha256=85701f94

EQUIV E1 ok
DIFF_COUNT cells=0 attrs=0 conns=0
PIPS diff=1974943 (statistic, never a verdict term)
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
E1 placement level=E1 constrained=9 matched=3 mismatched=0 unobserved=6
DECODE_CHECK c1=ok c2=ok (c1 recovered 1780/1780 placed cells, 6 not fuse-backed)
MASK sha256=59147bfc… entries=6
```

**PASS.** The row's verdict reproduces at the phase-close tip: three clean
sets, an empty residual, `c1` recovering every placed cell and `c2`
byte-identical. The open bitstream's sha256 differs from the one the row
recorded (`6d91d0c8…`) at identical size — the packer moved between the two
builds — which is exactly why the verdict is a **diff of the two flows** and
never a hash comparison.

## E2E — the same design through the example path

```sh
make -C $FL/apicula/examples/gw5a ae350-emb-tcm-tangmega138k.fs
shasum -a 256 .../ae350-emb-tcm-tangmega138k.fs
gowin_unpack -d GW5AST-138C -o /tmp/ae350-unpacked.v .../ae350-emb-tcm-tangmega138k.fs
grep -c 'AE350_SOC' /tmp/ae350-unpacked.v
```

```
make exit 0, 2.3 s
066d0869b42a91d730d974f418cff7b5d025b71d9734e0a595a92484af93b1aa  ae350-emb-tcm-tangmega138k.fs
Info:            AE350_SOC:       1/      1   100%
gowin_unpack exit 0, 288418 lines
0
```

**PASS on the build, and the `grep -c` expectation is void by measurement.**
`make` exits 0, yosys reports `1 AE350_SOC`, nextpnr places `AE350_SOC 1/1`
and the bitstream packs — the example path is not harness-only. But
`grep -c 'AE350_SOC'` printing `1` presumes the block leaves a fuse trace,
and step 5 measured that it leaves **none**: `AE350_SOC` is a non-fuse-backed
bel (`equiv.NON_FUSE_BACKED_BELS`), exactly as `EMCU` is upstream, so nothing
in the bitstream can name it and `gowin_unpack` cannot recover it. The check
that carries the same weight, and passes, is `c1` in the diff above:
1780/1780 placed cells recovered, 6 not fuse-backed.

---

## Fixes this validation forced

1. **Evidence admissibility, four defects** (§6) — `56e9237`.
2. **A stale `chipdb-GW5AST-138C.bin`** (`0206b922`, 32 931 799 B) under
   `$DATASTORE/toolchains/nextpnr/share/nextpnr/himbaechel/gowin/`, which is
   the path the installed binary probes when no `--chipdb` is passed. nextpnr
   loads a database by path and never checks that its constids still match
   the binary, so a stale twin is silently usable. Replaced by a hard link to
   the current `85701f94…`; guarded by
   `test_installed_chipdb_bins_are_one_database`.
3. **The `nextpnr` build tree was stale** — `$FL/nextpnr/build/nextpnr-himbaechel`
   (03:37) aborted on the current database with
   `Assertion failure: int(ctx->idstring_idx_to_str->size()) == idx (idstring.cc:46)`,
   the signature of a `constids` change against an older `.bin`. Rebuilt at
   the phase-close tip; it now places the `big-shift` example clean
   (`117 warnings, 0 errors`). The binary the phase's rows were measured with
   is the installed `d63e552b…`, which is unaffected.
4. **The re-scope ledger's run count** was three revisions behind the budget
   ledger (rev 5 said 6 of 8; `P2.T38` had since spent 2). Rev 6 closes it at
   8 of 8, and the test now reads the current revision instead of the first.

5. **The wire map contradicted the database it was measured against.**
   `wire-map-138c.json` recorded 867 bound bits with each tap keyed the way
   the `.dat` table lists it; the shipped chipdb binds 884 and takes a tap's
   direction from the *wire* (`6e58e8b`: `F/Q/OF` end no pip and are the
   block's outputs; `A-D/CE/CLK/LSR` are pip destinations and are its
   inputs). Re-derived from `dat_parser`'s tables — 416 of the 518
   `Ae350SocOuts` records name pip-destination wires, exactly the input-bit
   count, and the 437 pip-diff-confirmed taps split 415 input / 22 output —
   and the artefact corrected to **884/911 bound** (inputs 416/416, outputs
   468/495, 27 unbound and all outputs). The derivation is now a committed
   tool, `tools/derive_ae350_wire_map.py`, which imports no `chipdb`, so the
   reconciliation test still compares two independent readings; a test
   asserts that independence. `64f537d` (open-toolchain), `c5d7842` (apicula).

---

## The gate

One full gate per repository, foreground, at the phase-close tip — `C12`'s
rule that the orchestrator runs the gate once per phase and no push runs one.

| repo | command | wall clock | result |
|---|---|---|---|
| apicula | `GATE_SCOPE=full make gate` | **7:02** | `GATE full: ok, 2 checks` — 475 passed, 6 skipped, 1 xfailed (fast) + 54 passed, 1 xfailed (heavy) |
| nextpnr | `GATE_SCOPE=full make gate` | **0:38** | `GATE full: ok, 0 checks` — `hclk-6block` 2/2, `arch-gen-deterministic` `bba=828038b9 chipdb=d6e00bdc`, `dcs-spines` 4/4 |
| open-toolchain | `GATE_SCOPE=full make gate` | **0:12** | `GATE full: ok, 3 checks` — 180 passed; `check_evidence.py`; `check_criteria.py --phase 0` |
| fine-line (umbrella) | `GATE_SCOPE=full make gate` | **0:12** | `GATE full: ok, 3 checks` — `CRITERIA ok: 14/14` |

The apicula gate was **red on its first run** and is the fifth defect this
close found: `test_clkdiv_routes_138c` pinned a `.bin` archived during
Phase 1 and ran it against the installed binary, which aborts —
`Assertion failure: int(ctx->idstring_idx_to_str->size()) == idx` — because
the AE350 `constids.inc` append since invalidated it. Repointed at the
installed database, the only one that can be that binary's pair, and re-run
green (`ae350/gate-chipdb-pin-138c`, merged as `ebef8e9`). One re-run, no
second failure.

PHASE2-GATE: pass
