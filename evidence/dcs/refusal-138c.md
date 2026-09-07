# The 138C DCS closes as a named refusal

`P1.T38` second pass, 2026-09-07. This supersedes the `E0` close recorded in
`summary.md` `## P1.F2`. Nothing measured is withdrawn; what changes is what
the measurement is read to prove.

## What happened

`P1.F2` and `P1.F4` landed on `epic/gw5ast138c` in that order, and they
contradict each other:

* `P1.F2` closed the DCS at `E0` on three sweep points (`q1`, `q2`, `sel4`),
  each `EQUIV E0 ok`, `DIFF_COUNT cells=0 attrs=0 conns=0`, `c1`/`c2` ok.
* `P1.F4` added `gowin_pack.reject_untraced_dcs_control` (`C4#2`): a design
  that drives `SELFORCE` or any `CLKSEL[0..3]` on a die whose DCS control
  wires have never been traced is **refused by name** rather than packed with
  a fuse taken from the pre-5A wire model (`D30`).

Every one of the three sweep points drives `CLKSEL` and `SELFORCE` — the
`clocking_dcs` shape wires them to design inputs, and a DCS that does not
select is not doing anything. So `P1.F4` refuses exactly the designs `P1.F2`
closed, and the `E0 ok` rows are **not reproducible on the pair this phase
lands on**.

## The re-run, on the landing pair

```
BATCH_COMPLETE p1t38c-dcs runs=3 ok=0 diff=0 aborted=3
BATCH_SKIPPED  batch=p1t38c-dcs n=0 refused=3
```

(`aborted=3` in the `BATCH_COMPLETE` marker is the marker's fixed four-field
schema, `spec-harness.md` §8: it has no `refused` field and rolls refusals in.
`BATCH_SKIPPED`'s `refused=3` and the rows' own `verdict` are the truth.)

All three rows, in `runs.jsonl`, carry `verdict: "refused"` and the packer's
exact words:

> DCS CLKSEL0, CLKSEL1, CLKSEL2, CLKSEL3, SELFORCE is driven on a device whose
> DCS control wires have never been traced: the wire names come from the
> pre-5A model, so the route into them is not the route this die uses.
> Refusing rather than emitting an unverified fuse (P1.T31).

The vendor half of each run completed and left its `.fs`
(`run/impl/pnr/run.fs`, ~13 s per run) — the oracle artefact `D30` requires
beside a refusal, showing the vendor compiles the same design.

Pair: `nextpnr-himbaechel` `f029437e…`, `chipdb-GW5AST-138C.bin` `0206b922…`,
`apycula/GW5AST-138C.msgpack.xz` `315c02d8…`.

## Which of the two is right, and why

**The refusal.** `E0` and `E1` compare cells, attributes and connectivity
after the don't-care mask; `D32` makes routing never a verdict term. The
`CLKSEL`/`SELFORCE` routing lives entirely in pip fuses. So the equivalence
check was structurally incapable of seeing the one thing that is unverified:
the `E0 ok` verdicts were true statements about the ladder and silent about
whether the bitstream selects anything on hardware.

Weakening the guard to make the row close would be the exact failure `D30`
exists to prevent — a plausible-looking bitstream with no error. The guard
stays; the row's status becomes what it honestly is,
`refused:<named error>` (`A12`), and DONE-STD clauses (b) and (d) do not apply
to it (`spec-primitives.md` §"DONE-STD"). Its required unit tests are
`tests/test_gw5ast138c_dcs_control_wires.py` (5) and
`tests/test_pack_refusal_is_a_verdict.py` (4).

## What is still true, and what closes this row for good

Still true and still landed, none of it withdrawn:

* the 138C has **4 DCS in 2 quadrants**, at (54, 93) `P26*`/`P27*` and
  (54, 88) `P36*`/`P37*` (`ports-138c.md`);
* the **output** side: `dcs_clkout_node` joins a DCS output to
  `CBRIDGEOUT_<half><n>`, and the spine permission set is derived from the
  database rather than hardcoded;
* the **input** side: `get_logic_clock_ins` returns the 24 gates per half the
  `.dat` `CMuxTopIns`/`CMuxBotIns` tables give, and the central multiplexer's
  unsuffixed gate name is MEASURED onto `CMuxBotIns` (`input-side-138c.md`).

What would close the row at `E0`/`E1` is one thing: a vendor bitstream that
routes an external net into a bridge cell's `SELFORCE`/`CLKSEL` inputs, so the
wires can be traced instead of guessed. `input-side-138c.md` §6 names the
campaign; the `PCLK*` half of the input multiplexer is the same shape of gap
and is closed by the same kind of run.
