# `evidence/dqce/` — DQCE on the GW5AST-138C

Two rows live here.

## `P1.T28` — the tile-type re-derivation

8 oracle runs (`p1-dqce-types`, `evidence/_runs/p1-dqce-types.log`), all
`verdict=ok`, 0 aborted. Ledger `runs/oracle-runs.jsonl`. Sweep: `n_dqce = 1..4`
simultaneous `DCE`, two CE-assignment sequences. Artefacts
`tiletypes-138c.md` / `tiletypes-138c.json`. It established that the pre-5A
search values 80/81/84/85 all resolve on this die and that three of the four
cells move fuses; it could not settle how many DQCE the die hosts, or which
spines they gate.

## `P1.T29`/`P1.T30` — the quadrants, the model and the open flow

**Full artefact: `quadrants-138c.md`.** Headline: the shipped 138C chipdb
carried **zero** DQCE entries (the `GW5AST-138C` branch of `fse_create_clocks`
returns before the builder), and the die has **two** quadrants, not four —
quadrant 1 at cell (54, 93) gating `SPINE8..13` and quadrant 2 at cell
(54, 88) gating `SPINE16..21`, twelve DQCE in all.

### Rows

| batch | runs | ok | aborted | what it measured |
|---|---|---|---|---|
| `p1t29-dce` | 3 | 3 | 0 | capacity and spine occupancy: `n = 1, 12, 13` `DCE` |
| `p1t29-dqce-e1`  | 1 | 0 | 1 | first open-flow attempt; aborted, `.bin` built from the wrong branch's `gowin_arch_gen` (`idstring_idx_to_str` assertion) — a process finding, not a device one |
| `p1t29-dqce-e1b` | 1 | 0 | 1 | second attempt; aborted, `Unable to place cell 'dce0', no BELs remaining to implement cell type 'DCE'` — nextpnr knew only the pre-5A spelling `DQCE`. The bel counts in that same log are the proof the chipdb half landed: `DQCE 0/12`, `DCS 0/4`, where the shipped pair reported neither |
| `p1t29-dqce-e1c` | 1 | see below | | the row proper, after nextpnr learned the `DCE` spelling |

```
BATCH_COMPLETE p1t29-dce runs=3 ok=3 diff=0 aborted=0
```

### Sweep

| batch | axis | points |
|---|---|---|
| `p1-dqce-types` | `n_dqce` simultaneous `DCE`, plus the CE-assignment order | `1, 2, 3, 4` x two CE sequences (8 runs) |
| `p1t29-dce` | `n_dqce` at and beyond the measured capacity | `1, 12, 13` |
| `p1t29-dqce-e1c` | quadrant under test | `q1` (the row proper; `q2` is the same cell shape, gating `SPINE16..21`) |

The capacity point `n = 13` is the one that fixes the count: twelve `DCE` place,
the thirteenth does not, which is how the twelve-DQCE figure above is a
measurement rather than a reading of the builder.

### Verdict

The row closes at **E0**, not E1, and the reason is structural. Verbatim, on
`p1t29-dqce-e1c` (design `clocking_dqce`, sweep `q1`, scope = both clock-bridge
cells):

```
EQUIV E0 ok
DIFF_COUNT cells=0 attrs=0 conns=0
PIPS diff=2019654 (statistic, never a verdict term)
PER_TILE (none)
RESIDUAL_UNEXPLAINED entries=0 bits=0 bytes=0
  ACCOUNTED net_route bits=448 bytes=0 tiles=2 mask_entry=net_route
E1 placement level=E0 constrained=0 matched=0 mismatched=0 unobserved=0
DECODE_CHECK c1=ok c2=ok (c1 recovered 15/15 placed cells, 18 not fuse-backed; c2 0 differing bytes of 4147478)
MASK sha256=59147bfc633e10c5c1f4875bef6cf0cf9b76f8d58868ffc084f8c252557a1ec0 entries=6 [header_words,crc_checksum_padding,unused_tile_fill,free_placement,net_route,io_default_unused_pins]
NOTE EC9: the open placement exported no CLS constraint, so there is nothing for E1 to assert
```

**Zero unexplained bits, zero cell/attr/conn differences, and the mask is
byte-identical to the `hclk` and `dhcen` rows' — it was not widened.**

**Why E1 is unattainable here (EC9).** A DQCE is not a CLS-addressed bel: it
lives in a clock-bridge cell and its site is chosen by the router, not by the
design, so neither flow exports an `INS_LOC`/CLS constraint for it and E1's
placement-identity half has nothing to assert. This is the same class as
`CLKDIV`, which has no CLS address either (`P1.T14`). The row therefore closes
at E0 with placement free, and the placement freedom is real: the vendor put
its DQCE on `SPINE8` in (54, 93) and the open flow put its on `SPINE19` in
(54, 88) — both legal, both inside the compared scope, and the difference is
accounted to `net_route`, which is never a verdict term.

**Two open-flow gaps were found and closed on the way, both recorded here
because a later reader will hit them:**

1. `gowin_arch_gen.py` must be the one from the branch the installed
   `nextpnr-himbaechel` was built from. Generating the `.bin` with the
   `clocking/gw5a-hclk-6block` copy while the binary came from
   `integration/p1-clocking` produces a `.bin` twice the size that the binary
   rejects with `Assertion failure: int(ctx->idstring_idx_to_str->size()) == idx`
   (`p1t29-dqce-e1`).
2. nextpnr knew only the pre-5A spelling: `ERROR: Unable to place cell 'dce0',
   no BELs remaining to implement cell type 'DCE'` (`p1t29-dqce-e1b`). Fixed by
   `X(DCE)` in `constids.inc` plus a rename at the head of `pack_dqce`, exactly
   the shape of the existing `DHCE`->`DHCEN` normalisation. That is a constids
   change, so the binary and the `.bin` were regenerated as a pair.

The decode check needed two additions, both narrower than the `DHCEN`
precedent they follow (`harness/equiv.py`):

* `PACKER_CLOCK_MUX_PLACEHOLDERS` — an unused `$PACKER_DQCE_*` / `$PACKER_DCS_*`
  placeholder writes no fuse *by construction* (`get_DQCE_fuses` /
  `get_DCS_fuses` return nothing without `DQCE_PIP` / `DCS_MODE`), so `c1` must
  not demand it back. The placeholder that *was* used keeps its attribute and
  stays required;
* `dqce_recovered_via_pip` — a used DQCE's whole signature is one spine
  multiplexer select fuse, and `gowin_unpack` recovers that as a **pip**: there
  is no DQCE cell in the unpacker's model on any device. So `c1` asks for the
  very pip the packer wrote, named in `DQCE_PIP`, instead of for a cell the
  bitstream format cannot carry.

### Artefacts

`quadrants-138c.md`, `tiletypes-138c.md`, `tiletypes-138c.json`,
`runs/oracle-runs.jsonl`, `runs/capacity-runs.jsonl`,
`runs/capacity-result.json`, `probe_capacity.py`,
`_runs/p1t29-dce.log`, `_runs/p1t29-dqce-e1*.log`.
