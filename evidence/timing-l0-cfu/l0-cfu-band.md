# L0 CFU band — first real vendor-SDF measurement (`P0.T37`, `V12a --classes cfu`, `D60`)

`P0.T32` could only run the tool's **inventory** half: no vendor `.sdf` existed on this
box (`l0-cfu-inventory.md`). This task produced one and ran the **band** half. It is
therefore the first measurement of the open flow's CFU arc model against Gowin STA, and
the first check of `P0.T35`'s **derived** C1/I0 table against silicon-vendor numbers.

## What was run

- design: **attosoc-tangmega138k** (`P0.T33`'s richest CFU corpus — picorv32 + BSRAM ROM),
  re-run because `P0.T19`'s collector had pruned the `.sdf` from the kept run tree.
- oracle: `gw_sh` `run.tcl` **unchanged from `P0.T33`** (sha256
  `95eb4b32817dc992918de7d1016decc0f52e73f1ac785b1973bac0965ea0b8d6`), Standard
  **1.9.12.03**, `GOWINHOME=/Applications/GowinIDE.app/...`, `-gen_sdf 1` already on.
  Wall clock 30 s, exit 0, zero `unknown option:` lines.
- SDF path taken from the collector glob, **not** an assumed basename (`F12`): the vendor
  names the file after the *project* (`create_project -name run`), so it is
  `run/impl/pnr/**run.sdf**`, not `attosoc.sdf`. 1,594,366 B — over the 1 MB copy
  threshold, so only its sha256 is recorded here.
- tool: `$OTC/tools/check_timing_l0.py` (`--classes cfu`), chipdb
  `apicula/apycula/GW5AST-138C.msgpack.xz` sha256
  `fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb` — the **post-`P0.T40`**
  de-aliased rebuild (`F2`), apicula `143d156` on `epic/gw5ast138c`; arc source of truth
  `nextpnr/himbaechel/uarch/gowin/gowin_arch_gen.py:create_timing_info` (`e8440c71`).

## Corner (`D49f`)

The part number fixes the grade — `GW5AST-LV138PG484AC1/I0` is **C1/I0** — and there is
**no `gw_sh` option to pick a timing corner**: `set_option -h` offers `-gen_sdf <0|1>` and
nothing else in the corner/grade/voltage/temperature namespace. The vendor STA states the
corner it used in `run.tr`:

```
<Setup Delay Model>:Slow 0.873V 0C C1/I0
<Hold Delay Model>:Fast 0.927V 85C C1/I0
```

The SDF header carries the triple as three separate lines, all three echoed as the one
`V12a` condition line:

```
(VOLTAGE 0.93:0.90:0.87) (PROCESS "best=0.65: nom=1.0: worst=1.8") (TEMPERATURE 85:25:0)
```

So the `.sdf` **does** carry `min:typ:max` triples = `best:nom:worst`, and `D49f`'s
`max`-field convention selects the **slow / 0.873 V / 0 C / C1/I0** corner — exactly the
grade whose chipdb table `P0.T35` derives rather than reads. `TIMESCALE 1 ns`.

## Verdict

```
L0 ok: 1175/7136 arcs within ±10%, 5961 exceptions listed
```

(full stdout, with all 5,961 exceptions enumerated, in `summary.md`; tool exit 1.)

`L0` **fails** on the CFU class at `-138C`. This is a finding for `W-TIMING`/Phase 6, not a
reason to widen the band. `S17a`'s Phase-0 done criterion is now *executable and executed*
(`D66`) and its answer is negative.

Cells reached: LUT4 3,896 arcs, ALU 2,560, DFFRE 532, MUX2_LUT5 72, SDPB (BSRAM) 64,
DFFSE 12. **825 SDF arcs are unmapped** — LUT3 (579), LUT2 (234), LUT1 (2), OBUF (8),
IBUF (1), INV (1): nextpnr's Gowin arch installs a timing model for `LUT4` and the
`MUX2_LUT*` chain only, so a vendor-packed LUT1/2/3 has no counterpart arc, and IO buffers
are the Phase-3 `io` class, out of `D60`'s Phase-0 scope. No mapping was invented for them.

## Ratio distribution — is `P0.T35`'s 1.25x derivation right?

`ratio = vendor SDF max field / nextpnr's installed arc`, same arc, same normalised pins.
`> 1` means the open model is optimistic, `< 1` means pessimistic.

| cell | n | vs chipdb **C2/I1** (measured, `.tm` chunk 0) | vs **derived C1/I0** (1.25 x chunk 0) |
|---|---|---|---|
| ALL | 7136 | min 0.457 / **median 0.984** / max 2.240 | min 0.365 / **median 0.787** / max 1.779 |
| LUT4 | 3896 | 0.457 / 0.916 / 1.408 | 0.365 / 0.732 / 1.125 |
| ALU | 2560 | 0.467 / 1.236 / 1.905 | 0.373 / 0.987 / 1.523 |
| DFFRE | 532 | 1.489 / 1.489 / 1.489 | 1.190 / 1.190 / 1.190 |
| DFFSE | 12 | 1.489 / 1.489 / 1.489 | 1.190 / 1.190 / 1.190 |
| MUX2_LUT5 | 72 | 0.728 / 0.728 / 2.240 | 0.580 / 0.580 / 1.779 |
| SDPB (BSRAM) | 64 | 0.801 / 0.801 / 0.801 | 0.641 / 0.641 / 0.641 |

**The 1.25x derivation does not hold.** The vendor's own C1/I0 slow-corner arcs sit at a
median **0.79** of the derived C1/I0 table and a median **0.98** of the table `P0.T35`
labelled C2/I1. On combinational logic — LUT4 and the BSRAM read path, 3,960 of the 7,136
arcs — the chunk-0 table is the closer fit by a wide margin (LUT4 0.92 vs 0.73), which is
what one would expect if **`.tm` chunk 0 is already the C1/I0 table** and the 1.25
multiplication is double-counting the grade. `P0.T36` established that chunks 0-2 are a
family-generic preamble byte-identical across 22 GW5* devices and that no chunk is a
second graded table; this measurement says the one graded table there is C1/I0, not C2/I1.

Two caveats Phase 6 must settle before rewriting the parser:

1. **Sequential arcs go the other way.** Every DFF `CLK->Q` in the SDF is 1.49x chunk 0 and
   1.19x the derived table, so the flop model is *optimistic* on both hypotheses; a single
   global rescale cannot fix both LUT and DFF. The per-group structure is wrong, not just
   a constant.
2. **The vendor's per-instance spread is real.** The same logical LUT4 pin carries
   different delays on different instances (e.g. `I0->F` seen at 0.260/0.411/0.457/0.493/
   0.511/0.521 ns), because Gowin permutes the physical LUT inputs and derates per
   instance; nextpnr installs one value per pin pair. That spread is why min/max span
   0.37-1.78 and why only the medians are meaningful. Part of the L0 failure is this
   structural difference, not a table error.

Handed to `W-TIMING` Phase 6 (`S17b`, `S18`) as the concrete input `P0.T35` asked for:
re-identify `.tm` chunk 0's grade against these medians before trusting `1.25`.

## Reproducibility note (measured, not assumed)

The vendor run was executed **twice** back to back. The two `run.sdf` files are
byte-identical except the `//Created Time:` header line, and so are the two `run.fs`
(3 differing bytes, all inside that line); the `V12a` contract line and every ratio above
are bit-identical across the two runs. So Gowin PnR is deterministic here, but **a sha256
over a `.fs`/`.sdf` is not reproducible** because the file embeds its own creation time —
which is why `evidence/calibration/runs.jsonl`'s `vendor_fs_sha256` for `attosoc`
(`494eca8f…`) no longer matches the regenerated artefact (`d4f76ad4…`). Noted, not fixed
here: it is `P0.T33`'s row and a cross-cutting evidence-hygiene item.

## Artefacts

| what | path | sha256 |
|---|---|---|
| vendor SDF (1,594,366 B, not copied) | `$DATASTORE/calibration/attosoc/run/impl/pnr/run.sdf` | `6cd3c03f7ad1f0155f4af7e7736faa63805c1623a10bac93d1c738016df2598a` |
| same, run 1 of 2 (timestamp line only) | (superseded) | `8e2207aaac50a56b57d3f978d7d0c95411a9a54ca281279d578d8dbd195905e9` |
| vendor timing report | `$DATASTORE/calibration/attosoc/run/impl/pnr/run.tr` | recorded in the row |
| chipdb consumed | `apicula/apycula/GW5AST-138C.msgpack.xz` | `fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb` |

`$DATASTORE = /Users/alex/fine-line-data/open-toolchain-gw5ast`. The heavy intermediates of
the run tree (`run.pr` 83 MB, `run.bin`/`run.binx`, the HTML reports) were deleted; the
tree is left in the `P0.T33` shape (`run.fs`, `run.tr`, `run.vo`) plus `run.sdf`.

## Tool fixes forced by the real SDF (`P0.T37`, tests in `tools/tests/test_check_timing_l0.py`)

Both are parse/mapping fixes. Neither touches the band, the corner convention or the
verdict rule.

1. **`norm_pin`** — the vendor SDF names a BSRAM data-out bit `DO[0]`; nextpnr's cell
   variants name the same bit `DO0` (`RAM16SDP4` uses brackets on both sides). Without
   normalising the bracket form, all 64 BSRAM arcs landed in `unmapped` and the BSRAM half
   of `D60`'s CFU class was silently never measured. `7072 -> 7136` compared arcs.
2. **multi-line condition header** — a real Gowin SDF puts `VOLTAGE`, `PROCESS` and
   `TEMPERATURE` on three lines; the tool took the first match and dropped the process and
   temperature corner, i.e. exactly what `D49f` requires be recorded. All header condition
   lines are now joined into the one line `V12a` allows, each verbatim, in file order.
