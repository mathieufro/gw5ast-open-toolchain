# IO bank coercion on GW5AST-138C (`P3.T27`, upstream apicula PR #535)

## Verdict: **`E0+hw-pending`** — the defect is reproduced and fixed; the bitstream-level confirmation is named and owed

0 vendor runs. 1 evidence row, `p3-t27-bank-coercion-0000`, `verdict: ok`,
`level: E0`, decode checks `n/a` (see "What was *not* measured").

## The defect

A bank that holds a true-LVDS output pair records an LVDS bank-wide `IO_TYPE`
in its `BankDesc`. `Device.process_IBUF` then applied that bank-wide type to
**every** plain single-ended `IBUF` in the bank, unconditionally — so an
ordinary 3.3 V input that merely shared a bank with an LVDS pair was packed as
LVDS. Upstream apicula PR #535 is the same defect on a different device.

## The fix, stated as a rule rather than a patch

An `IBUF` adopts the bank-wide standard **only when the bank has an ordinary
(non-LVDS) output**. An input-only bank leaves each `IBUF` on its own
`IO_TYPE`, or on the device default when it declares none.

`GW5AST-138C` inherits `Device.process_IBUF` and `Device.check_io_banks`
unmodified, and `GW5A_25A` keeps its own separate override, untouched — so the
fix reaches this die without editing a path `S3` freezes.

## How it was measured, at 0 vendor runs

| check | result |
|---|---|
| mixed-bank case against the **pre-fix** `process_IBUF` | fails (the IBUF is coerced to LVDS) |
| the same case against the **fixed** `process_IBUF` | passes (the IBUF keeps `LVCMOS33`) |
| single-type bank's `IO_TYPE` fuse | unchanged — a guard, so the fix is not a widening |
| explicit per-pin `IO_TYPE` conflict | still refused by name (`BankDesc.check_or_set_attr`) |
| `GW5A-25A` chipdb and packer defaults | unchanged (`S3`, `tests/test_family_regression_gw5a.py`) |

`apicula tests/test_bank_coercion_138c.py` — 6 tests, all pass, exercising
`BankDesc` / `process_IBUF` / `check_io_banks` against a stubbed chipdb. The
fail-then-pass pair is the measurement: an assertion that passes against both
handlers would prove nothing about the defect.

## What was *not* measured, and what `hw-pending` owes

No bitstream on this board exercises the case. The die's only `TRUELVDS` pair
is `J14`/`H14` (`IOR103A`/`B`), and no design in this phase's corpus places a
single-ended `IBUF` in that pair's bank — so there is no vendor bitstream to
diff, the row closes on the packer rather than on a bitstream, and the two
decode checks are `n/a` rather than run.

**The Hardware Gate (`P9`) owes exactly one observation**: build a bank plan
that mixes the `J14`/`H14` TLVDS pair with single-ended inputs in the same
bank, and read the unpacked `IO_TYPE` of those inputs back as `LVCMOS33` and
not LVDS. One vendor run, or none if `P9` folds it into a design it is
building anyway.
