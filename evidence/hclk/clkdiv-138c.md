# nextpnr places CLKDIV / CLKDIV2 on the GW5AST-138C — P1.T11

apicula `clocking/gw5a-hclk-6block` `570d399`; nextpnr `clocking/gw5a-hclk-6block`
`8566c51` (T10, constids HCLK40-53); chipdb `.bin` `72e6ff4a…` (P1.T08b).
Rows: `evidence/hclk/runs.jsonl` (`hclk-clkdiv-0001`, `hclk-clkdiv2-0001`).

## 1. Placement — PROVEN

`nextpnr-himbaechel --no-route`, exit **0** in every case. Bel from the
written JSON's `NEXTPNR_BEL`; the block is the measured `_gw5a_hclk_locs`
entry, not an inference.

| Design | Cell | Bel | Tile (row, col) | HCLK block |
|---|---|---|---|---|
| `clkdiv_chain-tangmega138k.v` | `CLKDIV div2` | `X64Y108/CLKDIV_1` | (108, 64) | **4** |
| same, `(* BEL = "X117Y108/CLKDIV_2" *)` | `CLKDIV div2` | `X117Y108/CLKDIV_2` | (108, 117) | **5** |
| `clkdiv2_chain-tangmega138k.v` | `CLKDIV2 div2` | `X64Y108/CLKDIV2_0` | (108, 64) | **4** |
| `clkdiv2_chain-tangmega138k.v` | `CLKDIV div` | `X64Y108/CLKDIV_0` | (108, 64) | **4** |

Log lines, verbatim:

```
Info: 	              CLKDIV:       1/     24     4%
Info: 	             CLKDIV2:       1/     24     4%
Info: Placed 1 cells based on constraints.        # the block-5 run only
```

The unconstrained placer picks block 4 on its own, and the constrained run
proves block 5 is a real target — the two blocks that had 26 nodes and no
fuse before P1.T08b.

Guarded by `tests/test_gw5ast138c_clocking.py`:
`test_nextpnr_places_clkdiv_138c`, `test_nextpnr_places_clkdiv_138c_in_block_5`,
`test_nextpnr_places_clkdiv2_138c` (all `heavy`; they run the real yosys and
the installed nextpnr).

## 2. Routing — ABORTED, with the cause measured

Full place-and-route exits **125** on both designs:

```
Warning: Failed to route net 'div_clk' from X64Y108/CLKDIV_O41 to X93Y107/CLK1 using dedicated routing.
   ... 24 such warnings ...
Warning: Failed to find a route for arc 23 of net div_clk.     # clkdiv
Warning: Failed to find a route for arc 6 of net div_clk.      # clkdiv2
ERROR: Routing design failed.
```

Cause, measured from the `.fse` and the name tables, not guessed:
`gw5_make_hclk_to_clk_gates` builds every HCLK→global-clock gate pip by
scanning the grid for `clock_pips` entries named `{T,B,R,L}BDHCLK{0..3}`.
`clknames_5ast138c` defines **0 of those 16 names**; `clknames_5a25a` defines
all 16. So on the 138C the function is a no-op, no HCLK→GCLK gate pip exists,
and a CLKDIV output has no path onto a global spine. (Its `spec_ttyp` table is
also 25A-literal, but that never gets reached.) This is `port-138c.md`
FINDING 3 made concrete, and it is the next piece of the S10/S12 seam — it
needs the 138C's own BDHCLK naming, which nobody has measured.

## 3. Vendor oracle (1 run charged)

`fuzz.gw5ast138c.harness.oracle --design-dir …/p1t11/clkdiv
--extra-option "-use_sspi_as_gpio 1"`, GOWINHOME Standard 1.9.12.03:
`PREFLIGHT run ok=True returncode=0 reason=ok`.

- `run.fs` 34,668,941 B `3d36f0aa63b6f2b48fabe9b3ac153bfffe15ab012b158022836ea7ab32b5ac5a`
- `run.sdf` 41,622 B `5157bd8d…`, `run.tr` 175,231 B `db01f722…`
- vendor utilisation: `CLKDIV | 1/24 | 5%`

Two `.cst` facts fell out and are worth carrying forward: the checked-in
`examples/gw5a/tangmega138k.cst` omits `IO_TYPE` on `clk` and `reset`, which
the harness's own D20 `.cst` assertion rejects (the run copy adds
`IO_TYPE=LVCMOS33`, banks 4 and 5, not the PR #423 bank-6/7 class); and its
LED pins P19/R19/U21 are SSPI-dedicated, so the vendor needs
`-use_sspi_as_gpio 1` on top of the harness's standard `-use_cpu_as_gpio 1`.

## 4. E0 — NOT COMPUTED, and why

**DIFF_COUNT n/a. RESIDUAL n/a.** There is no number to paste, and inventing
a scope where the answer is trivially "identical" would be worse than saying
so. Two independent reasons, each on its own sufficient:

1. **The open side has no `.fs`.** Routing aborts (§2), so `gowin_pack` has no
   routed netlist. Packing the `--no-route` JSON instead aborts with
   `AttributeError: 'GW5AST_138C' object has no attribute
   'get_BLOCKER_LUT_fuses'` — nextpnr's routing-blocker cells, which a routed
   design would not contain.
2. **Even with two `.fs`, an HCLK-scoped E0 would be vacuous.** Unpacking the
   *vendor* bitstream with apicula (`equiv.unpack_netlist`) yields 138,600
   cells of exactly four types — DFF 138,240, IOB 324, LUT 28, BANK 8 — and
   **no CLKDIV cell at any tile**. `gowin_unpack` has no CLKDIV decoder for
   this device, so the cell set inside the HCLK tile is empty on the vendor
   side by construction and `compare_e0` would report `cells=0 attrs=0
   conns=0` for a design whose whole subject is a CLKDIV.

A real E0 on this primitive therefore needs, in order: the HCLK→GCLK gate
naming (§2) so the open flow routes, and a CLKDIV unpacker so the vendor side
has a cell to compare. Both are measurements, both are outside P1.T11.

## 5. Artefacts

`$DATASTORE/batch/p1t11/{clkdiv,clkdiv-b5,clkdiv2}/` — `top.v`, `top.cst`,
`top.sdc`, `yosys.log`, `nextpnr.log`, `nextpnr-noroute.log`,
`top_pnr_placed.json`, and for `clkdiv/` the vendor `run/` tree and
`gw_sh.log`.
