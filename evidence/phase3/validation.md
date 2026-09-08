# Phase 3 — Validation (`blueprints/P3-io-iologic.md` "## Validation", verbatim)

Run at the phase close, in the foreground, with `$GOWINHOME` =
`/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA` (Standard 1.9.12.03,
licensed — `edu-provisional: false` on every row this phase wrote).

| # | step | result |
|---|---|---|
| 1 | `V14` per-primitive structural facts (`S10`, `S11`, `S12`, `S15`) | **PASS** |
| 2 | `V16` named refusals | **PASS** |
| 3 | `V12a --classes io` | **PASS, amended** — `0/0 arcs` is the measured answer, not an absent arc block (`A31`) |
| 4 | evidence admissibility (pre-`V9`) | **PASS** |
| 5 | `S3` family regression | **PASS** — after a regression this step found and this phase fixed |
| 6 | the phase's example set builds | **PASS** |
| 7 | `V20` storage hygiene | **PASS** |
| 8 | attribution and branch shape | **PASS** |

---

## 1. `V14` — per-primitive structural facts

```sh
test "$(shasum -a 256 $FL/apicula/apycula/GW5AST-138C.msgpack.xz | cut -d' ' -f1)" \
   = "$(grep -m1 '^chipdb_sha256:' $OTC/evidence/oddr-iddr/summary.md | awk '{print $2}')" \
   && echo OK-chipdb-fresh || { echo FAIL-chipdb-stale; exit 1; }

python $OTC/tools/check_criteria.py $PIPE/spec-primitives.md $OTC/evidence \
    --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz --phase 3
```

```
OK-chipdb-fresh
clause-d: deferred to Phase 7 (D65)
CRITERIA ok: 13/13
```

chipdb under test: `f2f92b0448b7218b969237f150c694039bad9e0d4f0f17dfdbfde5108d0efd6c`,
recorded as the literal `chipdb_sha256:` line of `evidence/oddr-iddr/summary.md`,
so the gate cannot pass against an earlier phase's chipdb (`F7`).

**PASS.** No `FAIL` line. All 13 Phase-3 rows satisfy DONE-STD, `clause (d)`
deferred to Phase 7 as `D65` specifies.

## 2. `V16` — named refusals

```sh
cd $FL/apicula && python -m pytest tests -k "unsupported_error" -q
```

```
13 passed, 872 deselected
```

**PASS.** `0 failed`. The suite names
`tests/test_gw5ast138c_clocking.py::test_iologic_before_hclk_unsupported_error_138c`
— asserted against Phase 1's synthetic no-HCLK fixture and never against the
live 138C chipdb (`F16`) — plus the `OSER16`/`IDES16` guards, which this phase
**changed in kind**: `P3.T16` refuted the expected vendor refusal, so what the
tests now pin is that the refusal is *gone*
(`test_oser16_refusal_is_gone_on_gw5a`) and that the implementation's extent is
claimed only for the die it was measured on
(`test_io16_extent_is_claimed_for_the_measured_die_only`).

## 3. `V12a --classes io` — the IO/IOLOGIC L0 arc band

```sh
python $OTC/tools/check_timing_l0.py --classes io --sdf <the oddr-iddr SDF> \
    --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz
```

```
L0 ok: 0/0 arcs within ±10%, 0 exceptions listed
(VOLTAGE 0.93:0.90:0.87) (PROCESS "best=0.65: nom=1.0: worst=1.8") (TEMPERATURE 85:25:0)
grade: C1/I0 -- derived (1.25 x C2/I1, P0.T35 -- NOT measured)
io: 0 chipdb arcs and 0 nextpnr arcs BY MEASUREMENT (P3.T32) -- the .tm blocks at
0x3278 (IO buffers) and 0x306c (IREG/OREG) are byte-identical to GW2A-18/-55/
GW2AR-18, i.e. inherited and never characterised for GW5A, and the vendor's own
138C SDF contradicts them: OBUF I->O is 2.528/2.737 ns against a whole-block
maximum of 0.819 ns, and no clock-to-out candidate lands within +/-10% of ODDR
CLK->Q 1.160/1.146 or IDDR CLK->Q0/Q1 0.572/0.486.
unmapped: 8 SDF arcs have no nextpnr model arc: ODDR/dut CLK->Q0, ODDR/dut CLK->Q1,
IBUF/clk_ibuf I->O, IBUF/din_ibuf I->O, IBUF/d1_ibuf I->O, OBUF/dout_obuf I->O,
OBUF/dout2_obuf I->O, OBUF/dout3_obuf I->O
```

**PASS, with the blueprint's expectation amended (`A31`).** The blueprint reads
`0/0 arcs` as "`P3.T33`'s arc block is absent". `P3.T32` measured why it is
absent: this die's `.tm` IO and IOLOGIC blocks are byte-identical to three GW2A
parts, i.e. inherited and never characterised, and the vendor's own SDF
contradicts them by a factor of three. Emitting arcs from that table would put
an invented model into the chipdb where a named absence belongs. The eight
vendor arcs are enumerated as `unmapped`, not silently dropped.

## 4. Evidence admissibility (pre-`V9`)

```sh
python $OTC/tools/check_evidence.py $PIPE/spec-primitives.md $OTC/evidence
```

```
RUNS: 28 files, 351 rows, 351 valid
EVIDENCE ok: 348 rows, 17 pending, 0 blank, 0 missing artifacts
0 admissibility findings
```

**PASS.** Re-run **after** the storage-hygiene deletion of step 7, which is the
only proof that no cited artefact was removed.

## 5. `S3` family regression on the selected edition

```
OK GW5A-25A  /Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
OK GW5AT-60B /Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
SKIP second-edition /Users/alex/Desktop/GowinIDE.app/Contents/Resources/Gowin_EDA
GW5A-25A  60f1ba427f964feab3048f5dca82dc075acf9374a456476919202626d1335564
GW5AT-60B 615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8
P3-FAMILY-REGRESSION ok: 2/2 builds, 0 diffs, 2 skipped
```

Both byte-identical to the values the previous phase closed on. Plus the
example control the blueprint's own `S3` wording implies: one 25A design
(`oddr-tlvds` — ODDR and TLVDS, the two primitives this phase touched most)
synthesised and placed once, then packed twice, with this branch's `gowin_pack`
and with the Phase-2 close checkout's:

```
head a6d984e97d9660e55836de08879f4a375424f9c0d8a2b58cfa094f1553ec08a2
base a6d984e97d9660e55836de08879f4a375424f9c0d8a2b58cfa094f1553ec08a2
BYTE-IDENTICAL
```

**PASS — but only after this step found a real regression and the phase fixed
it.** The first run of this step returned `d513cda5…` / `730dade3…`, not the
baselines. Two 138C measurements had been generalised to the whole Arora V
family without a run behind them, and nothing else in the phase would have
caught either:

1. the 16-bit gearbox extent, which put **115 `OSER16` and 115 `IDES16` bels on
   the GW5A-25A** that no vendor run ever asked about;
2. the `B`-half IOLOGIC fuse displacement, which moved **where a shipped device
   writes real fuses** on 7 tile types of the 25A and 60B.

Both are now claimed for `GW5AST-138C` alone (`chipdb.has_gw5_io16`), each with
the one vendor run per die that would widen it named, and both baselines are
restored. Guards: `tests/test_family_regression_gw5a.py` (6),
`tests/test_unsupported_error_io.py::test_io16_extent_is_claimed_for_the_measured_die_only`.

## 6. The phase's example set builds

```sh
cd $FL/apicula && make -C examples/gw5a -j4 tangmega138k
ls examples/gw5a/*-tangmega138k.fs | wc -l
```

```
exit 0
23
```

**PASS.** 57.6 s wall clock, **0 vendor runs**. 6 inherited targets + **17
added by this phase**, one per primitive that closed at `E1` (`ODDR`, `IDDR`,
`OSER4`, `OSER8`, `OSER10`, `OVIDEO`, `IDES4`, `IDES8`, `IDES10`, `OSER16`,
`IDES16`, `TLVDS_IBUF`, `TLVDS_OBUF`, `TLVDS_TBUF`, `TLVDS_IOBUF`) plus the
static `IODELAY` and the `ADCLRC`. Each design and each `.cst` is **generated
from the shape file that measured its row** (`$OTC/tools/emit_io_examples_138c.py`),
so an example cannot drift away from the evidence that justifies it. A row that
closed `refused:` carries its error-text unit test instead of an example, per
`D65` clause (d). `examples/gw5a/tangmega138k.cst` is byte-identical to its
pre-phase first 44 lines and the `primer25k:` list still has exactly 44 targets
(`tests/test_examples_gw5a_138c.py`, 4).

## 7. `V20` — storage hygiene

```
OK-evidence-gitignore
OK-manifests
OK-no-binaries
```

**PASS.** 3 027 uncited vendor intermediates deleted (`*.pr`, `*.binx`,
`run/impl/pnr/run.bin`, `*.html`) — **24.42 GB**, datastore 41 GB → 18 GB. Every
one of the 1 650 artefacts an evidence row cites by sha256 was kept, which is
what step 4's `0 missing artifacts` re-verifies. Detail:
`evidence/_runs/p3-storage-hygiene.md`.

## 8. Attribution and branch shape

```sh
for r in apicula nextpnr; do
  git -C $FL/$r log --format=%B <base>..HEAD | grep -cE 'Co-Authored-By|Generated with'
done
```

```
0
0
```

**PASS.**
