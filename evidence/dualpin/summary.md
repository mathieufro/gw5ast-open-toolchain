# Dual-purpose pins on the GW5AST-138C (`P2.T27`-`P2.T29`)

`spec-primitives.md` §6 asks one question per option: which fuses does handing
this configuration port to the fabric actually move, and does `gowin_pack`
move the same ones? Ten vendor runs answer it — an all-off baseline and nine
sweep points, each diffed against that baseline so the moved bits isolate the
option and nothing else.

Batch `p2t29-dualpin2`, chipdb `85701f94…`, IDE 1.9.12.03 Standard, no
`edu-provisional`. The shape is a `CLKDIV` at HCLK block 5 with a ring-counter
context; the design is byte-identical at every point.

## 1. The nine points

| option | vendor bits | packer bits | symmetric difference | level | verdict |
|---|---|---|---|---|---|
| `jtag` | 1 | 1 | **0** | `E1` | ok |
| `sspi` | 21 | 1 | 20 | `E1` | ok |
| `mspi` | 1 | 1 | **0** | `E1` | ok |
| `ready` | 1 | 1 | **0** | `E1` | ok |
| `done` | 1 | 1 | **0** | `E1` | ok |
| `reconfign` | — | — | — | — | **refused** (vendor) |
| `cpu` | 0 | 2 | 2 | `E1` | ok |
| `i2c` | — | — | — | — | **refused** (open flow) |
| `ae350_triple` (`sspi`+`mspi`+`cpu`) | 22 | 4 | 22 | `E1` | ok |

Seven points close at `E1`; two are named refusals, which `D30` makes a
deliverable with its own verdict rather than a hole. Both are recorded with
the tool's exact words, and the harness now classifies them as such instead of
calling a device fact a crash.

## 2. The configuration fuse, per option

Every option that moves a configuration bit moves exactly one, in tile
`(180, 108)`:

| option | bit | `gowin_pack` emits it |
|---|---|---|
| `done` | 2486 | yes |
| `ready` | 2488 | yes |
| `jtag` | 2489 | yes |
| `sspi` | 2491 | **yes, as of `P2.T27`** |
| `mspi` | 2492 | yes |

`sspi` is the gap this phase closed. The 138C override of
`get_pins_attr_vals` had no `sspi` branch at all — both sibling GW5 devices
emit `SSPI_AS_GPIO` unconditionally — so `--sspi_as_gpio` was parsed and
dropped, and bit 2491 was never set. It now matches the vendor exactly.

## 3. `SSPI_AS_GPIO` also reconfigures the pins it releases

Beyond bit 2491, the vendor moves **20** further bits, in two tiles:

| tile | bits |
|---|---|
| `(166, 108)` | 300, 410, 411, 415, 758, 806, 807, 810, 872, 873, 874, 924, 926, 929, 930, 934 |
| `(167, 108)` | 1034, 1035, 1160, 1163 |

These are `IOB` longvals of the pins SSPI occupies: releasing a configuration
pin to the fabric reconfigures that pin's IOB. That is the **`io_used_pin_config`
class** — the one `evidence/ae350/e1-138c.md` §6 named and left to `W-IO`
(Phase 3) — and it is now attributed to a cause rather than merely counted.
`gowin_pack` does not emit them, and this phase does not teach it to: a used
pin's IO configuration is the class PR #423 fixed, and emitting an IO setting
the vendor does not emit for the same pin is a live thermal hazard, not a
completeness win. The bits are named here so Phase 3 starts from a cause.

## 4. `cpu_as_gpio`: apicula sets two bits the vendor does not

The `cpu` point is the one asymmetry pointing the wrong way. With
`-use_cpu_as_gpio 1` the vendor moves **no bit at all**, on this design and on
the `ae350_triple` point; `gowin_pack` sets `CPU_AS_GPIO_0` and `CPU_AS_GPIO_1`
at `(180, 108)` bits 2502 and 2503. Recorded as a `DIFF`, not a note.

The caveat that keeps it from being a fix on the spot: neither point
instantiates an `AE350_SOC`, and no CPU pin is claimed by either design, so
the vendor may legitimately treat the option as a no-op here. What is
established is the direction — apicula is the side setting bits nobody has
seen the vendor set — and the closing evidence is a vendor build that both
instantiates the block and claims the CPU pins, which is Phase 9's hardware
row. Until then the two attributes stay as they are and this line is the
record.

CPU_AS_GPIO_2 (attrid 37) is defined for this device and sets no bit: the
vendor moves no bit at all under `cpu`, so there is nothing for a third handle
to explain, and the marker `P2.T27` left is resolved by deletion rather than
by emission. An attrid
that is defined and never emitted is a `7.5` defect only while it is
unexplained; this is the explicit refusal `D30` asks for.

## 5. The two refusals

**`reconfign` — the vendor refuses.** `gw_sh` exits 1 with
`configuration that does not support RECONFIG_N` on
`set_option -use_reconfign_as_gpio 1`. The option exists in the vendor's own
option table for this tool but not for this device configuration. `gowin_pack`
accepts `--reconfign_as_gpio` and emits `RECONFIG_AS_GPIO` at `(180, 108)`
bit 2490, so the packer is more permissive than the vendor here and that bit
is unmeasured — the vendor will not build a design that would confirm it.

**`i2c` — the open flow refuses.** `gowin_pack` raises
`i2c_as_gpio has conflicting settings in nexpnr and gowin_pack.` The cause is
in nextpnr: `pack_pincfg` adds the `I2C` parameter only when
`gwu.has_I2CCFG()`, which is false for this device, so the packer flag and the
placed netlist can never agree. Consistent with the fuse side —
`get_dualpin_fuses()` returns nothing for `i2c` on this device, because
`I2C_AS_GPIO` has no entry in its configuration table. **The 138C has no I2C
configuration pins**, and the two tools already agree on that; what they do
not do is say so before the packer crashes. Refusing `--i2c_as_gpio` by name
on a device with no I2C configuration entry is the fix, and it belongs with
the CLI surface (`P2.T30`), not here.

## 6. What `P2.T27` did to the `AE350_SOC` row's residual

Measured, not estimated: the `P2.T23` design was re-packed with the corrected
packer and compared against **the same vendor bitstream**, so the only thing
that differs is `SSPI_AS_GPIO`.

| | differing bits | tiles |
|---|---|---|
| `P2.T23` packer | 3 898 905 | 17 778 |
| `P2.T27` packer | 3 898 847 | 17 777 |
| delta | **-58** | **-1** |

Where the 58 went: **1** is the configuration fuse itself, `(180, 108)` bit
2491, and the other **57** are in the AE350's own configuration band — tiles
`(156, 10)`, `(157, 10)`, `(158, 10)`, `(159, 10)`, `(160, 10)`, `(158, 28)`,
`(159, 28)`, `(159, 46)`, `(159, 64)`. Every one of them moved *toward* the
vendor: the total fell by exactly the number that changed, so none moved away.
Setting `SSPI_AS_GPIO` changes what the packer computes for the block's band,
not just one config bit.

**The `io-config` residual proper is unchanged, and deliberately.**
`evidence/ae350/e1-138c.md` §6's two classes — `io_used_pin_config` 333 bits /
167 tiles and `io_nondefault_config` 309 / 154 — are `IOBA`/`IOBB` longvals of
used pins, and §3 above shows exactly what the vendor does there for `sspi`:
20 bits in tiles `(166, 108)` and `(167, 108)`. `gowin_pack` still does not
emit them and this phase does not teach it to. Closing that class means
emitting an IO configuration for a used pin, which is the class PR #423 fixed;
it stays `W-IO`'s (Phase 3), now with a measured cause attached rather than
only a count.

## 7. `mode_as_gpio`: an option apicula does not have

`gw_sh` accepts `-use_mode_as_gpio` — it is in the tool's option table beside
the eight apicula knows. `gowin_pack.CliArgs` has no `--mode_as_gpio` flag and
`attrids.cfg_attrids` no `MODE_AS_GPIO` handle. Unswept and unmeasured, named
here so it is a known absence rather than an unknown one.

## 8. Mask

Untouched, as `P2.T28` requires. This is a **configuration** shape, not an I/O
shape: the swept parameter is a chip-level configuration attribute and the six
pins are context held fixed, so the mask's IO-default entry has no bearing on
it. Masking anything here would erase the very bits the sweep exists to find.

## 9. Ledger

Sub-ledger `ae350-dualpins`, authorised at ten runs; **thirteen** spent. Three
of them bought the shape: the first vehicle — one input, one flop, one LED —
cannot reach `E1`, and only a vendor run could show why (§ `evidence/_runs/
p2t29-dualpin-void.log`). The vendor emits an `R<r>C<c>[cls][half]` column in
its `.tr` only for real register-to-register paths, and that design has none,
so its realised placement is unreadable; and the only tile it could scope is
the flop's, where GowinSynthesis's `DFFRE` and yosys's `DFF` differ before the
sweep says anything. The `CLKDIV` vehicle has neither problem. The overrun is
three runs and is recorded rather than absorbed.
