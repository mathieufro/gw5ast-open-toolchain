# D26 calibration — ASSUMED vs MEASURED (P0.T34)

Full detail, derivations and deviations: `measured-budget.md` in this same directory
(T33's own `summary.md` here is a different task/deliverable — the `S6` checker
calibration — and is untouched by this file).

| Quantity | ASSUMED | MEASURED |
|---|---|---|
| `gw_sh run all`, minimal 138K design | ≤ 10 min | 23.144 s |
| `gw_sh run all`, largest available (`attosoc-tangmega138k`) | ≤ 45 min | 26.834 s |
| chipdb build, `GW5AST-138C` | ≤ 30 min | 33.071 s |
| yosys synth, one stand-in | ≤ 5 min | 5.064 s |
| nextpnr PnR, one stand-in on 138K | ≤ 20 min | 13.273 s |
| Parallelism (concurrent oracle pipelines) | 1 | ≥ 2 (both succeed, Standard licence) |

`measured_per_run_total` = 41.481 s; `batch_runs` (parallelism = 1) = **867**;
`batch_runs` (parallelism = 2) = 1735. No quantity overran its ASSUMED budget by more
than 2x (see `measured-budget.md` for the per-row ratios and the overrun-rule
self-check).
