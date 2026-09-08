# `V20` storage hygiene at the Phase-3 close (`P3.T38`)

## The three `V20` assertions

```
OK-evidence-gitignore
OK-manifests
OK-no-binaries
```

`git ls-files` under `$OTC/evidence` returns no `.fs`/`.vo`/`.tr`/`.sdf`/
`.fse`/`.dat`/`.tm`; both sha256 manifests are present; the run-log drop is
git-ignored. The example bitstreams this phase adds
(`examples/gw5a/*-tangmega138k.fs`) are ignored too, so the 23 built targets
are artefacts and not commits.

## What was deleted, and why deleting it is safe

A vendor `gw_sh` project leaves far more behind than the evidence cites. The
deletion is keyed on **what an evidence row names**, not on age alone: the
1 650 artefacts any `runs.jsonl` cites by absolute path plus sha256
(`vendor_fs`, `sdf`, `tr`, `open_fs`, `oracle_log`, `open_log`) were left
untouched, and only file classes no row references were removed.

| class | what it is | files | bytes |
|---|---|---|---|
| `*.pr` | the vendor's placed-and-routed database | 273 | 21.99 GB |
| `*.binx` | the vendor's intermediate bitstream image | 272 | 1.18 GB |
| `run/impl/pnr/run.bin` | the raw bitstream image beside the `.fs` the rows cite | ~280 | 1.16 GB |
| `*.html` | the vendor's HTML reports, duplicated by `run.rpt.txt` | 2 210 | 0.07 GB |
| **total** | | **3 027** | **24.42 GB** |

The chipdb install (`$DATASTORE/chipdb/`), the device-file mirror
(`$DATASTORE/ide-share-device/`) and the toolchain mirror were excluded by
path, because `chipdb-GW5AST-138C.bin` is itself a `.bin` the open flow needs.

Datastore: **41 GB -> 18 GB**. Boot volume free: 59 GiB.

`check_evidence.py` after the deletion: `EVIDENCE ok: 348 rows, 17 pending,
0 blank, 0 missing artifacts` — no cited artefact was removed, which is the
only proof that matters here.

## What was NOT deleted, and why

Whole run trees older than 24 h were **kept**. Their `run.fs`, `run.sdf`,
`run.tr` and `gw_sh.log` are cited by sha256 from the evidence rows, and
`check_evidence.py` verifies each one exists and still hashes to the recorded
value. Deleting a cited bitstream would trade 6 GB for the ability to re-check
any row of this phase against the artefact it was derived from, which is the
thing the evidence tree exists to make possible.
