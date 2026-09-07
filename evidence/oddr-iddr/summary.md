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

## ATTRIBUTE-AUDIT (`P3.T11`)

**2 oracle runs**, the task's whole cap, covering **four** primitives: one
vendor design carries `ODDR` **and** `ODDRC`, the other `IDDR` **and**
`IDDRC`. The two `C` variants add a `CLEAR` port and no parameter
(`$GOWINHOME/IDE/simlib/gw5a/prim_sim.v:7793` `IDDR`, `:7854` `IDDRC`,
`:7988` `ODDR`, `:8070` `ODDRC` — `TXCLK_POL`+`INIT` on the output pair,
`Q0_INIT`+`Q1_INIT` on the input pair), so one design per direction measures
both. Driver: `evidence/oddr-iddr/audit_oddr_iddr_attrs.py`; log
`evidence/_runs/p3-oddr-iddr-audit.log`; per-run record `audit-runs.json`.

**The HCLK-clocked variant is not run, by measurement rather than omission.**
`P3.T08` established `G-FCLK-138C`: this die has no HCLK→FCLK edge
(`dev.io2hclk == {}`) and none of `P3.T07`'s twelve vendor bitstreams
configures a single `FCLK*` pip. The vendor clocks IOLOGIC on the 138C over
`BUFG`/global, which is what both audit designs do.

### Instrument

`gowin_unpack` surfaces only `MODE=` and `CLKODDRMUX_ECLK=` as IOLOGIC flags.
The audit calls `parse_attrvals` again on the same tile with the same tables
and keeps the **whole** decoded `{attr: val}` dict, then computes, through
`gowin_pack`'s own path (`add_attr_val` → `get_shortval_fuses`), the fuse set
each side writes. The verdict term is the fuse set, not the attribute list:
an attribute at its zero code moves no bit and is not a gap.

**Instances are matched to decoded tiles by package ball**
(`P3.T06`'s `evidence/iologic/pin-hclk-138c.json`), never by the decoded
`MODE=` flag. `gowin_unpack.py:806-830` tells `ODDR` from `ODDRC` by the mere
*presence* of `LSROMUX_0`, and this die sets `LSROMUX_0=0` on the plain
variant too — so the flag calls a plain `ODDR` an `ODDRC`. That mislabelling
is itself a finding and is recorded here rather than worked around silently.

### Measured, per primitive, at `IOLOGICA` of tile type 247

| primitive | ball | tile | vendor attributes | vendor fuses |
|---|---|---|---|---|
| `ODDR` | `AB16` (`IOB80A`) | `(79,108)A` | `OUTMODE=MODDRX1`, `CLKOMUX=ENABLE`, `LSROMUX_0=0`, `LSRIMUX_0=0` | `(20,59) (21,54) (21,112) (21,113)` |
| `ODDRC` | `AB17` (`IOB80B`) | `(79,108)B` | **none decoded** — see the B-half gap below | none |
| `IDDR` | `AA15` (`IOB83A`) | `(82,108)A` | `INMODE=IDDRX1`, `CLKIMUX=ENABLE`, `LSRIMUX_0=0`, `LSROMUX_0=0` | `(21,15) (21,104)` |
| `IDDRC` | `W15` (`IOB72A`) | `(71,108)A` | `INMODE=IDDRX1`, `CLKIMUX=ENABLE`, `LSRMUX_LSR=INV`, `LSROMUX_0=0` | `(21,15) (21,49) (21,56) (21,104)` |

`attr-gap.tsv` carries one row per attribute either side sets, with the fuse
count that attribute's value is worth and a disposition; `fuse-delta.json`
carries the two fuse sets and their difference per primitive, as they stood
**before** the handler change `P3.T12` makes.

### The 138C-specific differences, named

1. **`GSR` — `attrid 5`, one fuse `(21,119)`, every primitive.** The generic
   `Device.common_iologic_handler` (`gowin_pack.py:2138`) emits `GSR`
   unconditionally and `DISGSR` when the cell has no `GSREN`. On this die
   `DISGSR` is **not** the zero code: it sets `(21,119)`, and the vendor
   leaves that fuse clear on all three primitives measured. It is the single
   over-emitted bit in each. Disposition: **handler** — the 138C override
   emits `GSR` only for the explicit `GSREN=TRUE` opt-in.
2. **`LSRMUX_LSR` on `IDDRC` — `attrid 19`, two fuses.** The generic
   `get_in_iologic_attrs` (`:2210-2219`) selects `SIG` for a cell with an
   asynchronous clear and leaves `LSRIMUX_0` at the placeholder `UNKNOWN`.
   The vendor selects **`INV`** and sets no `LSRIMUX_0` at all: `SIG` writes
   `(21,49)` where the vendor writes `(21,56)`. Disposition: **handler**.
3. **`OUTMODE`: vendor `MODDRX1`, `gowin_pack` `ODDRX1` — attrid 1, no fuse
   difference.** Both spellings reach the same three fuses at this tile type,
   so this is a naming difference and not a configuration one. Disposition:
   **unexplained-justified**, no change.
4. **`TSHX=SIG`, `LSRIMUX_0=0`, `LSROMUX_0=0`, `CLKODDRMUX_ECLK=UNKNOWN`
   are all worth zero fuses here.** They are the zero code of their
   attribute, so `gowin_pack` emitting them where the vendor's decode does
   not report them is an encoding artefact, not an over-emission. Disposition:
   **unexplained-justified**, no change — in particular the
   `CLKODDRMUX_ECLK=UNKNOWN` that `G-FCLK-138C` makes unavoidable on this die
   costs nothing.

### Named gap: the B half of an IO tile has no IOLOGIC fuse table

The `ODDRC` placed on `IOB80[B]` (the vendor's own timing report puts it
there) configures **nothing** decodable: `db.shortval[247]['IOLOGICB']` holds
**3** fuse coordinates against `IOLOGICA`'s **100**, and no bit inside it is
set. The nine further bits the `ODDR` design moves in that tile are all
`pip` bits (routing), not IOLOGIC configuration.

This is the same shape the GW5A-25A shows — every IO tile type there has one
populated IOLOGIC table (676 keys / 90 coordinates) and one stub (2 keys / 2
coordinates), on the A half or the B half depending on the tile type — so it
is a property of the database, not of this die alone. What it means here is
concrete and bounded: **on tile type 247 an IOLOGIC may be configured on the
A half only.** Every point of `P3.T12`'s sweep lands on an A-half ball
(`AB16` = `IOB80A`, `AA15` = `IOB83A`), so the row closes on A-half evidence
and the B half is a stated limit of it, carried to the serialiser and
deserialiser rows (`P3.T13`, `P3.T14`) as an inherited input.

## SWEEP (`P3.T12`)

**6 oracle runs**, the task's cap, one per point of `shapes/io_basic.py`'s
`POINTS` (`oddr-default`, `oddr-txclk-pol`, `oddr-init`, `iddr-default`,
`iddr-q0-init`, `iddr-q1-init`). Batch log `evidence/_runs/p3-oddr-iddr.log`
(`BATCH_COMPLETE p3-oddr-iddr runs=6 ok=0 diff=6 aborted=0`); designs under
`$DATASTORE/p3t12`; rows `evidence/oddr-iddr/runs.jsonl`.

The rows published here are **re-derived** from those six vendor bitstreams
and the open flow's, by `recompare_rows.py`, after the packer and decode
corrections below landed — the comparison is a pure function of the two
bitstreams, so no further oracle run was spent
(`evidence/_runs/p3-oddr-iddr-recompare.log`), the same separation `P3.T08`
used over `P3.T07`'s designs.

### The packer now writes exactly the vendor's IOLOGIC fuses

`GW5AST_138C.common_iologic_handler` and `GW5AST_138C.get_in_iologic_attrs`
apply the two `P3.T11` findings (`GSR` only on the explicit opt-in;
`LSRMUX_LSR=INV` for a cell with an asynchronous clear, with no `LSRIMUX_0`
beside it). Measured at `IOLOGICA` of tile type 247, per primitive:

| primitive | vendor fuses | `gowin_pack` before | after |
|---|---|---|---|
| `ODDR` | `(20,59) (21,54) (21,112) (21,113)` | +`(21,119)` | **identical** |
| `IDDR` | `(21,15) (21,104)` | +`(21,119)` | **identical** |
| `IDDRC` | `(21,15) (21,49) (21,56) (21,104)` | +`(21,119)`, −`(21,56)` | **identical** |

and on the real pair, at `(79,108)A`, the open bitstream and the vendor's set
the same four bits.

### Three defects the row uncovered, all fixed here

1. **`equiv.split_bel_name('IOLOGICAO')` answered `('IOLOGICA', 14)`.** The
   generic rule reads a trailing capital as the `A`/`B` side letter, and an
   IOLOGIC bel name ends in its *direction*. Nothing matched the decoded
   `('IOLOGIC', 0)`, so `decode_check` `c1` reported the placed ODDR missing
   from a bitstream that in fact carried it. Phase 3 is the first phase to
   place an IOLOGIC, which is why no earlier row could hit it.
2. **`E1` had no path for an IOLOGIC.** Its site is a bitstream address, not a
   `CLS` coordinate, so `INS_LOC` cannot constrain it and the `.tr` half of
   `E1` has nothing to compare — exactly the property `level_e1_bitstream`
   exists for. `IOLOGIC` joins `CLKDIV2`/`CLKDIV`/`PLL` in
   `BITSTREAM_ADDRESSED_CELL_TYPES`, and every row now closes `E1` on
   `X79Y108/IOLOGICAO` (or `X82Y108` for the input points) matching the
   vendor's own decoded placement.
3. **`io_basic` named no comparison scope.** `equiv.in_scope` reads an empty
   tile list as the empty set, so the `E0` comparison compared nothing and its
   zeroes were vacuous. The whole-die alternative is not available: the vendor
   bitstream decodes to 138 576 cells against the open flow's 384 (MEASURED
   here) because the vendor configures every unused DFF. The scope is now the
   two data balls' own cells, `(79,108)` and `(82,108)`, which is where an
   IOLOGIC can be at all — its pad's cell. The `P3.T07` HCLK probe keeps the
   empty scope it was measured under.

### Verdict, and the one term that is not closed

All six rows: `level = E1`, `decode_check.c1 = ok`, `decode_check.c2 = ok`,
`diff_count.cells = 0`, `diff_count.attrs = 0`, `unexplained_bits = []`, no
over-emitted fuse. `check_evidence.py --slug oddr-iddr` prints `EVIDENCE ok`.

Every row is nevertheless `verdict: diff`, on **six `conns` entries and
nothing else**. They are the same six `(cell, port)` keys on both sides, with
an identical net *partition* — `IOB(79,108,0).I`, `IOLOGIC.D0`, `.DI` and `.Q`
share one net on each side, `IOLOGIC.D1` has its own, `IOB(82,108,0).O` has
its own — and different net *identities*. `equiv.net_id` digests a net's
sorted endpoint set as `(x, y, z, type, port)`, so a net keeps its identity
only if every endpoint sits at the same site on both sides; these nets run out
to the shape's context flops, and the two flows place those independently.

They are placed independently because the `INS_LOC` export cannot name them:
GowinSynthesis renames the instance (`din_r` becomes `din_r_s0` in the
vendor's own timing report), and `equiv.insloc_lines` deliberately refuses to
constrain a name the vendor's netlist does not carry, since `gw_sh` aborts the
whole run on `ERROR (CT1135)`. So this is free placement of out-of-scope
cells, which `dontcare.mask`'s `free_placement` entry admits at `E0` and
explicitly not at `E1`.

**The fix is a shape change, and it needs runs this task does not have.**
Drive `D0` and `D1` from two package balls instead of from a fabric flop and
its inverse: the design then contains no fabric cell at all, every net of the
scoped tiles has both endpoints inside them, and the `conns` term closes with
the rest. That is six new oracle runs against a `P3.T12` cap of six already
spent — a budget deviation, which the blueprint requires be priced before it
is spent, not absorbed. Recorded here for that decision; the packer, the
decode and the `E1` evidence above stand either way.
