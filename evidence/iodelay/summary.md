# IODELAY shape-A sweep on GW5AST-138C

`P3.T21` (the sweep) and `P3.T22` (the decode). Shape `iodelay_a`: one
`IODELAY` on a 3.3 V bank-5 input ball (`AA9`, `IOB53A`, cell `(52,108)`),
`DO` captured in a flop, `SDTAP`/`VALUE` from pads, `DF` to a pad. 28 sweep
points: 24 `C_STATIC_DLY` values in Gray-code order, then `DYN_DLY_EN` and
`ADAPT_EN` false/true.

```
BATCH_COMPLETE p3-iodelay-a runs=28 ok=0 diff=16 aborted=12
```

## The `C_STATIC_DLY` fuse table (MEASURED, 28 vendor bitstreams)

Baseline `c-static-dly-0`, which sets **no** delay fuse at all. Every other
point adds exactly the bits of its own binary weight in tile `(52,108)`, row
21 — nothing else in the tile moves:

| `C_STATIC_DLY` bit | weight | fuse (row, col) |
|---|---|---|
| 0 | 1 | `(21, 3)` |
| 1 | 2 | `(21, 4)` |
| 2 | 4 | `(21, 5)` |
| 3 | 8 | `(21, 6)` |
| 4 | 16 | `(21, 7)` |
| 5 | 32 | `(21, 8)` |
| 6 | 64 | `(21, 9)` |
| 7 | **128** | `(21, 10)` |

All 24 points are consistent with it, including the ten that carry bit 7
(128, 129, 130, 131, 132, 134, 136, 140, 152, 192).

**This is not the pre-5A `DELAY_DEL` map.** The GW5AST-138C spends **one**
enumerated IOLOGIC attribute — number **118**, unnamed in the shipped
`attrids` table — on the whole 0-255 step, where GW1N/GW2A spend seven
one-bit attributes `DELAY_DEL0`-`DELAY_DEL6` (ids 32-38). Its value ids are
`2` for one step and `1000 + n` for every `n >= 2`; step 0 has no row. The
shortval table carries all 255 non-zero steps. So **`DELAY_DEL7` was never
the question**: bit 7 *is* fuse-backed on this die, and the refusal
`P3.T20` recorded ("needs `DELAY_DEL7`, which the IOLOGIC attribute table
does not have") is an artefact of reading the pre-5A window on a die that
does not use it. The attribute is now named `C_STATIC_DLY` in `attrids`,
and `gowin_unpack` recovers the step from any bitstream:

```
c-static-dly-1    IOLOGICA {'C_STATIC_DLY=1'}
c-static-dly-16   IOLOGICA {'C_STATIC_DLY=16'}
c-static-dly-64   IOLOGICA {'C_STATIC_DLY=64'}
c-static-dly-128  IOLOGICA {'C_STATIC_DLY=128'}
c-static-dly-152  IOLOGICA {'C_STATIC_DLY=152'}
```

## Dynamic and adaptive mode are fuse-backed too

`dyn-dly-en-true` moves **37** bits of the same tile (and clears `(0,65)`
and `(0,68)`); `adapt-en-true` moves **41**, a superset of the dynamic set
plus `(7,84)`, `(7,94)`, `(20,109)`, `(20,118)`. Both light six further
IOLOGIC attributes the shipped table does not name — ids 77, 78, 89, 106,
108 and 135, decoding as `ENABLE`/`ENABLE`/`ENABLE`/`INV`/`TRUE`. The two
`false` points are bit-identical to the baseline, so the deltas are the
modes' own. Naming those six is the next IODELAY task; the bit lists are in
`fuse-attribution.json`.

## Verdicts

| verdict | n | why |
|---|---|---|
| `diff` | 16 | 14 static points that build, plus `dyn-dly-en-false` and `adapt-en-false` |
| `aborted` | 12 | the 10 bit-7 points and the two `true` points: `gowin_pack` exits 1 on its own named refusal, which `openflow` records as a failed step rather than `verdict: refused` |

No point reaches `verdict: ok`, and the reason is **not** the delay value:
`cells` and `attrs` are 0 and `conns` is 1 on every built point. It is that
the open flow's whole IODELAY fuse set is the pre-5A one. Comparing the two
bitstreams' IO tile at four different steps gives the **same** difference
every time — the delta does not move with the sweep:

* vendor-only, constant: `(8,99) (8,100) (9,95) (9,96) (20,12) (20,20)
  (20,98) (21,80)`, plus that point's own delay bits;
* open-only, constant: `(2,38) (3,28) (3,29) (3,36) (3,107) (3,110) (8,57)
  (8,58) (9,53) (9,54) (9,106) (9,107) (9,109) (9,111) (21,49) (21,54)
  (21,66)`.

So `gowin_pack` writes **no** `C_STATIC_DLY` bit at all on this die (the
open set is identical at steps 0, 1, 16 and 64) and writes seventeen
enable-path bits the vendor does not. Closing the row at `E1` needs the
138C's IODELAY *enable* attributes attributed the same way this task
attributed the step — a packer task, and `P3.T22` may not touch
`gowin_pack.py`. **Named, measured, and open**, with the exact bit lists
above.

## Budget

49 oracle runs, against a 28-run allocation. The first 21 were spent on the
shape's original ball `N15` (`IOB146A`, ttyp 63) before the open half was
known to be impossible there: `chipdb.dat_portmap` builds a GW5A IOLOGIC
portmap only for a tile that carries an `IOBB`, so fourteen of this die's
326 IOLOGIC bels — ttyps 63, 64, 65, 86, 87, 251 — carry no ports at all,
and every open half aborted with "No wire found for port DF". Those 21 rows
are archived at `archive/runs-ttyp63-unmodelled.jsonl`; the ball moved to
`AA9` and the 28 were run again. **The phase is now 89/110 with ~32 runs of
allocation left — an overrun the owner should price.**

## Files

* `runs.jsonl` — the 28 measured rows.
* `fuse-attribution.json` — per point: every bit set in the scoped tile, the
  delta against the baseline, and the decoded IOLOGIC attributes
  (`tools/attribute_iodelay_fuses.py`).
* `archive/runs-ttyp63-unmodelled.jsonl` — the 21 rows on the unmodelled ball.
* Designs and logs: `$DATASTORE/p3t21b/`, batch log
  `evidence/_runs/p3-iodelay-a.log` (and `-ttyp63.log` for the first attempt).

| artefact | sha256 |
|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `df0ae17df04eeb3ce23a9edf56d37adcd5fc5d231ebccfc7fd1d3daf7613a958` |
| `chipdb-GW5AST-138C.bin` | `3df1431840852dbdb9f22953c584927d7f3e5bf259f902ff7cd8be5b53c82d18` |
| `nextpnr-himbaechel` | `084bbbfa61c1f2ff225640b80ce0440ba8ce45b2bb304ef295bf3729c318436e` (this task's build; the pair's `.bin` is unchanged -- no constids moved) |
