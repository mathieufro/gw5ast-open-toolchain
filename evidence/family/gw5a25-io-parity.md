# GW5A-25 parity gate for IO and IOLOGIC (`C11`, `P3.T40`)

The question `C11` asks of a primitive phase is narrow and answerable: for
every IO/IOLOGIC primitive the GW5A-25 example set exercises, does the
GW5AST-138C carry a row at **at least** the level the 25A claims? This file
answers it primitive by primitive and names every miss.

## What the 25A claims, and how much that is

The 25A's claim is the `primer25k:` target list of `examples/gw5a/Makefile`
plus the upstream 25A fuzzing campaign behind it. Its IO/IOLOGIC members are
the ten serdes targets (`oddr-tlvds`, `oser4`, `oser8`, `oser10`, `ovideo`,
`iddr`, `iddrc`, `ides4`, `ides8`, `ides10`, `ivideo`,
`oser10-clkdiv-tlvds`), the three ADC targets and `blinky-osc`.

That claim is **weaker than it looks, and measurably so**: `P1.T44` found that
no `primer25k` target can be built today, on this fork or on upstream, because
the device string the Makefile pins (`GW5A-LV25MG121NES`) resolves to a speed
grade apicula builds no timing model for. So the 25A level for every row below
is "the primitive is modelled and the chipdb builds", not "a bitstream was
produced and compared" — the 138C rows are the stronger evidence in every case
where both exist.

## Parity table

`138C level` uses the phase's own vocabulary (`E1` = fuses + placement match
against the vendor; `E0` = fuses only; `refused:<reason>` = terminal, with the
tool's own error text).

| 25A example | primitive | 25A level | 138C level | parity |
|---|---|---|---|---|
| `iddr`, `iddrc` | `IDDR`, `IDDRC` | modelled | `E1` | **met** |
| `oddr-tlvds` | `ODDR` | modelled | `E1` | **met** |
| `oser4` | `OSER4` | modelled | `E1` | **met** |
| `oser8` | `OSER8` | modelled | `E1` | **met** |
| `oser10` | `OSER10` | modelled | `E1` | **met** |
| `ovideo` | `OVIDEO` | modelled | `E1` | **met** |
| `ides4` | `IDES4` | modelled | `E1` | **met** |
| `ides8` | `IDES8` | modelled | `E1` | **met** |
| `ides10` | `IDES10` | modelled | `E1` | **met** |
| `ivideo` | `IVIDEO` | modelled | **none** | **MISS** |
| `oddr-tlvds`, `oser10-clkdiv-tlvds` | `TLVDS_IBUF/OBUF/TBUF` | modelled | `E1` | **met** |
| — (not in the 25A example set) | `TLVDS_IOBUF` | modelled | `E1` | met, 138C ahead |
| — (not in the 25A example set) | `OSER16`, `IDES16` | not modelled on 25A | `E1` | 138C ahead |
| — (not in the 25A example set) | `IODELAY` | GW1N/GW2A only | `E0` | 138C ahead |
| `adc-temp`, `adc-loc-left`, `adc-glo-right` | `ADC` | modelled (`Adc25kIns`/`Outs`) | see the ADC row of `spec-primitives.md` §1 | see below |
| `blinky-osc` | `OSCA` | modelled | `refused:no OSCA resource in current device` | **scoped out** |

## The misses, named

1. **`IVIDEO` has no 138C row at all.** The `io_des` shape sweeps `IDES4`,
   `IDES8` and `IDES10` and stops there; `evidence/ides/summary.md` records
   that `IVIDEO` keeps the pre-5A output window rather than a measured one,
   which is the honest state but is not a row. Closing it is one vendor run on
   an `io_des` point that instantiates `IVIDEO`, diffed exactly as the three
   widths were. This is the phase's one measured IO/IOLOGIC parity miss.

2. **`OSCA` is not a miss, it is an absence.** Three vendor runs refused both
   oscillator primitives by name on this die (`ERROR (RP0008) : There is no
   OSCA resource in current device`), so the 25A's `blinky-osc` has no
   counterpart to be behind. `fse_create_osc`'s early return for this device
   is the measured truth, and the near-miss is recorded: the `.fse` does carry
   an oscillator shortval table for one cell, which a literal reading would
   have turned into a bel for a resource the vendor refuses to place.

3. **`ELVDS` is neither.** It is not in the 25A example set, and on this board
   it is refused at every VCCIO level reachable outside banks 6/7. The matrix
   is recorded rather than asserted (`evidence/elvds/vccio-matrix.tsv`).

## The direction of the gate

Of the seventeen rows above, the 138C is at or ahead of the 25A on sixteen.
The one direction the 25A is ahead is `IVIDEO`, and that is a shape that was
never written rather than a primitive that resisted measurement.

The reverse obligation `C11` also implies — that nothing measured here quietly
changes the 25A — is `S3`, and it is asserted separately and mechanically:
`GW5A-25A` and `GW5AT-60B` rebuild byte-identical to the values the previous
phase closed on (`tests/test_family_regression_gw5a.py`). Two claims this
phase discovered on the 138C were deliberately **not** generalised to the
family for exactly that reason — the 16-bit gearbox extent and the `B`-half
IOLOGIC fuse displacement — and each carries the one run per die that would
settle it.
