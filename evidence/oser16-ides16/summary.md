# `OSER16` / `IDES16` on the GW5AST-138C — adjudicated and implemented

`P3.T16` adjudicated the two 16-bit gearboxes against the vendor; `P3.T17`
replaced the open flow's accidental refusal with one that named the gap;
`P3.T16a` closed it. Both primitives now build end to end in the open flow and
both close at **`E1`, `ok`, `0/0/0`, with an empty `fuses_moved`** — the open
bitstream's scoped fuses are bit-identical to the vendor's.

## Verdict: the vendor accepts both, and so does the open flow now

| run | primitive | shape | vendor | open | level | verdict |
|---|---|---|---|---|---|---|
| `p3-oser16-io_ser16-0000` | `OSER16` | `io_ser16` | accepted, `IOLOGIC 2/285` | **ok** | `E1` | **ok** 0/0/0 |
| `p3t16a-ides16b-io_des16_balls-0000` | `IDES16` | `io_des16_balls` | accepted, `IOLOGIC 1/285` | **ok** | `E1` | **ok** 0/0/0 |
| `p3-ides16-io_des16-0000` | `IDES16` | `io_des16` | accepted | ok | `E0` | `diff` — the shape's own XOR fold |

The third row is kept, not replaced: it is `P3.T16`'s adjudication vehicle, and
its three remaining `c1` misses are the three freely placed `MUX2_LUT*` cells
of the `Q10`-`Q15` XOR fold that shape documents (`D105`). `io_des16_balls`
drops the fold — `Q10`-`Q15` are simply left unconnected — so no fabric cell
remains and the row closes.

**Vendor runs spent by `P3.T16a`: one.** `OSER16`'s row was re-derived from the
bitstream `P3.T16` already bought (`tools/redo_open_half.py`), which spends no
oracle run; only the clean `IDES16` shape needed the vendor.

## The geometry, MEASURED — and it is not the GW1N one

The two vendor bitstreams decode as follows at the pad pair under test
(`AA9` = `IOB53A`, cell (108, 52)):

| | tile / table | attributes |
|---|---|---|
| `OSER16` main | (108, 52) `IOLOGICA` | `OUTMODE=ODDRX8`, `HWL=TRUE`, `CLKOMUX=ENABLE`, `WRFCLKSEL=UNK102`, `FCLKSEL1=HCLK2`, `FCLKSEL2=HCLK2_` |
| `OSER16` aux | (108, 53) `IOLOGICB` | `OUTMODE=LVDSOUT` (the die's alias for `DDRENABLE`), `ISI=ENABLE`, `OCLKCE=CE`, same clock selection |
| `IDES16` | (108, 52) `IOLOGICA` | `INMODE=105`, `CLKIMUX=ENABLE` — and **nothing at all** in the `B` half |

So on the Arora V families a 16-bit gearbox occupies **one pad pair**, not two
consecutive cells: `OSER16` takes the pair's `A` and `B` halves and `IDES16`
takes `A` alone. That is exactly the asymmetry the vendor's own resource report
showed (`IOLOGIC 2/285` against `IOLOGIC 1/285`) and it is *why* it showed it.
`get_tile_io16_offs` therefore stays `(0, 0)` on this family and means it; the
`io16` extra_func records `pair: (0, 0)` with `aux: 'IOLOGICB'` so a packer can
tell the two geometries apart without inferring anything from a zero.

Three consequences fell out of that single fact:

* **the `B` half's IOLOGIC fuses live in the aux cell**, next to its pad's:
  (108, 52)'s own `IOLOGICB` table stays clear and (108, 53)'s carries the aux
  configuration. `chipdb` now gives `IOLOGICB` the `fuse_cell_offset` its
  `IOBB` already had, and `gowin_pack`/`gowin_unpack` follow it. Before this,
  the die's whole `B` column of IOLOGIC was unusable and nothing said so;
* **`INMODE` value id 105** is this die's 16:1 input mode. It is not the pre-5A
  `IDDRX8` (67) — `OSER16` reuses that id in the *output* direction — and no
  shipped table names it, so it enters `attrids` as `UNK105` beside `UNK76`
  (which is `IDES8` here) and `UNK102`;
* **`OCLKCE=CE`** is the one attribute of the aux half the generic `DDRENABLE16`
  handler misses.

## Extent: structural, and stated as such

`chipdb` creates the two bels on every cell that has both `IOLOGIC` halves and
the pad pair to go with them — 156 cells on this die. That extent is derived
from the device's own tables rather than fuzzed cell by cell the way the
GW1N-9/GW1NS-4 ranges were, and one cell of it (108, 52) is measured. A ball
whose pair the vendor refuses would therefore be accepted here and refused by
`gw_sh`; no such ball is known, and finding one is a sweep, not a fix.

## Decode

A decoded 16-bit gearbox is reported under **both** the gearbox bel and the
`IOLOGIC` half whose fuse table carries it. Both are true of the same bits and
a placement may name either, so reporting one and dropping the other made the
other unrecoverable — which is what the first `c1` mismatch of this task was.
