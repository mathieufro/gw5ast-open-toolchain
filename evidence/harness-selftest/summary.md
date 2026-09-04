# P0.T29 — harness self-tests and the unpacker-completeness fix

Design under test: `$DATASTORE/oracle-smoke` (shape `smoke`, primitive DFF).
Vendor side rebuilt 2026-09-04 (`run.fs` 34,668,941 B, `BATCH_COMPLETE
t29-vendor runs=1 ok=1`), open side `top.fs` 34,668,145 B from P0.T21.

## Self-tests (`spec-harness.md` §9, `spec.md` S5/S6b) — `selftest-smoke.txt`

```
COMPLETENESS ok: 0 unattributed tiles, 0 missing cells
SELFTEST ok: 1 difference reported, 0 spurious
```
exit status 0. 763 tiles of the open bitstream carry set fuses; all 763 are
attributed to a decoded bel or pip. The injected fuse is the first clear
single-bit LUT flag of a decoded LUT (deterministic), and the checker reports
it as exactly one attribute difference.

## Unpacker fix (apicula 727047d) — two GW1N-shaped decode rules

1. `RAM16`'s shadow-SRAM mode is built from the `fse` `shortval(28)` record
   keyed `(2,0)`, absent on every GW5A slice tile type, so its fuse set was
   empty and matched **every** cleared tile: a `RAM16` was decoded in all
   16,200+ slice tiles and `ram16_remove_bels()` deleted `LUT0`-`LUT5` and
   `DFF4`/`DFF5` from each. GW1N-9C and GW2A-18C carry one real fuse there.
2. In all 24 GW5AST-138C IOB tables the positive `LVDS_OUT=ON` record's fuse
   set equals the fuse set of the default (negative-key) records a plain input
   buffer sets (`-ODMUX=TRIMUX, OPENDRAIN=OFF, PADDI=PADDI`, bits (20,51) and
   (20,79) at tile (55,108)), so every used input decoded as `TLVDS_IBUF` and
   its paired `IOBB` was dropped. No IOB table of GW1N-1, GW1N-9C, GW1NZ-1,
   GW1NS-4 or GW2A-18C has that property, and the guard tests the table, not
   the device name.

## Decode check and E1 after the fix — `equiv-e1-after-fix.txt`

```
DECODE_CHECK c1=ok c2=ok (c1 recovered 13/13 placed cells, 6 not fuse-backed;
                          c2 0 differing bytes of 4147478)
DIFF_COUNT cells=3 attrs=36 conns=40
RESIDUAL_UNEXPLAINED entries=3 bits=15422 bytes=162
E1 placement level=E1 constrained=1 matched=1 mismatched=0 unobserved=0
```

`c1` was `mismatch` (9/13) before the fix. The verdict is still `DIFF`, for two
reasons that are **not** unpacker blind spots:

- the three open-side passthrough LUTs at tile (2,1) nextpnr inserts and the
  vendor does not (the P0.T26 packing difference, T33's subject). They were
  partly hidden before: the spurious `RAM16` removed them from the open side
  too, so the decode looked cleaner than it was.
- `unmodelled_fuse` 14,935 bits over 231 tiles: tiles where both sides unpack
  the *same* cells and attributes and the raw bits still differ — fuses
  apicula models nowhere, dropped identically on both sides. This is the D35
  blind spot, enumerated, not masked. `unattributed_tile` 487 bits over 180
  tiles and 162 B of vendor-only preamble words are unchanged from P0.T25.
