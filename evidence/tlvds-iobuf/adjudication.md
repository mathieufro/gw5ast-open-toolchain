# `TLVDS_IOBUF` on GW5AST-138C — the adjudication

VERDICT: restored

## The question

`chipdb.fse_create_diff_types` removed `TLVDS_IOBUF` for every device outside
`{GW5A-25A, GW2A-18, GW2A-18C, GW1N-4}` (`chipdb.py`, the `elif device not
in {...}` branch) with no recorded rationale anywhere in the tree or its
history. Either the type is genuinely absent on the other dies, or the set is
an artefact of which devices happened to be fuzzed.

## What was measured

One design, one `gw_sh` run (`p3-tlvds-iobuf`, 1 oracle run, ledger cumulative
93/140): a single `TLVDS_IOBUF` on the die's only `TRUELVDS` pair
(`J14`/`H14` = `IOR103A`/`B`, tile `(181,102)`, bank 3 at 3.3 V), its `I`,
`OEN` and `O` on package balls.

**The vendor accepts it.** `gw_sh` ran the design end to end —

    Placement and routing completed
    Bitstream generation completed

— with no warning naming the primitive, and produced `run.fs`, `run.tr`,
`run.vo` and `run.sdf` like any other point. The removal is therefore wrong
for this device, not conservative.

The open flow, on the same inputs and before the fix, refused it by name:

    ERROR: TLVDS_IOBUF is not supported

from `pack_io.cc`'s `pack_diff_iobs`, which asks `gwu.is_diff_io_supported`
and so is reading the chipdb's `diff_io_types` — the removed entry, reaching
the user as a refusal of a type their silicon has.

## What changed

`'GW5AST-138C'` joins the set in `fse_create_diff_types`, with the measurement
cited beside it. Nothing else: the `GW1NZ-1` and `GW1N-1` branches are
untouched, `TLVDS_IBUF_ADC` stays 25A-only, and `GW5A-25A`'s own
`diff_io_types` is unchanged (guarded by a test). **No C++ change was needed**
— `pack_io.cc` already carries the `ID_TLVDS_IOBUF` cases in `get_pn_cells`
and `switch_diff_ports`; the only thing missing was the chipdb entry, which
is why the refusal was a data question all along.

## The row after the fix

`E1`, `verdict: ok`, `cells` 0 / `attrs` 0 / `conns` 0 in tile `(181,102)`,
decode `c1` ok / `c2` ok, no unexplained bit — rebuilt from the stored vendor
bitstream at **no further oracle run** (`tools/redo_open_half.py`).

## Scope of the claim

This adjudicates **GW5AST-138C** and nothing else. The other devices still
outside the set (`GW5AT-60B`, the GW1N/GW2A parts not listed) were not built
and are not claimed either way; each needs its own oracle run before its entry
moves.
