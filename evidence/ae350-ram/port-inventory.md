PORTS 26

# AE350_RAM port inventory

Measured, not quoted. Source A: `/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA/IDE/bin/prim_syns/gw5a/primitive.xml`, the `<name>AE350_RAM</name>` module block.
Source B: the DDR3_Shared golden netlist `riscv_ae350_soc.vo` — **`AE350_RAM` does not appear in it**
(`grep -c AE350_RAM` = 0), so column `in_vo` is `no` for every port and `tied_to` is `n/a`.
The vendor reference design instantiates `AE350_SOC` alone and drives its `EXTM_*` AHB master
port out to fabric-side DDR3, never to an `AE350_RAM` slave.

| name | direction | width | in_xml | in_vo | tied_to | shared with AE350_SOC |
|---|---|---|---|---|---|---|
| POR_N | input | 1 | yes | no | n/a | yes |
| HW_RSTN | input | 1 | yes | no | n/a | yes |
| CORE_CLK | input | 1 | yes | no | n/a | yes |
| AHB_CLK | input | 1 | yes | no | n/a | yes |
| APB_CLK | input | 1 | yes | no | n/a | yes |
| RTC_CLK | input | 1 | yes | no | n/a | yes |
| CORE_CE | input | 1 | yes | no | n/a | yes |
| AXI_CE | input | 1 | yes | no | n/a | yes |
| AHB_CE | input | 1 | yes | no | n/a | yes |
| EXTM_HADDR | input | 32 | yes | no | n/a | yes |
| EXTM_HBURST | input | 3 | yes | no | n/a | yes |
| EXTM_HPROT | input | 4 | yes | no | n/a | yes |
| EXTM_HREADY | input | 1 | yes | no | n/a | yes |
| EXTM_HSEL | input | 1 | yes | no | n/a | yes |
| EXTM_HSIZE | input | 3 | yes | no | n/a | yes |
| EXTM_HTRANS | input | 2 | yes | no | n/a | yes |
| EXTM_HWDATA | input | 64 | yes | no | n/a | yes |
| EXTM_HWRITE | input | 1 | yes | no | n/a | yes |
| EMA | input | 3 | yes | no | n/a | yes |
| EMAW | input | 2 | yes | no | n/a | yes |
| EMAS | input | 1 | yes | no | n/a | yes |
| RET1N | input | 1 | yes | no | n/a | yes |
| RET2N | input | 1 | yes | no | n/a | yes |
| EXTM_HRDATA | output | 64 | yes | no | n/a | yes |
| EXTM_HREADYOUT | output | 1 | yes | no | n/a | yes |
| EXTM_HRESP | output | 1 | yes | no | n/a | yes |

## Totals

- ports: **26** (23 input, 3 output, 0 inout)
- parameters: **0** — the search space is empty, so this row is wire discovery, not a sweep
- fabric bits: **194** total (128 in, 66 out)

## Names shared with `AE350_SOC`

Shared names matter because `create_reuse_wire` (`gowin_arch_gen.py:516-523`) reuses the wire
when both bels land in one tile, so a shared name must resolve to the same `(r, c, wire)` triple
or the two bels silently fight over it.

26 of 26 names are shared: `POR_N`, `HW_RSTN`, `CORE_CLK`, `AHB_CLK`, `APB_CLK`, `RTC_CLK`, `CORE_CE`, `AXI_CE`, `AHB_CE`, `EXTM_HADDR`, `EXTM_HBURST`, `EXTM_HPROT`, `EXTM_HREADY`, `EXTM_HSEL`, `EXTM_HSIZE`, `EXTM_HTRANS`, `EXTM_HWDATA`, `EXTM_HWRITE`, `EMA`, `EMAW`, `EMAS`, `RET1N`, `RET2N`, `EXTM_HRDATA`, `EXTM_HREADYOUT`, `EXTM_HRESP`

Not shared: none — `AE350_RAM` is an **exact subset** of `AE350_SOC`'s 149 ports: every one of
the 26 names matches on direction *and* width (measured, 0 mismatches). `EXTM_*` is a slave
(AHB-target) view on both primitives, so the two bels cannot be distinguished by port shape and
`create_reuse_wire` will collapse all 26 wires if they share a tile. The chipdb must therefore
either place `AE350_RAM` in a different tile from `AE350_SOC` or treat the reuse as intended;
`P2.T09`/`P2.T25` measure which.

## DISCREPANCIES

None between sources in the sense of `P2.T02`: source B contains no `AE350_RAM` instance at all,
so there is nothing to disagree with. Recorded as an absence, not a discrepancy.
