# `parse_pll` — the marker file (`P1.T33`, blueprint path)

The full measurement, the `.tm` dump, the datasheet comparison and the `V12a`
stdout are in `../timing-l0-cfu/pll-slice.md`. This file carries the marker the
blueprint names.

`NO-DATA: the GW5AST-138C .tm publishes no PLL timing group. Each parsed chunk
is 15552 bytes and only chunks 0, 1, 2 are parsed at all — `tm_parser.py:344`
breaks on `if i >= 3 and device in {…'GW5AST-138C'}` — and at offset 0x7cc each
carries an 80-byte, five-path block that is byte-identical to `GW2A-18.tm`'s and
names five rPLL outputs (CLKOUT/LOCK/CLKOUTP/CLKOUTD/CLKOUTD3) this die does not
have. UG306E Table 5-2 gives the Arora-V PLL CLKOUT0..6/CLKFBOUT/LOCK, DS1239E
Table 3-18 publishes no CLKIN→CLKOUT delay, and the vendor SDF for a 138C PLL
design emits all seven CLKIN→CLKOUTn IOPATHs as 0.000 — so the PLL slice of the
L0 band is "no arcs by design", asserted as 7/7 rather than skipped.`
