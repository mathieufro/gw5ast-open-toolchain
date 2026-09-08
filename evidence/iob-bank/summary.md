# IOB / bank-default safety row -- GW5AST-138C (`P3.T26`, re-diffed `P3.F2`)

## Verdict

**Verdict: `ok` on 34 of the 35 pairs, `diff` on one. Safety verdict: CLEAR** -- the open flow programs no IOB or bank fuse the vendor does not, on any pin state, on every pair whose two halves are the same design. **0 oracle runs spent, on either pass.** The row is decoded entirely from vendor/open bitstream pairs already in the datastore; `P3.T26` measured the defect and `P3.F2` re-measured the same 35 pairs after `D108` fixed it, both without a `gw_sh` invocation. 35 pairs: the `T23` AE350 vehicle (`ae350-row`, `ae350-e0`), the three `P0.T33` calibration baselines (`big-shift`, `attosoc`, `uart-message`), the `P0` E2E smoke, three clocking runs (`p1f3-a`, `p1f3-c`, `p1f3-e2e`) and all 24 ODDR/IDDR, OSER and IDES runs of this phase.

`spec.md` §7.10 and `LOOP-BRIEF` §7 forbid emitting an IO configuration matching the
class PR #423 fixed. **CLEAR**: the open flow programs no IOB or bank fuse the vendor
does not, on 34 of the 35 pairs, in every pin state; on the 35th, `ae350-e0`, the two
halves are different designs and the eleven remaining observations are named below.
**The Hardware Gate (`P9`) precondition is met** for a bitstream built by the open flow
as it stands: `P9` re-asserts this row (0 oracle runs, same driver) and requires
`violations == 0` in the `unused/DRIVE` and `used_output/SLEWRATE` classes before a
`.fs` is loaded; both are 0 here. No `PULL_STRENGTH` regression exists: PR #423's own
fuse is bit-exact.

## What changed, and what it cost

| class | `P3.T26` (before `D108`) | `P3.F2` (after) |
|---|---|---|
| violations, all 35 pairs | **22 206** | **11** |
| violations, the 34 pairs whose halves are the same design | 22 195 | **0** |
| unused-pin `DRIVE`/`DRIVE_LEVEL` bits the vendor does not set | **22 020** | **0** |
| unused pins carrying them | 305-319 per design | **0** |
| `SLEWRATE` open-only on used outputs | 143 / 143 | **0** (attribute gone from both sides) |
| `HYSTERESIS` on used inputs | vendor-only 114 | **equal 114** |
| unused-pin `PULLMODE` open-only | 35 (one pad per design) | **0**; the 930 bit-equal observations unchanged |

The eleven that remain are **all in one design, `ae350-e0`**, whose two halves are not
the same design -- a known `P2` skew this row named on its first pass -- so a pin that
is an output in one bitstream is unused in the other and the comparison has nothing to
say about it. Listed rather than folded into the verdict.

## The three packer changes (`D108`, `GW5AST_138C` only)

The `GW5A` base class, GW5A-25A and GW5AT-60B are untouched: none has this measurement,
and a default is not a thing to change on an unmeasured part (`S3`). Guard: rebuilding
the GW5A-25A chipdb with and without the change gives the same file,
`60f1ba427f964feab3048f5dca82dc075acf9374a456476919202626d1335564`, and `apicula
tests/test_iob_defaults_138c.py` asserts both siblings keep their own defaults.

1. **`get_unused_io_attrvals` drops `DRIVE` and `DRIVE_LEVEL`.** That is the whole 22
020-bit class; the row's own subtraction had already proved those two attributes are the
only thing that can program those bits.
2. **`SLEWRATE` becomes a design-only attribute** (`design_only_io_attrs`): no default,
emitted only when a design names `SLEW_RATE`. The vendor leaves the fuse clear on all
143 used outputs of the corpus.
3. **`HYSTERESIS` defaults to `ON` for inputs.** The vendor programs it on every used
input that carries the attribute at all (114 of 117; the other three are the `ae350-e0`
skew), so the inherited `NONE` (the zero code) left every receiver without the Schmitt
trigger the vendor gives it. Now bit-equal on all 114.

One refinement of `D108`'s wording, by measurement: `D108` says an unused pin should
carry `IO_TYPE`/`OPENDRAIN`/`PADDI` **and no `PULLMODE`**. The vendor does program a
pull on the configuration pads -- `PULLMODE` is bit-equal on 930 site-observations -- so
dropping it outright would have introduced 865 new divergences. The one open-only
`PULLMODE` was a single pad, `(R108C101)`/`IOBB`, which carries both `D08` and `SO`: the
vendor treats it as the serial-output pad and leaves it at the pull-up that costs no
fuse, where `_no_pullup_cfgs` made the open flow program `NONE`.
`GW5AST_138C._pullup_cfgs` names that one measured exception; every other `NONE` is left
exactly as it was.

## Vendor-only classes: what the open flow still does not emit

None of these is a claim-1 violation -- fuses the **vendor** sets and the open flow does
not -- but they are the row's remaining gaps, named not forgiven:

* **`DRIVE`/`DRIVE_LEVEL`, unused pin, 70 site-observations** (two pads per design). The vendor does program a drive on those two pads. Emitting a drive on a floating pad is exactly the class `LOOP-BRIEF` §7 forbids, so this stays a vendor-only gap until the two pads are identified and a rule naming them can be measured, rather than restored as a blanket default.
* **`IO_TYPE`/`OPENDRAIN`/`PADDI`/`ODMUX_1`, 35 site-observations each** (one pad per design), and `PULLMODE` on 4 -- unchanged from the first pass.
* **`LVDS_OUT`, unused pin**: `lvds_out_is_aliased` on this die, a decode alias rather than a configuration (see below).

## The instrument: an attribute is not a fuse

The first pass classified an attribute that decodes only on the open side as a violation
-- right when the open bitstream sets a bit the vendor does not, wrong when it does not:
`parse_attrvals` resolves a *smaller* bit set to a different name, so removing a fuse
can make an attribute appear. After `D108` exactly that happened at one unused pad per
design, where the open bit set is a strict subset of the vendor's (7 bits against 13 at
`(R108C110)`), and the decoder read the remainder as `LVDS_OUT=ON`.
`derive_iob_safety_138c.site_open_only_bits` now decides the claim at fuse level: where
the open bits at a site are a subset of the vendor's, nothing was invented and the
attribute is recorded as `decode_alias` -- 35 such observations, one per design, none a
violation. Tests: `test_iob_safety_138c.py`
(`test_an_attribute_backed_by_no_open_only_fuse_is_a_decode_alias` and its negative).

## How the re-diff was done, and why it can be believed

`repack_open_fs.py` rebuilds a stored run's **open** bitstream with `gowin_pack` alone,
from the run's own `top_pnr.json`, so placement is fixed and only the packer's
contribution moves. Dual-purpose-pin flags are not guessed: `nextpnr` records the two
the packer cross-checks (`SSPI`, `I2C`) as `PINCFG` parameters, and `gowin_pack` raises
when the two sides disagree. The guard that makes the comparison mean anything:
repacking with the packer **as it stood before the fix** reproduced the stored `top.fs`
byte for byte on 24 of the 35 designs, giving **22 206** violations -- `P3.T26`'s own
number, to the unit. The other 11 designs were packed by older `apicula` commits, so
their baseline was re-established at `HEAD` rather than assumed. Only then was `D108`
applied and the 35 repacked again.

Everything is read off the **unpacked bitstream** (`D20b`), through apicula's own
`parse_attrvals` against `db.longval[ttyp]['IOBA'|'IOBB'|'BANK']` -- never off the
packer's intent -- and the claim itself is decided at fuse level (see "The instrument"
above). Pin state comes from the open flow's placement (`top_pnr.json` `NEXTPNR_BEL`),
which both flows share because they are driven by the same `.cst`. `it never leaves a
used pin's IO_TYPE / bank VCCIO unset`: **HOLDS** -- 0 `unset_on_used`, `IO_TYPE` equal
on 117/117 used inputs and 143/143 used outputs, `BANK_VCCIO` equal on 71/71 used banks
and 209/209 unused.

## Fuse classes found, per pin state (after `D108`)

Site-observations summed over the 35 designs. `equal` = both sides decode the attribute
to the same value; `open_only`/`vendor_only` = only that side sets it; `decode_alias` =
only the open side decodes it, but its bits at that site are a subset of the vendor's,
so no fuse was invented.

### unused pin (~316 IOB halves per design)

| attribute | equal | open_only | vendor_only | decode_alias |
|---|---|---|---|---|
| `IO_TYPE` | 11 045 | 0 | 35 | 0 |
| `OPENDRAIN` | 11 045 | 0 | 35 | 0 |
| `PADDI` | 11 045 | 0 | 35 | 0 |
| `PULLMODE` | 930 | **0** | 4 | 0 |
| `DRIVE` | 0 | **0** | 70 | 0 |
| `DRIVE_LEVEL` | 0 | **0** | 70 | 0 |
| `ODMUX_1` | 35 | 0 | 35 | 0 |
| `HYSTERESIS` | 0 | 0 | 3 | 0 |
| `IOB_UNKNOWN51` | 0 | 0 | 1 | 0 |
| `LVDS_OUT` | 11 010 | 0 | 0 | 35 |

### used input (117 sites) / used output (143 sites) / diff pair / banks

`IO_TYPE`, `LVDS_OUT`, `OPENDRAIN`, `PADDI` equal on all 117 used inputs; `HYSTERESIS`
equal on 114, `open_only` on 3 (all `ae350-e0`); `PULLMODE` equal on 91, `open_only` on
1 (`ae350-e0`). On the 143 used outputs, `IO_TYPE`/`OPENDRAIN`/`PADDI` equal on all 143;
`DRIVE`, `DRIVE_LEVEL`, `ODMUX_1`, `IOB_UNKNOWN51`, `PULLMODE` equal on 141-142 and
`open_only` on exactly 1 (the `ae350-e0` skew); **`SLEWRATE` appears on neither side.**
No differential IO is placed in any of the 35 designs (`P3.T23`-`P3.T25` own it:
`evidence/tlvds`, `evidence/elvds`).

| state | attribute | equal | open_only | vendor_only |
|---|---|---|---|---|
| used bank | `BANK_VCCIO` | 71 | 0 | 0 |
| used bank | `PULL_STRENGTH` | 70 | 1 | 0 |
| used bank | `LVDS_OUT` | 70 | 1 | 0 |
| unused bank | `BANK_VCCIO` | 209 | 0 | 0 |
| unused bank | `PULL_STRENGTH` | 0 | 0 | 2 |
| unused bank | `LVDS_OUT` | 0 | 0 | 2 |

PR #423's own fuse is **correct on this device**: `PULL_STRENGTH=MEDIUM` and
`BANK_VCCIO` match the vendor bit for bit on every used bank. The `ae350-e0`
observations are the skew, named not folded in.

## What `P3.T26` corrected, and which is still true

`P0.T33` settled the `io_default_unused_pins` residual as "631 bits are `gowin_pack`'s
unused-IO `IO_TYPE`/`BANK_VCCIO` defaults ... no `DRIVE`/`PULLMODE`, so **NOT** the PR
#423 class". Measured on the same `big-shift` baseline, **610 of those bits were
`DRIVE`/`DRIVE_LEVEL`** and `IO_TYPE` contributed zero, so that mask entry had been
masking a drive default on every floating pin of the die. After `D108` `big-shift`
carries **0** such bits.

## Files and guards

`iob-safety.json` (raw result), `runs.jsonl` (35 rows). Drivers:
`derive_iob_safety_138c.py`, `repack_open_fs.py`. Tests: `test_iob_safety_138c.py` (9),
`test_repack_open_fs.py` (5), `apicula tests/test_iob_defaults_138c.py` (9),
`test_iob_bank_defaults_138c.py` (5 -- its strict `xfail` for the drive default is now
an ordinary assertion).

## Inherited-input `W-IO` (`gestalt-p2` `D1`) -- still open

"Does a design that actually drives a released SSPI pin as a GPIO get the right IOB
configuration through the ordinary IO path?" Not from this corpus: no design in it
drives a released SSPI pin as a GPIO, so the 20 `sspi` bits at `(166,108)`/`(167,108)`
are unobserved here. What this row now settles is that the ordinary IO path is clean
where it can be observed -- the prior cause `P3.T26` gave `W-IO` is gone.
