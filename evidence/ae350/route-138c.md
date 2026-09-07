# `P2.T22`/`P2.T23` — the open flow routes `AE350_SOC` and packs a bitstream

apicula/nextpnr branch `ae350/route-138c`. **0 new vendor runs** (ledger stays
at 2 of 8); both bitstreams compared here are run `p2t26-tilewires` and its
no-block control `p2t26-baseline`, banked.

## 1. `P2.T10`'s residual class is refuted

`P2.T10` read the router failure as a *placement* constraint: "every one of the
867 bound ports names a fabric tile's own wire … each net therefore has exactly
one legal fabric endpoint bel". Measured, that is wrong in its premise.

| fact | measurement |
|---|---|
| die row 0, tile type 242 | **0 bels**, 125 pips (`db.tiles[242].bels == []`) |
| `Q0`/`F0`/`OF0` in ttyp 242 | pip **sources** only — 23 / 29 / 4 pips; **0** pips end on them |
| `A0`/`CLK0`/`CE0`/`LSR0` in ttyp 242 | pip **destinations** — 28 / 28 / 20 / 20 sources each |

There is no bel to constrain, and no constraint is needed: a tap is an ordinary
local wire of a bel-less routing tile, reachable through that tile's pips. What
was actually wrong is the **direction** of every tap.

## 2. How the vendor placed the port cells — read from the bitstream

`gowin_unpack.parse_tile_(default=False)` over `p2t26-tilewires`' `.fs` minus
`p2t26-baseline`'s, rows 0-3, columns 140-181:

| region | what the vendor did |
|---|---|
| die row 0, cols 161-180 | **no bel at all**; 415 pips whose *destination* is a row-0 `A`/`B`/`C`/`D`/`CE`/`CLK`/`LSR` wire, and 418 pips whose *source* is a row-0 `F`/`Q`/`OF` wire |
| die row 1, cols 154-164 | the LUT buffers — `LUT0`-`LUT7` in 11 tiles |
| elsewhere | the 905 shift/capture flops, placed freely |

So the vendor places **nothing** in the AE350's own tiles. Its input pins are
fed by ordinary fabric routing into row-0 `A`-`D`/`CE`/`CLK`/`LSR` wires; its
output pins are read out of row-0 `F`/`Q`/`OF` wires. Per class:

```
row-0 pip destinations set by the vendor:  A 97  B 101  C 96  D 100  CLK 6  CE 13  LSR 2   = 415
row-0 pips sourced from block wires:       F 165  OF 164  Q 89                             = 418
```

`CE` 13 is exactly the block's 13 clock-enable inputs (`CORE_CE`, `AXI_CE`,
`DDR_CE`, `AHB_CE`, `APB_CE[0..7]`, `APB2AHB_CE`); `LSR` 2 is exactly its two
asynchronous resets; `CLK` 6 is exactly its six clock inputs. No *output* port
is a clock, an enable or a reset, so the direction is not a matter of opinion.

## 3. The constraint mechanism: none — a re-derived port map

`fse_create_ae350` bound `Ae350SocIns` to the input ports and `Ae350SocOuts` to
the output ports. Under that binding every input pin sat on a `Q`/`F`/`OF` wire
that no pip can drive — an unreachable sink — which is precisely the router's
`Failed to find a route for arc 1 of net drv[390]`.

The tables are not one direction each. Classifying every record by its wire:

| table | slots | `F`/`Q`/`OF` | `A`-`D`/`CE`/`CLK`/`LSR` |
|---|---|---|---|
| `Ae350SocIns` | 416 | 398 | 0 |
| `Ae350SocOuts` | 495 | 53 (slots 0-43 and 478-494) | **416** (slots 44-477) |

416 is the block's input-bit count to the bit. So `Ae350SocOuts` holds the whole
input map in one run, with the head and tail of the output map either side of
it, and `Ae350SocIns` holds the output map's middle run. The run bounds are
*derived* from the wire classes in `fse_create_ae350`, never written down.

Within the head run the slot order and the port order disagree, so the class
decides there: an `LSR` tap can only be a reset input and a `CLK` tap only a
clock input. That is the one place the map is ordered by class rather than by
slot, and it is recorded as such.

Result: **416 input bits bound, 468 output bits bound, 27 unmapped, 0 taps
pointing the wrong way** (`tests/test_ae350_tap_directions.py`).

## 4. The router change

One line, in `gowin_arch_gen.py`. `create_reuse_wire(tt, wire, "AE350_IN")`
calls `set_wire_type` on a wire the tile already owns, so an AE350 clock tap
stripped `TILE_CLK` from the tile's `CLK` line — for every cell in that tile,
not only the AE350. `globals.cc:79` reads that type to decide a clock sink is
legal, which is why `P2.T10` saw *"Failed to route net 'clk_IBUF_I_O' … using
dedicated routing"* six times and fell back to the ordinary router. A tap now
keeps the type its wire already carries; only a wire the tile does not have
gains an `AE350_IN`/`AE350_OUT` type. No change was needed in `globals.cc`
itself and none was made.

## 5. The pair

| artefact | sha256 |
|---|---|
| `GW5AST-138C.msgpack.xz` | `d6e00bdc919cf4e248a98337a4891781b43e25844749f7ff03afda34ded8c367` |
| `chipdb-GW5AST-138C.bin` | `85701f94db2af0dfd04ccf64458b7f9be5dc2ed0c524ac8a890b024afe7af010` |
| `nextpnr-himbaechel` | `d63e552b31f298dc59225bb48ef321ec8304c906da63a0b0b76ec20ccf35ceb5` |

Installed to `$DATASTORE/chipdb/{p2t22,std}` and
`$DATASTORE/toolchains/nextpnr/{bin,share/himbaechel/gowin}`.

## 6. The open-flow build (`P2.T22`)

Run `p2t26-tilewires`' own `top.v`/`top.cst`, all 149 ports.

| stage | result |
|---|---|
| yosys 0.63 | ok — `AE350_SOC` survives as one blackbox beside 905 flops |
| nextpnr pack | ok — 27 ports disconnected with a warning each: exactly the 27 unmapped bits |
| nextpnr place | ok — the cell binds to its single bel at `X159Y0` |
| nextpnr global router | **ok** — `clk_IBUF_I_O` routed over the clock plane, no fallback |
| nextpnr route | **ok** — 4136 arcs, 0 errors, 5.14 s |
| `gowin_pack` | **ok** — `top.fs` 34 668 145 B, sha256 `b07b3ed496591f44f3436d45dde5dbf0d2ad47596ba0b96eb53cea3df558e315` |

`--timing-allow-fail` was passed; the design has no interior timing path, so
nothing depended on it. nextpnr needs `--vopt sspi_as_gpio` to agree with
`gowin_pack --sspi_as_gpio`; `cpu_as_gpio`/`mspi_as_gpio` exist only on the
`gowin_pack` side and `get_PINCFG_fuses` checks only `i2c`/`sspi`.

## 7. `E0` (`P2.T23`) — not reached, and why

```
DIFF_COUNT cells=134248 attrs=148339 conns=553776
RESIDUAL_UNEXPLAINED entries=2 bits=658 bytes=0
DECODE_CHECK c1=mismatch c2=ok (c1 recovered 2039/2111 placed cells, 6 not fuse-backed; c2 0 differing bytes of 4147478)
MASK sha256=59147bfc633e10c5c1f4875bef6cf0cf9b76f8d58868ffc084f8c252557a1ec0 entries=6
CALIBRATION FAIL top: 836370 diffs enumerated, 2 unexplained
```

**E0-VERDICT: not reached — no scope exists.** `equiv.compare_design` refuses an
unscoped `E0` by design (`D32`, F6), and there is no `ae350_soc` `ShapeSpec`:
`P2.T20` authored one for the `Emb_TCM` vehicle that the `P2.T26` re-scope
replaced, and the 149-port vehicle was never given one. The run above is
therefore `--calibration`, the **whole-device** comparison, and its
`DIFF_COUNT` is dominated by free placement — nextpnr put the 905 flops
somewhere other than the vendor did, which `E0` masks and calibration does not.

Per-tile, that is exactly where the difference is:

| region | tiles | cells | attrs | conns |
|---|---|---|---|---|
| die row 0, cols 150-181 (**the AE350 band**) | 32 | **0** | **0** | **2** |
| everything else | 17 450 | 134 725 | 148 339 | 567 189 |

The block's own band is clean. The two `RESIDUAL_UNEXPLAINED` entries are
`io_used_pin_config` (348 bits, 166 tiles) and `io_nondefault_config` (310 bits,
154 tiles) — the `W-IO` (Phase 3) classes, neither of them AE350. `DECODE_CHECK`
`c1` is a `mismatch` because 72 of 2111 placed cells are not recovered from the
open `.fs`; `c2` is byte-exact.

**Residual classes, precisely:**

1. **`no-scope`** (blocking, owns the `E0` verdict) — the 149-port vehicle has
   no `ShapeSpec`, so `E0` cannot be scoped and only calibration runs. Fix is a
   `shapes/ae350_soc.py` for *this* vehicle: mechanical, one task, 0 vendor runs.
2. **`decode-c1`** — 72 placed cells not recovered by `gowin_unpack` from the
   open `.fs`, 6 of them not fuse-backed at all. Not AE350-specific.
3. **`io-config`** (`W-IO`, Phase 3) — the two enumerated residual entries.
4. **`head-order`** (open, AE350) — within the input map's head run the slot
   order and the port order disagree, and only the wire class resolves it. The
   assignment *among* the six clock inputs is therefore not established: this
   vehicle drives all six from one net, so no measurement here can separate
   them. It needs a vehicle with six distinct clock sources — a design change,
   hence a vendor run, hence an owner call against the 6-of-8 remaining budget.

`P2.T22` DONE-STD clause (a) is discharged: the open flow builds the same design
end to end and produces a bitstream. `P2.T23` is **blocked on residual class 1**
and no `runs.jsonl` row is appended with a non-terminal verdict (`D33`).
