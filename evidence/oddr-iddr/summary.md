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

## NEXTPNR-CHIPDB (`P3.T05`)

Rebuilt from the apicula chipdb above, on `nextpnr` `gowin/io-iologic-138c`
(no nextpnr source change: this task only runs the generator).

```sh
python himbaechel/uarch/gowin/gowin_arch_gen.py -d GW5AST-138C -o $DATASTORE/p3/chipdb-GW5AST-138C.bba
bbasm --le $DATASTORE/p3/chipdb-GW5AST-138C.bba $DATASTORE/p3/chipdb-GW5AST-138C.bin
```

The blueprint's literal `bbasm --e` is wrong twice over: `--e` selects the
`#embed` C output, and `bbasm` exits with `Endian parameter is mandatory`
without `--le`/`--be`. `--le` is what `cmake/BBAsm.cmake` passes on this host
and what `P0.T16b` recorded.

| artefact | sha256 | bytes |
|---|---|---|
| `$DATASTORE/p3/chipdb-GW5AST-138C.bba` | `a494b58e572229044d31d1474ca34be0f569510374c8f7a61273106c9a9a9fd8` | 91,674,955 |
| `$DATASTORE/p3/chipdb-GW5AST-138C.bin` | `9cce739de58353640475b07c838b37dceb68ea63c3fc22f0d42e093116c7f33a` | 33,569,367 |
| `nextpnr-himbaechel` (unchanged) | `d400514b6f35fd9d5449ac7c8e957171b3a94fcf1fa8410f18b9ebf6ec60f1e8` | - |

chipdb_sha256: 6a776c745d63fa8cf279a986d531435cea7a07b07033e591aafd36b61b401e1d

That is the sha256 of the canonical `apicula/apycula/GW5AST-138C.msgpack.xz`
the `.bba` was generated from, and it supersedes the `P3.T03` line above.

**Pair installed**, all three copies one database: `.bin` into
`$DATASTORE/toolchains/nextpnr/share/himbaechel/gowin/` and
`$DATASTORE/chipdb/std/`, msgpack into `$DATASTORE/chipdb/std/`. `constids.inc`
is untouched, so the Phase-2 binary `d400514b` stays the valid partner (`D101`).

### The bel surface nextpnr sees

Probe design `examples/gw5a/iddr-boardclk.v` -- a **placeholder** created here
because `P3.T09` has not landed; `P3.T09` overwrites it. One `IDDR` on the
`uart_rx` pin (V14) clocked from the board oscillator on **V22**, `Q0`/`Q1` on
`led[0]`/`led[1]`, all four pins already in `tangmega138k.cst`.

```
nextpnr-himbaechel --device GW5AST-LV138PG484AC1/I0 \
  --chipdb $DATASTORE/p3/chipdb-GW5AST-138C.bin \
  --json $DATASTORE/p3/oddr-probe-synth.json --write $DATASTORE/p3/oddr-probe.json \
  --vopt cst=tangmega138k.cst --verbose
```

exit 0, **0 lines matching `^ERROR`**, `Program finished normally.`

| bel type | used | available |
|---|---|---|
| `IOLOGICI` | **1** | **326** |
| `IOLOGICO` | 0 | **326** |
| `IOB` | 4 | 324 |

326 is exactly apicula's post-gate surface (164 `IOLOGICA` + 162 `IOLOGICB`):
the generator emits one `IOLOGICI` and one `IOLOGICO` bel per apicula IOLOGIC
bel, so nothing was lost or invented at the boundary. The `.bba` carries the
bel-name strings `IOLOGICAO`/`IOLOGICAI`/`IOLOGICBO`/`IOLOGICBI`; the blueprint's
`grep -c 'IOLOGICA'` finds them, but note that bel **types** are constid indices
in the `.bba`, not strings, which is why the second half of the check reads
nextpnr's own utilisation dump instead.

`CHIP_HAS_5A_HCLK`: the chip-level flags word is the first `u32` after
`label extra_data` (`ChipExtraData.serialise`) and reads **87937 = 0x15781**;
`0x15781 & 0x10000 == 0x10000`, so the flag crossed into the `.bin`.

### `S3` no-family-regression guard

```
60f1ba427f964feab3048f5dca82dc075acf9374a456476919202626d1335564  25a.msgpack.xz
615d4d0349ba238c1760d9685c4893fb132e39ea253aed0af6021e5da20082d8  60b.msgpack.xz
```

**Byte-identical** to the values of record. The ttyp gate is device-guarded, and
that is now measured rather than argued.
