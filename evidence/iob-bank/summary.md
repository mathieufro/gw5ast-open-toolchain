# IOB / bank-default safety row — GW5AST-138C (`P3.T26`)

**Verdict: `refused:unused_pin_drive_default`. Safety verdict: HOLD — this
device must not reach the Hardware Gate (`P9`) on the open flow's current
unused-IO defaults.**

**0 oracle runs spent.** The row is decoded entirely from vendor/open bitstream
pairs already in the datastore, so the 4 runs the blueprint budgets for it are
unspent. 35 pairs: the `T23` AE350 vehicle (`ae350-row`, `ae350-e0`), the three
`P0.T33` calibration baselines (`big-shift`, `attosoc`, `uart-message`), the
`P0` E2E smoke, three clocking runs (`p1f3-a`, `p1f3-c`, `p1f3-e2e`) and all
24 ODDR/IDDR, OSER and IDES runs of this phase (`p3t12`, `p3t12b`, `p3t13`,
`p3t13b`, `p3t14`).

Driver: `$OTC/tools/derive_iob_safety_138c.py`. Raw result:
`iob-safety.json`. Rows: `runs.jsonl` (35). Tests:
`$OTC/tools/tests/test_iob_safety_138c.py` (7).

Everything below is read off the **unpacked bitstream** (`D20b`), through
apicula's own `parse_attrvals` against `db.longval[ttyp]['IOBA'|'IOBB'|'BANK']`
— never off the packer's intent. Pin state comes from the open flow's
placement (`top_pnr.json` `NEXTPNR_BEL`), which both flows share because they
are driven by the same `.cst`.

## The claim, and how it lands

| half of the claim | verdict |
|---|---|
| the open flow never sets a bank/IOB fuse the vendor does not, for the same pin state | **FAILS** — 22 189 violations over 35 designs |
| it never leaves a used pin's `IO_TYPE` / bank `VCCIO` unset | **HOLDS** — 0 `unset_on_used`, `IO_TYPE` equal on 117/117 used inputs and 143/143 used outputs, `BANK_VCCIO` equal on 71/71 used banks |

## Fuse classes found, per pin state (vendor vs open)

Counts are site-observations summed over the 35 designs. `equal` = both sides
decode the attribute to the same value; `open_only` / `vendor_only` = only that
side sets it at all.

### unused pin (≈316 IOB halves per design)

| attribute | equal | open_only | vendor_only |
|---|---|---|---|
| `IO_TYPE` | 11 080 | 0 | 0 |
| `OPENDRAIN` | 11 080 | 0 | 0 |
| `PADDI` | 11 080 | 0 | 0 |
| `PULLMODE` | 930 | **35** | 4 |
| **`DRIVE`** | 70 | **11 010** | 0 |
| **`DRIVE_LEVEL`** | 70 | **11 010** | 0 |
| `LVDS_OUT` | 0 | 0 | 11 010 |
| `ODMUX_1` | 35 | 0 | 35 |
| `HYSTERESIS` | 0 | 0 | 3 |

### used input (117 sites)

`IO_TYPE`, `LVDS_OUT`, `OPENDRAIN`, `PADDI` equal on all 117; `PULLMODE` equal
on 91, `open_only` on 1; `HYSTERESIS` `vendor_only` on 114.

### used output (143 sites)

`IO_TYPE`, `OPENDRAIN`, `PADDI` equal on all 143; `DRIVE`, `DRIVE_LEVEL`,
`ODMUX_1`, `IOB_UNKNOWN51`, `PULLMODE` equal on 141-142 and `open_only` on
exactly 1 (the `ae350-e0` skew below); **`SLEWRATE` `open_only` on all 143**.

### diff pair

No differential IO is placed in any of the 35 designs, so the state is
unobserved here. `P3.T23`-`P3.T25` own it (`evidence/tlvds`, `evidence/elvds`).

### banks

| state | attribute | equal | open_only | vendor_only |
|---|---|---|---|---|
| used bank | `BANK_VCCIO` | 71 | 0 | 0 |
| used bank | `PULL_STRENGTH` | 70 | 1 | 0 |
| used bank | `LVDS_OUT` | 70 | 1 | 0 |
| unused bank | `BANK_VCCIO` | 209 | 0 | 0 |
| unused bank | `PULL_STRENGTH` | 0 | 0 | 2 |
| unused bank | `LVDS_OUT` | 0 | 0 | 2 |

The PR #423 bank fuse itself is therefore **correct on this device**:
`PULL_STRENGTH=MEDIUM` and `BANK_VCCIO` match the vendor bit for bit on every
used bank. The two `unused_bank` `vendor_only` observations and all four
`used_bank` `open_only` observations are the same one design, `ae350-e0`,
whose two halves are not the same design (a known `P2` skew), and are named
here rather than folded into the counts.

## The violation, named at fuse level

**`refused:unused_pin_drive_default` — 22 020 fuse bits over 35 designs,
2 bits on every unused IOB half of every design.**

`GW5A.get_unused_io_attrvals` (`gowin_pack.py:5530`, inherited unchanged by
`class GW5AST_138C`) emits, for every unused pin:

```
OPENDRAIN=OFF, IO_TYPE=LVCMOS33, DRIVE=8, DRIVE_LEVEL=8, PADDI, PULLMODE=<...>
```

Computed through the packer's own path (`add_attr_val` → `get_longval_fuses`)
at each unused site, and compared against both bitstreams:

| attribute-value set | fuses it programs | of which the vendor also sets |
|---|---|---|
| the full set above | **5** | 3 |
| the same set with `DRIVE` and `DRIVE_LEVEL` removed | **3** | 3 |
| `IO_TYPE=LVCMOS33` alone | **0** | — |

So the 2 bits per unused pin that the open bitstream sets and the vendor's does
not are **exactly the `DRIVE` / `DRIVE_LEVEL` contribution**, and nothing else:
they disappear when those two attributes are dropped, and they cannot be the
`IO_TYPE` default, because `IO_TYPE=LVCMOS33` is the zero code here and programs
no fuse at all. 315-319 unused sites carry them in every design measured; the
vendor programs **no** IOB fuse on an unused pin beyond the 3 shared bits.

**This corrects `P0.T33`.** That task settled the `io_default_unused_pins`
residual as "631 bits are `gowin_pack`'s unused-IO `IO_TYPE`/`BANK_VCCIO`
defaults ... no `DRIVE`/`PULLMODE`, so **NOT** the PR #423 class". Measured
here on the same `big-shift` baseline: **610 of those bits are `DRIVE` /
`DRIVE_LEVEL`**, `IO_TYPE` contributes zero, and the mask entry
`io_default_unused_pins` has therefore been masking a drive default on every
floating pin of the die. The `io_used_pin_config` / `io_nondefault_config`
residuals `P2.T23`/`T29` carried forward are the same bits seen from the
used-pin side.

Two smaller open-only classes ride with it:

- **`SLEWRATE=FAST` on every used output** (143/143). No `.cst` in the corpus
  asks for a slew rate; the vendor leaves the fuse unprogrammed and the packer
  programs `FAST`. A **default the packer invents**, not a design-specific
  value.
- **`PULLMODE` open-only on 35 unused sites and 1 used input** — one site per
  design, the `PULLMODE` bit inside the 3-bit no-drive subset.

## Per class: is the vendor's value a default the packer should emit?

| class | vendor | design-specific? | disposition |
|---|---|---|---|
| `DRIVE` / `DRIVE_LEVEL`, unused pin | unprogrammed | no — no `.cst` names a drive on an unused pin | **packer over-emits a default.** Not fixed here: see below |
| `SLEWRATE`, used output | unprogrammed | no — no `.cst` names `SLEW_RATE` | **packer over-emits a default.** Same decision |
| `PULLMODE`, unused pin | mostly equal | no | over-emitted on 1 site per design; same decision |
| `PULL_STRENGTH`, used bank | `MEDIUM` | no — it is the `D53` default | **correct as emitted**, bit-equal, no change |
| `BANK_VCCIO` | `3.3` | driven by `IO_TYPE` | **correct as emitted**, bit-equal, no change |
| `LVDS_OUT`, unused pin | set | — | vendor-only; the table is `lvds_out_is_aliased` on this die (`gowin_unpack.py`), so this is a decode alias, not a configuration the open flow omits |
| `HYSTERESIS`, used input | set on 114 | not named by any `.cst` | vendor-only: a **vendor default the open flow does not emit**. Not a claim-1 violation; recorded as a named gap for `P3.T27` |
| `IO_TYPE`, `OPENDRAIN`, `PADDI` | equal everywhere | — | no gap |

## Why no packer change is made here

The blueprint forbids it, and the measurement agrees with the blueprint:

- `P3.T26`'s **Must NOT change** list names `get_default_pull_strength` /
  `get_default_unused_io_type` / `get_default_io_type` — "changing a default is
  a separate, owner-visible thermal decision". `get_unused_io_attrvals` is the
  same decision one function along.
- It lives on `class GW5A` (`gowin_pack.py:5301`), **not** on
  `class GW5AST_138C` (`:6942`). Dropping `DRIVE`/`DRIVE_LEVEL` there changes
  `GW5A-25A` and `GW5AT-60B` too, which is an `S3` family regression this
  phase may not take.
- The change is not **provably vendor-equal**: the vendor programs no bit
  there, so removing the two bits is vendor-equal *at bitstream level*, but
  whether a floating pin is safer with the drive strength programmed or
  unprogrammed is a silicon question this project cannot answer without the
  Hardware Gate — and PR #423 exists precisely because the intuitive answer was
  wrong once already.

**Escalated to the owner as a thermal/spec decision**, with the numbers above.
A device-scoped `GW5AST_138C.get_unused_io_attrvals` override that drops
`DRIVE`/`DRIVE_LEVEL` (and a `SLEWRATE` decision for used outputs) is the
candidate fix; it needs the owner's price, not this task's.

## Safety verdict

`spec.md` §7.10 and `LOOP-BRIEF` §7 forbid emitting an IO configuration
matching the class PR #423 fixed. The open flow currently emits a drive default
on **100 % of the die's unused pins** that the silicon vendor does not,
uniformly across every design in the corpus. That is inside the PR #423
attribute class and is unverified for thermal effect.

- **The row is `refused`, not `E0`/`E1`.**
- **The Hardware Gate (`P9`) precondition is not met** for any bitstream built
  by the current open flow on this device. `P9` must re-assert this row (0
  oracle runs, the same driver) and see `violations == 0` in the
  `unused/DRIVE` and `used_output/SLEWRATE` classes before a `.fs` is loaded.
- No `PULL_STRENGTH` regression exists: PR #423's own fuse is bit-exact.

## Inherited-input `W-IO` (`gestalt-p2` `D1`) — partially answered

"Does a design that actually drives a released SSPI pin as a GPIO get the right
IOB configuration through the ordinary IO path?" Not from this corpus: no
design in it drives a released SSPI pin as a GPIO, so the 20 `sspi` bits at
`(166,108)`/`(167,108)` are unobserved here. What this row *does* settle is that
the ordinary IO path is not clean to begin with — it over-emits `DRIVE` on
every unused pin — so `W-IO` stays open and now has a named prior cause.
