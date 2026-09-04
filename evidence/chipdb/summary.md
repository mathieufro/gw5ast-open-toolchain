# P0.T15 — chipdb builds, six sha256s

## Result

3 of 6 required (device, install) builds succeed; 3 fail. `V2`'s Done-when ("no `FAIL`
line, six builds and six recorded sha256s") is **not met**. Both failure classes are in
files this task must not touch, so they are recorded as findings, not fixed here.

| install | device | outcome | sha256 | bytes | ide_version |
|---|---|---|---|---|---|
| std (1.9.12.03) | GW5AST-138C | OK | `2dba96ff41bdc669fe1937e78e2eb65a59d7b21afbf64693b33139695055f8d3` | 1155296 | 1.9.12.03 |
| std (1.9.12.03) | GW5A-25A | **FAIL** | - | - | 1.9.12.03 |
| std (1.9.12.03) | GW5AT-60B | **FAIL** | - | - | 1.9.12.03 |
| edu (1.9.11.03) | GW5AST-138C | OK | `14061ccac8a3bf880d50877cfb0042eb66f74122c30198c2a4ab8f3f00fd0d34` | 1154148 | 1.9.11.03 |
| edu (1.9.11.03) | GW5A-25A | **FAIL** | - | - | 1.9.11.03 |
| edu (1.9.11.03) | GW5AT-60B | OK | `9d1523737187c2b504f424ad03054e9b60ae4a0e0f84880a7999947e264d3fe8` | 395096 | 1.9.11.03 |

`test_chipdb_no_family_regression` (4 zero exits expected for 25A/60B x std/edu) would
observe **1 of 4**: only edu/GW5AT-60B exits 0.

## Failure signatures (both in files frozen for this task)

- **std GW5A-25A, std GW5AT-60B** - `apycula.fse_parser.FseShapeError: unknown table type
  ... table=drpfuse expected_row_width=10 found_row_width=30` at `fse_parser.py:381`
  (`read_one_file`), ide_version=1.9.12.03, shape_set=v1_9_11plus. This is a **different**
  table (`drpfuse`) from the `longfuse` desync `P0.T11`-`P0.T13` fixed; it does not
  reproduce on `GW5AST-138C` on the same install. `apycula/fse_parser.py` is frozen for
  `P0.T15` ("frozen once `P0.T13` closes - a build failure here is a `P0.T13` defect, fixed
  there and re-run") - recorded here, not fixed.
- **edu GW5A-25A** - `KeyError: -1` at `apycula/chipdb.py:2150`
  (`fse_create_adc`, `wire = wnames.wirenames[wire_idx]`), reached from
  `chipdb.from_fse` (`:4152`). `apycula/chipdb.py` is frozen **in its entirety** for this
  phase ("the ~90 device-literal gates ... belong to Phases 1-4. A Phase-0 edit here is an
  out-of-scope change"). Recorded here, not fixed. Preceded by many `row too big ...`
  warnings from the same build (ADC/DRP-table parsing), same shape as the std-side
  `drpfuse` failure - plausibly one root cause surfacing two ways, but not diagnosed
  further (would require editing the frozen files).
- **std GW5AT-60B** on the same run also hits the `drpfuse` `FseShapeError`; **edu
  GW5AT-60B** does not - so the 60B failure is std-only, the 25A failure is both-install.

## Determinism (`spec.md` section 8.3 / `D`'s claim) - finding: mismatch, not a silent pass

`GW5AST-138C` was built **three separate times** from the **same** std install
(1.9.12.03) across this task's runs, and once more on edu. Every rebuild produced a
**different** sha256, including after decompressing the `.xz` and re-hashing the raw
msgpack bytes (ruling out an `.xz` timestamp/compression artefact):

| run | install | sha256 (compressed) | bytes | sha256 (decompressed) |
|---|---|---|---|---|
| 1 (recorded above) | std | 2dba96ff...5f8d3 | 1155296 | 2fb615c5...e4a60 |
| 2 (determinism check) | std | a170503c...4faa2 | 1152092 | 704944a8...269f6 |
| 3 (V2-verbatim run) | std | 849f5bfe...bd75a | 1152964 | not re-checked |
| 4 (V2-verbatim run) | edu | 70f263c6...0eddb | 1147020(shared file) | not re-checked |

`GW5AT-60B` (edu) shows the same pattern: `9d152373...e3fe8` (395096 B, this task's first
build) vs `6a22ef41...057b0c` (394760 B, the V2-verbatim run) - a different device
confirming the non-determinism is not 138C-specific.

**Finding**: `chipdb_builder` output is not byte-for-byte reproducible across runs from
the same install, contradicting the reproducibility assumption implicit in "record the
sha256" as a stable fingerprint. Root cause not investigated (would touch frozen files /
is out of this task's scope); likely a non-deterministic iteration order (dict/set) inside
`chipdb.py`'s fse-to-Device conversion. Flagging for the owner / a later phase.

## test_chipdb_138c_nonempty

Verified directly (not via a checked-in test, since `tests/` is not in this task's file
list): `std/GW5AST-138C.msgpack.xz` is 1155296 bytes (> 1,000,000) and
`apycula.chipdb.load_chipdb(path)` returns a `Device` with a non-empty `chip_flags`
attribute (`['HAS_SP32', 'HAS_PINCFG', 'HAS_DFF67', 'HAS_CIN_MUX', 'NEED_BSRAM_RESET_FIX',
'NEED_CFGPINS_INVERSION', 'HAS_5A_DSP']`) - semantically equivalent to the spec'd
"msgpack-loading it yields a dict with >= 1 key named chip_flags" (the loader returns a
typed object, not a raw dict, when `msgspec` is installed; the key/attribute is present
either way).

## Artefacts

- `$DATASTORE/chipdb/std/GW5AST-138C.msgpack.xz`, `.../std/GW5AST-138C-run2.msgpack.xz`
  (determinism check)
- `$DATASTORE/chipdb/edu/GW5AST-138C.msgpack.xz`, `.../edu/GW5AT-60B.msgpack.xz`,
  `.../edu/GW5AT-60B-run2.msgpack.xz` (determinism check)
- No artefact for std/GW5A-25A, std/GW5AT-60B, edu/GW5A-25A - builds failed, nothing to
  copy.

## Logs

`$PIPE/evidence/_runs/chipdb-{std,edu}-{GW5AST-138C,GW5A-25A,GW5AT-60B}.log`,
`chipdb-std-GW5AST-138C-run2.log`, `chipdb-V2-verbatim.log` (the literal `V2` script,
captured after clearing stale `apycula/*.msgpack.xz` so `shasum` failures are real, not
stale leftovers).

---

## P0.T15b — re-run on Standard only (2026-09-04)

Owner constraint C9 / decision D79: the Gowin Standard licence landed, the Education
1.9.11.03 install was deleted from disk, and Standard 1.9.12.03 is `GOWINHOME` for
everything from now on. **Every Education row above is `superseded, install removed
2026-09-04`** — kept as a historical record only; it can no longer be reproduced on this
box (only the `IDE/share/device` tree survives, archived at
`$DATASTORE/ide-share-device/edu-1.9.11.03`).

All three devices now build on Standard, with the parser at `apicula` `epic/gw5ast138c`
(the drpfuse/longfuse/ADC work of P0.T13b/T13c):

| install | device | outcome | sha256 | bytes | ide_version |
|---|---|---|---|---|---|
| std | GW5AST-138C | OK | `ab1339e4cfb6d58cd5f646fca35d42b9a4b53b629c0edf27dd7ae1e9702bb88d` | 811780 | 1.9.12.03 |
| std | GW5A-25A | OK | `fa431045b35965ca96ed829dfebe7931ebc1bcab8563c084675bbafcc1b5a12e` | 320296 | 1.9.12.03 |
| std | GW5AT-60B | OK | `5a921a831b923899d03a70ce1791f0d938d8fb7c7794608a55e3cec0527acf18` | 320908 | 1.9.12.03 |

**Determinism (spec.md §8.3): confirmed.** `GW5AST-138C` built twice on Standard, same
shell, same parser: both runs produced `ab1339e4cf…`, 811780 bytes — byte-identical. The
earlier non-determinism finding (recorded above under the pre-T13b runs) was fixed by
`save_chipdb` canonicalization in P0.T13b and stays fixed.

**gw_sh path proof (pre-5-series build).** `GW1N-9C` — the device class whose chipdb build
shells out to `gw_sh` — built on Standard, exit 0, 191816 B, sha256 `54cc6fa47222…`, zero
`libGWTE` loader errors. This did **not** work at first: `apycula/codegen.py` invoked
`gw_sh` through `/usr/bin/env LD_PRELOAD=…`, and `/usr/bin/env` is SIP-protected on macOS,
so dyld stripped `DYLD_LIBRARY_PATH`/`DYLD_FRAMEWORK_PATH` across the exec and `gw_sh` died
with `Library not loaded: @rpath/libGWTE.dylib` → `pnr_result=None`. Fixed on
`epic/gw5ast138c` (commit `8b3338d`): `gw_sh` is exec'd directly, `LD_PRELOAD` is set in
the child env on Linux only. Per the disk rule, the `GW1N-9C` artefact was deleted after
its sha256 was recorded.

Artefacts: `$DATASTORE/chipdb/std/{GW5AST-138C,GW5AST-138C-run2,GW5A-25A,GW5AT-60B}.msgpack.xz`.
Logs: `evidence/_runs/chipdb-std-{GW5AST-138C,GW5AST-138C-run2,GW5A-25A,GW5AT-60B,GW1N-9C}.log`.
