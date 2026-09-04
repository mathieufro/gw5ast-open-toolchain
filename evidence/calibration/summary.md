# S6 — checker calibration on the three `tangmega138k` baselines (`P0.T33`, `V5`)

Measured 2026-09-04 on GW5AST-138C (part `GW5AST-LV138PG484AC1/I0`, `device_version C`),
oracle Gowin Standard 1.9.12.03 (licensed, `edu-provisional: false`), chipdb
`$DATASTORE/chipdb/std/chipdb-GW5AST-138C.bin`.

> **`S6`** — *the equivalence checker is calibrated on a whole-design baseline. This is a
> harness calibration criterion, not an equivalence pass: GowinSynthesis and yosys do not
> emit the same LUT4/DFF decomposition for a whole design, so a whole-design `E1` is not
> achievable and is not asked for (`D32`). For each of the three existing `tangmega138k`
> examples (`big-shift`, `attosoc`, `uart-message`) the checker runs end to end on the
> open-flow and oracle bitstreams and reports a **bounded, fully enumerated diff** — every
> differing item listed by category, none unexplained — with the pip delta recorded as a
> statistic. … Measure: checker exit 0 with an enumerated diff report on three designs; no
> mask entry added beyond the documented base set.*

**Verdict: `S6` MET for all three designs, at `E0` and at `E1`.** Six runs, six
`CALIBRATION ok` lines, no `FAIL` line, `RESIDUAL_UNEXPLAINED entries=0` everywhere. The
mask is unchanged: `sha256 59147bfc633e10c5c1f4875bef6cf0cf9b76f8d58868ffc084f8c252557a1ec0`,
the same six base entries, **no entry added**.

## Per design (level `E1`; `E0` is identical except for the `E1 placement` line)

| design | `DIFF_COUNT` | `PIPS` (statistic) | `RESIDUAL_UNEXPLAINED` | `CALIBRATION` |
|---|---|---|---|---|
| `big-shift` | cells=137690 attrs=139311 conns=552818 | 2012168 | entries=0 bits=0 bytes=0 | `CALIBRATION ok: 829826 diffs enumerated, 0 unexplained` |
| `attosoc` | cells=136401 attrs=175923 conns=566961 | 1970978 | entries=0 bits=0 bytes=0 | `CALIBRATION ok: 879294 diffs enumerated, 0 unexplained` |
| `uart-message` | cells=137421 attrs=139287 conns=554129 | 2008776 | entries=0 bits=0 bytes=0 | `CALIBRATION ok: 830846 diffs enumerated, 0 unexplained` |

`DECODE_CHECK` (§5.4, `D34`): `c2=ok` on all three (0 differing bytes of 4,147,478).
`c1=mismatch` on all three — `big-shift` 123/160, `attosoc` 2265/3050, `uart-message`
110/168 placed cells recovered, 6 not fuse-backed. Whole-design `c1` completeness is a
**named gap**, not a calibration failure: `S6b` scopes the precondition to the primitive
under test, and the missing cells are the vendor-side decomposition the checker is
calibrating against.

`E1 placement level=E0 constrained=0` on all three: `export_insloc` filters to instances
the vendor keeps, and GowinSynthesis renames every instance of a whole design, so no
`INS_LOC` line survives. This is the `EC9` shape already measured in `P0.T26` (`CT1135`),
and it is why `D32` says a whole-design `E1` is not asked for.

## Residual, fully enumerated (bits, per design)

| category | big-shift | attosoc | uart-message | disposition |
|---|---|---|---|---|
| `net_route` | 3,872,278 | 3,916,990 | 3,874,200 | ACCOUNTED, mask `net_route` |
| `set_level_diff` | 1,116 | 16,721 | 420 | ACCOUNTED (visible to the `E0` sets) |
| `vendor_only_fill` | 693 | 17,834 | 990 | ACCOUNTED, mask `unused_tile_fill` |
| `io_default_unused_pins` | 631 | 641 | 643 | ACCOUNTED, mask `io_default_unused_pins` |
| `comment_header` | 634 B | 634 B | 634 B | ACCOUNTED, mask `header_words` |
| `unmodelled_config_fuse` | 20 / 4 tiles | 9,893 / 138 tiles | 793 / 19 tiles | **GAP** → Phase 1, Phase 3 |
| `bsram_mode_fuse` | — | 28 / 8 tiles | 100 / 16 tiles | **GAP** → Phase 4 |
| `extra_config_frames` | — | 202,356 B | 99,198 B | **GAP** → Phase 4 |
| `extra_command_words` | 20 B | 56 B | 48 B | **GAP** → Phase 8 |

A GAP is *enumerated with a category and a named owner*, which is what `S6` asks for; it is
never masked, and it never reaches `unexplained_bits`.

## The two open questions `P0.T33` was asked to settle

### 1. The nextpnr passthrough LUT — **not a defect, no fix, no mask entry**

`nextpnr/himbaechel/uarch/gowin/gowin.cc:1199-1252` (`GowinImpl::create_passthrough_luts`,
called from `postPlace()` at `:926`) binds a `LUT4` with `INIT=0xff00` into the LUT bel
paired with a DFF whenever that LUT, its ALU and the tile's `RAMW` are all free, and moves
the DFF's `D` net onto the LUT's `I3`.

It is architecturally **required**, not a packing bug: in the apicula chipdb the CLS `DFF`
bel has **no `D` port at all** — `db.tiles[17].bels['DFF0'].portmap` is
`{'CE': 'CE0', 'CLK': 'CLK0', 'LSR': 'LSR0', 'Q': 'Q0'}` — so the flop's data input is
hard-wired to the paired LUT's `F` output inside the slice and no pip in the device can
reach it. Removing the pass-through would make every DFF whose `D` comes from the fabric
unroutable. There is therefore nothing small and correct to fix in nextpnr, and a mask
entry would be wrong twice over: a bound `LUT4` is real configuration, and `spec-harness.md`
§5.3 forbids masking a whole-design decomposition difference into silence. It is enumerated
under `set_level_diff` — exactly the LUT4/DFF decomposition class `S6`/`D32` declares
expected.

### 2. The `unmodelled_fuse` residual — **misclassification in the checker, now fixed**

`P0.T29` left 14,935 bits / 231 tiles under `unmodelled_fuse` on the smoke pair. Sampling
the same class on `big-shift` (217 tiles, 11,527 bits) and attributing each differing bit
to the chipdb table that owns it shows:

- **11,185 of 11,527 bits are pip fuses** (`db.tiles[ttyp].pips` / `clock_pips`) in tiles
  whose cell sets match — i.e. the physical route of a net whose endpoints match. §5.1b says
  *every bit either unpacker accounted for is subtracted*, and `gowin_unpack` does recover
  pips; the classifier was only consulting `netlist.cells`, so route bits were being
  reported as unmodelled. Fixed: `equiv.fuse_groups()` now attributes every differing bit to
  its chipdb fuse group before the cell-set classifier runs, and pip/`alonenode` bits land
  in `net_route` under the existing base mask entry (§5.3 row 5, `D32`).
- **631 bits are `longval:IOBA`/`IOBB` fuses on pins neither design uses**, all
  `open=1 vendor=0`, in the left (col 0) and right (col 181) IO columns. Source:
  `apycula/gowin_pack.py:1684-1716` `get_unused_io_fuses()` writes the bank default
  `IO_TYPE` and `BANK_VCCIO` into every unused IO of a used bank; the vendor leaves them
  cleared. The GW5A `get_unused_io_attrvals()` (`gowin_pack.py:1670-1672`) returns `[]`, so
  **no `DRIVE` and no `PULLMODE` are written** — this is not the PR #423 bank/drive-strength
  hazard class, it is the `io_default_unused_pins` base mask entry (§5.3 row 6).
- **The remainder** (20 bits on `big-shift`) is in the central clock spine
  (`db.center_col` 90 ± 3, tile row 20: `shortval:CFG`, `shortval:5A_PCLK_ENABLE_*`,
  unnamed `shortval` tables) and the bottom configuration row — device configuration apicula
  models no cell for. Enumerated as the `unmodelled_config_fuse` **named gap**, owner
  W-CLOCKING (Phase 1) and W-IO (Phase 3). On `attosoc` this class is 9,893 bits/138 tiles
  and on `uart-message` 793 bits/19 tiles.
- On the two designs with memory, a further named gap: `bsram_mode_fuse`
  (`shortval:BSRAM_SP|DP|SDP|ROM` in tiles neither side recovers a cell for) and
  `extra_config_frames` (the 62-byte / 496-bit BSRAM initialisation slot lines) — the
  memory-inference decomposition, owner W-COMPUTE-MEMORY (Phase 4).

## Defects found and fixed on the way

- `apycula/bslib.py` `read_bitstream()` identified the device-ID word by `ba[0] == 0x06`
  and the frame count by `ba[0] == 0x3b` with **no length guard**. A 62-byte BSRAM
  initialisation slot line beginning with either byte was read as a command word: on
  `uart-message-tangmega138k.fs` that aborted the read with
  `ValueError: ('Unsupported device', …)`, and on the vendor bitstream it re-set the frame
  count and pulled 507 slot lines into the fuse bitmap. Fixed by requiring the measured
  widths (device id 8 bytes, frame count 4 bytes). All six baseline bitstreams now read to
  a uniform 1517 × 21872 bitmap.

## Artefacts

Open flow (`examples/gw5a/Makefile`'s own recipe, invoked never edited — see `runs.jsonl`
for the literal `yosys` / `nextpnr` / `gowin_pack` command lines and the sha256 of every
`.fs`). Vendor oracle under `$DATASTORE/calibration/<design>/run/impl/pnr/run.fs`.
Full stdout: `calibration-stdout.txt` (`E0`, the `V5` invocation) and
`calibration-stdout-E1.txt`. Batch log `../_runs/t33-calibration.log`, watchdog
`../_runs/t33-calibration.watchdog.log`.

## Deviations

- **One `.cst` per design, filtered.** `examples/gw5a/tangmega138k.cst` (F39) constrains
  `led[0..15]`, `clk`, `reset`, `uart_tx`, `uart_rx`; each design has only a subset. nextpnr
  ignores a constraint on an absent port, the vendor aborts the whole run with
  `ERROR (CT1135) : Can't find object named …`. The oracle side therefore uses a copy
  filtered to the design's own top-module ports, written into `$DATASTORE/calibration/<d>/`.
  `examples/gw5a/` is untouched (`git diff --name-only` lists 0 paths under it).
- **`-use_sspi_as_gpio 1` on the oracle.** Without it the vendor refuses to place `led[0]`,
  `led[1]`, `led[3]` and `led[8]` (`ERROR (PR2017) … dedicated pin (CPU/SSPI)`). The open
  flow passes only `gowin_pack --cpu_as_gpio`; the config-pin mode difference that follows
  is visible in the enumerated residual, not masked.
- **`equiv.py` touched beyond calibration mode.** The blueprint scoped the edit to
  calibration mode; the pip misclassification above is a §5.1b correctness defect that
  affects every primitive row, so it was fixed for all levels under the standing order.
- **`apycula/bslib.py` touched** (not in the task's file list) for the same reason: without
  it `uart-message` cannot be read at all.
