# The AE350's core clock and DDR clock, measured (`P2.T38`)

`spec-primitives.md` §5 step (3) asks for the PLL placement to be *varied* and
the two routes *measured*. MUG1031 L1753-1759 and the shipped `.cst` say the
core clock comes from `PLL_R[0]`; that is now corroboration, not the source.

Two vendor runs, both `ok`, both on the `ae350_soc` shape with one line
overridden per run and the shape file itself untouched:

| batch | what differs from the `P2.T23` row | vendor verdict |
|---|---|---|
| `p2t38-pll-l` | `INS_LOC "u_pll" PLL_L[0]` in place of `PLL_R[0]` | built, PLL realised at `PLL_L[0]` |
| `p2t38-ddr-clk` | `AE350_SOC.DDR_CLK` driven by the PLL's `CLKOUT0` instead of the ripple divider | built, PLL back at `PLL_R[0]` |

## 1. The core clock is not `PLL_R[0]`-exclusive

Outcome (iii) of the three the blueprint admits. The vendor placed the PLL
where it was asked and took the core clock straight out of it:

```
  68.107   6.569   tCL   RR  1   PLL_L[0]   u_pll/CLKOUT1
  68.107   0.000   tNET  RR  1   R0C160     u_ae350/CORE_CLK
```

The `tNET` delay is **0.000 ns** — the same dedicated, zero-delay hop the
`PLL_R[0]` run shows at the same two lines (`p2t23-ae350-row2`, `run.tr:265`).
So the dedicated route exists from *both* PLL sites, and `PLL_R[0]` is a
convention of the reference design, not a property of the silicon.

CORE-CLK-ROUTE: PLL_L[0] also legal

**What the model owes.** Nothing was changed in `chipdb.py`, because there is
no exclusive `PLL_R[0]` edge in it to correct: the chipdb models one *fabric*
tap per clock port (`extra_func[(0, 159)]['ae350']['ins']['CORE_CLK']` =
`AE350_SOCCORE_CLKCLK1`) and no PLL edge at all, and `P2.T23` measured that
the vendor never uses that tap. The model is silent here, not wrong, and the
gap it owes — one dedicated edge **per PLL site**, not one — belongs to
`P2.T10`. `tests/test_core_clk_route.py::test_core_clk_model_matches_measurement`
fails the moment anyone models it as `PLL_R[0]`-only.

## 2. The DDR clock takes the ordinary clock network

Driven from the same PLL's second output, the DDR clock is routed like any
other clock — 2.091 ns over a net with fanout 110, not the core clock's
zero-delay hop:

```
 105.022   6.561   tCL   RR  2    PLL_R[0]   u_pll/CLKOUT0
 107.113   2.091   tNET  RR  110  R0C160     u_ae350/DDR_CLK
```

DDR-CLK-ROUTE: PLL_R[0].CLKOUT0 -> DDR_CLK

So the asymmetry is real and measured: **one** AE350 clock input has a
dedicated route, and it is the core clock. The shipped reference's second PLL
(`INS_LOC "u_Gowin_PLL_DDR3/PLL_inst" PLL_L[0]`) is a placement choice for the
DDR3 PHY's own clocking, not evidence of a dedicated DDR_CLK edge.

## 3. Ledger

Both runs come out of the `ae350` slug's remaining two: cumulative 8 of 8.
