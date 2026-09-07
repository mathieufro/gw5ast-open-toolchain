# ODDR / IDDR on GW5AST-138C

## GUARD-STATE

`D39` **state 2** landed (`P3.T03`): the corrected `if device in {'GW5AST-138C'}:
return bels` early exit is deleted from `apycula.chipdb.fse_iologic`, so
`IOLOGICA`/`IOLOGICB` are created from `fse[ttyp]['shortval']` keys 21/22 as on
every other device. The adjacent `GW5A-25A` ttyp gate `{48, 51, 263, 392, 399}`
is untouched.

Measured on the chipdb rebuilt from that source
(`apicula` `prim/io-iologic-138c`, oracle Gowin Standard 1.9.12.03,
`GW5AST-LV138PG484AC1/I0`):

| quantity | value |
|---|---|
| `IOLOGICA` bels over the grid | 534 |
| `IOLOGICB` bels over the grid | 532 |
| total IOLOGIC bels | 1066 |
| distinct ttyps carrying IOLOGIC | 47 |
| `HAS_5A_HCLK` in `chip_flags` | present |

Non-zero **and** clocked: the flag Phase 1 set is still in the same database, so
these bels have an FCLK source behind them, which is the whole point of the
ordering `D39` imposes.

`chipdb_sha256: 1c508c92f58f0f4cb1011b543061922f9ff336bf27861830d3757798cda292a6`
(before `P3.T04`'s ttyp gate; superseded below).

## TTYP-ADJUDICATION (`P3.T04`)

`ttyp-adjudication.tsv` carries one row per candidate tile type; the derivation
is `tools/derive_iologic_ttyps_138c.py`, and the run log with the budget
deviation is `evidence/_runs/p3-iologic-ttyp.log`.

**47 candidates, 14 accept, 33 reject, 0 disagreements.** The exclusion set now
in `fse_iologic` is

```
{60, 178, 179, 182, 183, 184, 185, 220, 239, 240, 242, 244, 246, 248, 250,
 252, 253, 254, 255, 274, 278, 279, 280, 281, 282, 283, 284, 285, 374, 378,
 379, 380, 381}
```

Derived, not probed. Two independent criteria agree on every row: a rejected
tile type carries **no `IOB` bel** once `fill_GW5A_io_bels` has consolidated the
differential pairs, **and** hosts **no bonded pin** in any of this die's three
packages (`PBGA484A`, `PBGA676A`, `FCPBGA676A`). The vendor probe the blueprint
plans is not writable for those 33: with no pin there is no `IO_LOC`, hence no
design. The 484-pin package this project targets has **no top-side IO pins at
all**, which is why the 155-cell top edge (ttyp 242) alone accounted for 310 of
the 740 orphan IOLOGIC bels.

The accept side is confirmed by real placement in `P3.T05` and measured by the
12 ODDR/IDDR vendor runs `P3.T07` owns.

| quantity | before the gate | after the gate |
|---|---|---|
| `IOLOGICA` | 534 | **164** |
| `IOLOGICB` | 532 | **162** |
| total | 1066 | **326** |
| distinct ttyps | 47 | **14** |

164 `IOLOGICA` is exactly the pinned surface: 168 cells carry an `IOB` bel, four
of which are the corner types `{48, 49, 50, 51}` the generic gate already drops.
