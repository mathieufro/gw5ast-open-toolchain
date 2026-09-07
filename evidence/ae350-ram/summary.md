# `P2.T25` — the `AE350_RAM` row: the device has no such resource

apicula branch `ae350/ram-row-138c`. **2 vendor runs** (`p2t25-ae350-ram-soc`,
`p2t25-ae350-ram-solo`); ledger 6 of 8.

```
VERDICT              refused (both companion points, both flows)
VENDOR               ERROR (RP0008) : There is no AE350_RAM resource in current device,
                     please change device
OPEN FLOW            ERROR: Unable to place cell 'u_ae350_ram', no BELs remaining to
                     implement cell type 'AE350_RAM'
DIFF_COUNT           undefined -- GowinSynthesis stops before place and route, so there
                     is no vendor bitstream to diff
RESIDUAL_UNEXPLAINED []   (nothing was decoded; the row records that, it does not claim it)
DECODE_CHECK         c1 n/a   c2 n/a
```

## 1. The experiment

`shapes/ae350_ram.py` has two companion points, and the second exists to
close the loophole in the first.

| point | design | why |
|---|---|---|
| `soc` | the `P2.T20` 149-port `AE350_SOC` vehicle **byte for byte**, with one `AE350_RAM` spliced in | isolates one variable, so a presence diff against the `P2.T23` bitstream would have shown the `AE350_RAM` and nothing else |
| `solo` | the same `AE350_RAM` with no `AE350_SOC` beside it | separates *the device has no such resource* from *the one AE350 site is already taken* |

The `soc` point wires every `AE350_RAM` input to the net the `AE350_SOC`'s
identically-named input already carries. That is MUG1031's external-AHB view
rather than a convenience: `EXTM_*` is an AHB **slave** port on *both* blocks
— `EXTM_HADDR` is an input and `EXTM_HRDATA` an output on each — so one
external master drives both and `EXTM_HSEL` picks between them. Only
`EXTM_HSEL` is the RAM's own net, from its own `INS_LOC`-pinned flop, because
two slaves that share a select have no external-master semantics at all. The
three outputs cannot share a net with the `AE350_SOC`'s three same-named
outputs — two drivers, one wire — so they drive their own XOR capture chain.

Sharing the other nets costs nothing: if the two blocks tap different wires
the router lights the second wire up and the diff shows it; if they tap the
same wire, nothing moves.

## 2. What the vendor said, twice

Both points stop in `GowinSynthesis`, at tech-mapping phase 4, in ~1 s:

```
ERROR (RP0008) : There is no AE350_RAM resource in current device, please change device
```

The control is `P2.T23`: the same `gw_sh`, the same device, the same fixed
Tcl header and the same `top.v` minus the `AE350_RAM` builds to a bitstream.
So `RP0008` names the `AE350_RAM` and not the AE350 family, and — because the
`solo` point says it with the `AE350_SOC` absent — it is not a contest over
the single `AE350_SOC` site either. The refusal is the primitive's, and it is
unconditional on this device.

Three independent sources agree, and none of them is the error message:

| source | reading |
|---|---|
| `GW5AST-138C.dat`, `gw5aStuff` | 120 keys. `Ae350SocIns`/`Ae350SocOuts` map the SoC's 149 ports; **no key matches `Ram`** |
| the `DDR3_Shared` golden netlist (`P2.T05`) | `grep -c AE350_RAM` = **0**; the reference design drives the SoC's `EXTM_*` out to fabric DDR3 |
| `prim_syns/gw5a/primitive.xml` | declares the module — but that file is **family**-wide, and `gw5a` covers devices this one is not |

`primitive.xml` is therefore a declaration of the *language*, not of this
die's resources, and `P2.T05`'s finding that all 26 `AE350_RAM` ports are an
exact name/direction/width subset of `AE350_SOC`'s 149 now reads the obvious
way: the RAM view is the same interface described for a device that carries
the block on its own.

## 3. The model: no bel, and no alias either

`P2.T09` asked for an `ae350_ram` entry in `dev.extra_func`, as a second bel
or as an alias of the `AE350_SOC`'s `EXTM_*` taps — the `create_reuse_wire`
hazard `port-inventory.md` flagged. **Neither is admissible.** A bel for a
resource the vendor's own front end denies would let the open flow accept a
netlist the vendor refuses, which is precisely the parity defect this phase
exists to prevent; and an alias would put two output pins of two bels on one
wire, which is a second driver by construction.

So the chipdb is **unchanged**: no `ae350_ram` key, no second bel, no alias,
and the `AE350_SOC` port map keeps every `EXTM_*` tap it already owns.
`GW5AST-138C.msgpack.xz` stays `d6e00bdc`, `chipdb-GW5AST-138C.bin` stays
`85701f94` and the installed `nextpnr-himbaechel` stays `d63e552b` — the pair
is untouched, so nothing was rebuilt or reinstalled.

Two tests pin the absence rather than leaving it as a silence
(`tests/test_ae350_ram_absent.py`): the built 138C device declares an `ae350`
entry and no entry whose name contains `ram`, and the device data carries the
two `Ae350Soc*` tables and no RAM table.

Fuses: **zero**, and not by measurement of a bitstream — there is no
bitstream. The row says `n/a`, never `ok`, for both decode checks.

## 4. Parity of the refusal

The open flow refuses the same two designs, and gets further before it does:
yosys exits 0, nextpnr reads the netlist, places all 11 `INS_LOC` cells
(the `P2.T20` nine plus this shape's two witnesses) and reports `AE350_SOC`
utilisation 1/1, then fails on the one cell that has no bel:

```
ERROR: Unable to place cell 'u_ae350_ram', no BELs remaining to implement cell type 'AE350_RAM'
```

That is the right answer with a weaker sentence than the vendor's: nextpnr
says *no bel remaining*, where the truth is *no bel at all, on this device,
ever*. It is left as measured rather than dressed up — inventing a named
refusal would mean adding an `AE350_RAM` constid to nextpnr for a cell type
the device does not have, which is the same mistake as adding the bel.

## 5. Consequences for the phase

* `spec-primitives.md`'s `AE350_RAM` 138C status cell now records the
  refusal; the row's Done criterion (`DONE-STD at E0`) is met by a terminal
  `refused` verdict with the vendor's exact words (`D30`,
  `spec-harness.md` §5.2), not by an `E0` comparison that has no two sides.
* `P2.T09` (the `ae350_ram` extra-func entry) is **VOID on this device**: its
  two tests assert a bel that must not exist. `rescope.md` rev 5 records it.
* Nothing in the `AE350_SOC` row moves. The `EXTM_*` taps it maps are the
  SoC's, and always were.

## 6. Two named boundaries of this result (gestalt-p2 `D4`, 2026-09-07)

The refusal is the best-evidenced result in the phase, and it is still
bounded by what was actually run:

* **IDE edition.** Both vendor points (`RP0008` on `soc` and `solo`) were run
  on **IDE 1.9.12.03 Standard** only. The `.dat` cross-check (`gw5aStuff`, 120
  keys, no `Ram` match) was separately confirmed on both shipped editions
  (§2 above), but the vendor's own front-end refusal — the `RP0008` message
  itself — was not re-run on Education 1.9.11.03. A hypothetical edition-gated
  resource would not be caught by this row as written.
* **`.dat` search term.** The 120-key `gw5aStuff` search was for the substring
  `Ram` (case-sensitive per §2's table). A table under another spelling —
  e.g. an abbreviation, a different capitalisation, or a name that does not
  contain `Ram` at all — would not have been seen by this search and would
  read as "no key matches" regardless of whether it exists.

Neither boundary is worth a vendor run on its own; both are worth stating so
the refusal is not read as broader than what was measured.
