# `AE350_SOC` bus-slicing plan — and the `EC5` routing decision

`P2.T06`. Frozen input to `P2.T08` (port map) and work order for `P2.T37` (`EC5` discovery).

## The decision, and why it is not a slicing plan

The `EMCU` method this task was written to imitate slices live `(r, c, wire)` triples out of
`dat.compat_dict['EMcuIns'/'EMcuOuts']` (`chipdb.py:3903-3945`). That method **cannot be applied
on `GW5AST-138C`**, because the device `.dat` carries no live entries to slice. Measured with the
frozen `dat_parser.Datfile` against
`$GOWINHOME/IDE/share/device/GW5AST-138C/GW5AST-138C.dat`:

| table | entries | live (`r >= 0 and c >= 0`) |
|---|---|---|
| `McuIns` | 265 | **0** |
| `McuOuts` | 372 | **0** |
| `EMcuIns` | 270 | **0** |
| `EMcuOuts` | 319 | **0** |

Every hard-block triple table in the 138C `.dat` is all-sentinel — `UfbIns/Outs`, `AdcIns/Outs`,
`Usb2PhyIns/Outs`, `Eflash128kIns/Outs`, `SpmiIns/Outs`, `I3cIns/Outs` and the four above, 16 tables,
0 live entries between them. The parser is not at fault: the same frozen parser reads
`GW1NS-4.dat` and returns **224** live `EMcuIns` and **302** live `EMcuOuts` triples, which is the
control that proves the offsets and the signed-16-bit decode are right. So the emptiness is a
property of the 138C device file, not of `dat_parser.py`, and no `.dat` slice exists to propose.

**Decision: every bus routes to `EC5` differential discovery; zero buses route to a table slice.**

## Plan

| bus | width | source | wire_type |
|---|---|---|---|
| POR_N | 1 | EC5-discovery | AE350_IN |
| HW_RSTN | 1 | EC5-discovery | AE350_IN |
| CORE_CLK | 1 | EC5-discovery | TILE_CLK |
| DDR_CLK | 1 | EC5-discovery | TILE_CLK |
| AHB_CLK | 1 | EC5-discovery | TILE_CLK |
| APB_CLK | 1 | EC5-discovery | TILE_CLK |
| DBG_TCK | 1 | EC5-discovery | TILE_CLK |
| RTC_CLK | 1 | EC5-discovery | TILE_CLK |
| CORE_CE | 1 | EC5-discovery | AE350_IN |
| AXI_CE | 1 | EC5-discovery | AE350_IN |
| DDR_CE | 1 | EC5-discovery | AE350_IN |
| AHB_CE | 1 | EC5-discovery | AE350_IN |
| APB_CE | 8 | EC5-discovery | AE350_IN |
| APB2AHB_CE | 1 | EC5-discovery | AE350_IN |
| SCAN_TEST | 1 | EC5-discovery | AE350_IN |
| SCAN_EN | 1 | EC5-discovery | AE350_IN |
| GP_INT | 16 | EC5-discovery | AE350_IN |
| DMA_REQ | 8 | EC5-discovery | AE350_IN |
| WAKEUP_IN | 1 | EC5-discovery | AE350_IN |
| TEST_CLK | 1 | EC5-discovery | AE350_IN |
| TEST_MODE | 1 | EC5-discovery | AE350_IN |
| TEST_RSTN | 1 | EC5-discovery | AE350_IN |
| ROM_HRDATA | 32 | EC5-discovery | AE350_IN |
| ROM_HREADY | 1 | EC5-discovery | AE350_IN |
| ROM_HRESP | 1 | EC5-discovery | AE350_IN |
| APB_PRDATA | 32 | EC5-discovery | AE350_IN |
| APB_PREADY | 1 | EC5-discovery | AE350_IN |
| APB_PSLVERR | 1 | EC5-discovery | AE350_IN |
| EXTS_HRDATA | 32 | EC5-discovery | AE350_IN |
| EXTS_HREADYIN | 1 | EC5-discovery | AE350_IN |
| EXTS_HRESP | 1 | EC5-discovery | AE350_IN |
| EXTM_HADDR | 32 | EC5-discovery | AE350_IN |
| EXTM_HBURST | 3 | EC5-discovery | AE350_IN |
| EXTM_HPROT | 4 | EC5-discovery | AE350_IN |
| EXTM_HREADY | 1 | EC5-discovery | AE350_IN |
| EXTM_HSEL | 1 | EC5-discovery | AE350_IN |
| EXTM_HSIZE | 3 | EC5-discovery | AE350_IN |
| EXTM_HTRANS | 2 | EC5-discovery | AE350_IN |
| EXTM_HWDATA | 64 | EC5-discovery | AE350_IN |
| EXTM_HWRITE | 1 | EC5-discovery | AE350_IN |
| DDR_HRDATA | 64 | EC5-discovery | AE350_IN |
| DDR_HREADY | 1 | EC5-discovery | AE350_IN |
| DDR_HRESP | 1 | EC5-discovery | AE350_IN |
| TMS_IN | 1 | EC5-discovery | AE350_IN |
| TRST_IN | 1 | EC5-discovery | AE350_IN |
| TDI_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_HOLDN_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_WPN_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_CLK_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_CSN_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_MISO_IN | 1 | EC5-discovery | AE350_IN |
| SPI2_MOSI_IN | 1 | EC5-discovery | AE350_IN |
| I2C_SCL_IN | 1 | EC5-discovery | AE350_IN |
| I2C_SDA_IN | 1 | EC5-discovery | AE350_IN |
| UART1_RXD | 1 | EC5-discovery | AE350_IN |
| UART1_CTSN | 1 | EC5-discovery | AE350_IN |
| UART1_DSRN | 1 | EC5-discovery | AE350_IN |
| UART1_DCDN | 1 | EC5-discovery | AE350_IN |
| UART1_RIN | 1 | EC5-discovery | AE350_IN |
| UART2_RXD | 1 | EC5-discovery | AE350_IN |
| UART2_CTSN | 1 | EC5-discovery | AE350_IN |
| UART2_DCDN | 1 | EC5-discovery | AE350_IN |
| UART2_DSRN | 1 | EC5-discovery | AE350_IN |
| UART2_RIN | 1 | EC5-discovery | AE350_IN |
| GPIO_IN | 32 | EC5-discovery | AE350_IN |
| DMA_ACK | 8 | EC5-discovery | AE350_OUT |
| SCAN_IN | 20 | EC5-discovery | AE350_IN |
| INTEG_TCK | 1 | EC5-discovery | AE350_IN |
| INTEG_TDI | 1 | EC5-discovery | AE350_IN |
| INTEG_TMS | 1 | EC5-discovery | AE350_IN |
| INTEG_TRST | 1 | EC5-discovery | AE350_IN |
| PGEN_CHAIN_I | 1 | EC5-discovery | AE350_IN |
| EMA | 3 | EC5-discovery | AE350_IN |
| EMAW | 2 | EC5-discovery | AE350_IN |
| EMAS | 1 | EC5-discovery | AE350_IN |
| RET1N | 1 | EC5-discovery | AE350_IN |
| RET2N | 1 | EC5-discovery | AE350_IN |
| PRESETN | 1 | EC5-discovery | AE350_OUT |
| HRESETN | 1 | EC5-discovery | AE350_OUT |
| DDR_RSTN | 1 | EC5-discovery | AE350_OUT |
| CORE0_WFI_MODE | 1 | EC5-discovery | AE350_OUT |
| RTC_WAKEUP | 1 | EC5-discovery | AE350_OUT |
| ROM_HADDR | 32 | EC5-discovery | AE350_OUT |
| ROM_HTRANS | 2 | EC5-discovery | AE350_OUT |
| ROM_HWRITE | 1 | EC5-discovery | AE350_OUT |
| APB_PADDR | 32 | EC5-discovery | AE350_OUT |
| APB_PENABLE | 1 | EC5-discovery | AE350_OUT |
| APB_PSEL | 1 | EC5-discovery | AE350_OUT |
| APB_PWDATA | 32 | EC5-discovery | AE350_OUT |
| APB_PWRITE | 1 | EC5-discovery | AE350_OUT |
| APB_PPROT | 3 | EC5-discovery | AE350_OUT |
| APB_PSTRB | 4 | EC5-discovery | AE350_OUT |
| EXTS_HADDR | 32 | EC5-discovery | AE350_OUT |
| EXTS_HBURST | 3 | EC5-discovery | AE350_OUT |
| EXTS_HPROT | 4 | EC5-discovery | AE350_OUT |
| EXTS_HSEL | 1 | EC5-discovery | AE350_OUT |
| EXTS_HSIZE | 3 | EC5-discovery | AE350_OUT |
| EXTS_HTRANS | 2 | EC5-discovery | AE350_OUT |
| EXTS_HWDATA | 32 | EC5-discovery | AE350_OUT |
| EXTS_HWRITE | 1 | EC5-discovery | AE350_OUT |
| EXTM_HRDATA | 64 | EC5-discovery | AE350_OUT |
| EXTM_HREADYOUT | 1 | EC5-discovery | AE350_OUT |
| EXTM_HRESP | 1 | EC5-discovery | AE350_OUT |
| DDR_HADDR | 32 | EC5-discovery | AE350_OUT |
| DDR_HBURST | 3 | EC5-discovery | AE350_OUT |
| DDR_HPROT | 4 | EC5-discovery | AE350_OUT |
| DDR_HSIZE | 3 | EC5-discovery | AE350_OUT |
| DDR_HTRANS | 2 | EC5-discovery | AE350_OUT |
| DDR_HWDATA | 64 | EC5-discovery | AE350_OUT |
| DDR_HWRITE | 1 | EC5-discovery | AE350_OUT |
| TDO_OUT | 1 | EC5-discovery | AE350_OUT |
| TDO_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_HOLDN_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_HOLDN_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_WPN_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_WPN_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_CLK_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_CLK_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_CSN_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_CSN_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_MISO_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_MISO_OE | 1 | EC5-discovery | AE350_OUT |
| SPI2_MOSI_OUT | 1 | EC5-discovery | AE350_OUT |
| SPI2_MOSI_OE | 1 | EC5-discovery | AE350_OUT |
| I2C_SCL | 1 | EC5-discovery | AE350_OUT |
| I2C_SDA | 1 | EC5-discovery | AE350_OUT |
| UART1_TXD | 1 | EC5-discovery | AE350_OUT |
| UART1_RTSN | 1 | EC5-discovery | AE350_OUT |
| UART1_DTRN | 1 | EC5-discovery | AE350_OUT |
| UART1_OUT1N | 1 | EC5-discovery | AE350_OUT |
| UART1_OUT2N | 1 | EC5-discovery | AE350_OUT |
| UART2_TXD | 1 | EC5-discovery | AE350_OUT |
| UART2_RTSN | 1 | EC5-discovery | AE350_OUT |
| UART2_DTRN | 1 | EC5-discovery | AE350_OUT |
| UART2_OUT1N | 1 | EC5-discovery | AE350_OUT |
| UART2_OUT2N | 1 | EC5-discovery | AE350_OUT |
| CH0_PWM | 1 | EC5-discovery | AE350_OUT |
| CH0_PWMOE | 1 | EC5-discovery | AE350_OUT |
| CH1_PWM | 1 | EC5-discovery | AE350_OUT |
| CH1_PWMOE | 1 | EC5-discovery | AE350_OUT |
| CH2_PWM | 1 | EC5-discovery | AE350_OUT |
| CH2_PWMOE | 1 | EC5-discovery | AE350_OUT |
| CH3_PWM | 1 | EC5-discovery | AE350_OUT |
| CH3_PWMOE | 1 | EC5-discovery | AE350_OUT |
| GPIO_OE | 32 | EC5-discovery | AE350_OUT |
| GPIO_OUT | 32 | EC5-discovery | AE350_OUT |
| INTEG_TDO | 1 | EC5-discovery | AE350_OUT |
| SCAN_OUT | 20 | EC5-discovery | AE350_OUT |
| PRDYN_CHAIN_O | 1 | EC5-discovery | AE350_OUT |

Buses: **149**. Bits: **911** — this is the `needed` count `P2.T04`'s
`RECONCILIATION-VERDICT` reports, measured from the same `primitive.xml` block. Covered by a table
slice: **0**.

Clocks carrying `TILE_CLK`: `CORE_CLK`, `DDR_CLK`, `AHB_CLK`, `APB_CLK`, `RTC_CLK`, `DBG_TCK` (6).

## EC5-DISCOVERY

Work order for `P2.T37`. One presence diff per uncovered bus.

| bus | bits | runs |
|---|---|---|
| POR_N | 1 | 1 |
| HW_RSTN | 1 | 1 |
| CORE_CLK | 1 | 1 |
| DDR_CLK | 1 | 1 |
| AHB_CLK | 1 | 1 |
| APB_CLK | 1 | 1 |
| DBG_TCK | 1 | 1 |
| RTC_CLK | 1 | 1 |
| CORE_CE | 1 | 1 |
| AXI_CE | 1 | 1 |
| DDR_CE | 1 | 1 |
| AHB_CE | 1 | 1 |
| APB_CE | 8 | 1 |
| APB2AHB_CE | 1 | 1 |
| SCAN_TEST | 1 | 1 |
| SCAN_EN | 1 | 1 |
| GP_INT | 16 | 1 |
| DMA_REQ | 8 | 1 |
| WAKEUP_IN | 1 | 1 |
| TEST_CLK | 1 | 1 |
| TEST_MODE | 1 | 1 |
| TEST_RSTN | 1 | 1 |
| ROM_HRDATA | 32 | 1 |
| ROM_HREADY | 1 | 1 |
| ROM_HRESP | 1 | 1 |
| APB_PRDATA | 32 | 1 |
| APB_PREADY | 1 | 1 |
| APB_PSLVERR | 1 | 1 |
| EXTS_HRDATA | 32 | 1 |
| EXTS_HREADYIN | 1 | 1 |
| EXTS_HRESP | 1 | 1 |
| EXTM_HADDR | 32 | 1 |
| EXTM_HBURST | 3 | 1 |
| EXTM_HPROT | 4 | 1 |
| EXTM_HREADY | 1 | 1 |
| EXTM_HSEL | 1 | 1 |
| EXTM_HSIZE | 3 | 1 |
| EXTM_HTRANS | 2 | 1 |
| EXTM_HWDATA | 64 | 1 |
| EXTM_HWRITE | 1 | 1 |
| DDR_HRDATA | 64 | 1 |
| DDR_HREADY | 1 | 1 |
| DDR_HRESP | 1 | 1 |
| TMS_IN | 1 | 1 |
| TRST_IN | 1 | 1 |
| TDI_IN | 1 | 1 |
| SPI2_HOLDN_IN | 1 | 1 |
| SPI2_WPN_IN | 1 | 1 |
| SPI2_CLK_IN | 1 | 1 |
| SPI2_CSN_IN | 1 | 1 |
| SPI2_MISO_IN | 1 | 1 |
| SPI2_MOSI_IN | 1 | 1 |
| I2C_SCL_IN | 1 | 1 |
| I2C_SDA_IN | 1 | 1 |
| UART1_RXD | 1 | 1 |
| UART1_CTSN | 1 | 1 |
| UART1_DSRN | 1 | 1 |
| UART1_DCDN | 1 | 1 |
| UART1_RIN | 1 | 1 |
| UART2_RXD | 1 | 1 |
| UART2_CTSN | 1 | 1 |
| UART2_DCDN | 1 | 1 |
| UART2_DSRN | 1 | 1 |
| UART2_RIN | 1 | 1 |
| GPIO_IN | 32 | 1 |
| DMA_ACK | 8 | 1 |
| SCAN_IN | 20 | 1 |
| INTEG_TCK | 1 | 1 |
| INTEG_TDI | 1 | 1 |
| INTEG_TMS | 1 | 1 |
| INTEG_TRST | 1 | 1 |
| PGEN_CHAIN_I | 1 | 1 |
| EMA | 3 | 1 |
| EMAW | 2 | 1 |
| EMAS | 1 | 1 |
| RET1N | 1 | 1 |
| RET2N | 1 | 1 |
| PRESETN | 1 | 1 |
| HRESETN | 1 | 1 |
| DDR_RSTN | 1 | 1 |
| CORE0_WFI_MODE | 1 | 1 |
| RTC_WAKEUP | 1 | 1 |
| ROM_HADDR | 32 | 1 |
| ROM_HTRANS | 2 | 1 |
| ROM_HWRITE | 1 | 1 |
| APB_PADDR | 32 | 1 |
| APB_PENABLE | 1 | 1 |
| APB_PSEL | 1 | 1 |
| APB_PWDATA | 32 | 1 |
| APB_PWRITE | 1 | 1 |
| APB_PPROT | 3 | 1 |
| APB_PSTRB | 4 | 1 |
| EXTS_HADDR | 32 | 1 |
| EXTS_HBURST | 3 | 1 |
| EXTS_HPROT | 4 | 1 |
| EXTS_HSEL | 1 | 1 |
| EXTS_HSIZE | 3 | 1 |
| EXTS_HTRANS | 2 | 1 |
| EXTS_HWDATA | 32 | 1 |
| EXTS_HWRITE | 1 | 1 |
| EXTM_HRDATA | 64 | 1 |
| EXTM_HREADYOUT | 1 | 1 |
| EXTM_HRESP | 1 | 1 |
| DDR_HADDR | 32 | 1 |
| DDR_HBURST | 3 | 1 |
| DDR_HPROT | 4 | 1 |
| DDR_HSIZE | 3 | 1 |
| DDR_HTRANS | 2 | 1 |
| DDR_HWDATA | 64 | 1 |
| DDR_HWRITE | 1 | 1 |
| TDO_OUT | 1 | 1 |
| TDO_OE | 1 | 1 |
| SPI2_HOLDN_OUT | 1 | 1 |
| SPI2_HOLDN_OE | 1 | 1 |
| SPI2_WPN_OUT | 1 | 1 |
| SPI2_WPN_OE | 1 | 1 |
| SPI2_CLK_OUT | 1 | 1 |
| SPI2_CLK_OE | 1 | 1 |
| SPI2_CSN_OUT | 1 | 1 |
| SPI2_CSN_OE | 1 | 1 |
| SPI2_MISO_OUT | 1 | 1 |
| SPI2_MISO_OE | 1 | 1 |
| SPI2_MOSI_OUT | 1 | 1 |
| SPI2_MOSI_OE | 1 | 1 |
| I2C_SCL | 1 | 1 |
| I2C_SDA | 1 | 1 |
| UART1_TXD | 1 | 1 |
| UART1_RTSN | 1 | 1 |
| UART1_DTRN | 1 | 1 |
| UART1_OUT1N | 1 | 1 |
| UART1_OUT2N | 1 | 1 |
| UART2_TXD | 1 | 1 |
| UART2_RTSN | 1 | 1 |
| UART2_DTRN | 1 | 1 |
| UART2_OUT1N | 1 | 1 |
| UART2_OUT2N | 1 | 1 |
| CH0_PWM | 1 | 1 |
| CH0_PWMOE | 1 | 1 |
| CH1_PWM | 1 | 1 |
| CH1_PWMOE | 1 | 1 |
| CH2_PWM | 1 | 1 |
| CH2_PWMOE | 1 | 1 |
| CH3_PWM | 1 | 1 |
| CH3_PWMOE | 1 | 1 |
| GPIO_OE | 32 | 1 |
| GPIO_OUT | 32 | 1 |
| INTEG_TDO | 1 | 1 |
| SCAN_OUT | 20 | 1 |
| PRDYN_CHAIN_O | 1 | 1 |

EC5-WORK-ORDER: 149 uncovered buses, 911 uncovered bits, 149 vendor runs required; `P2.T37` cap is 8 and the phase box is 90 — **OVERFLOW by 141 runs**, a `P2.T26` re-scope input, not a silent overrun.

## Re-scope input for `P2.T26`

Stated as options with their measured basis, not as a decision this task is entitled to take.

1. **Run the cap and record the rest as residual.** `P2.T37` takes the 8 widest buses in descending
   bit order and writes the remaining 141 buses to `residual`. Widest 8:
   `EXTM_HWDATA` (64), `DDR_HRDATA` (64), `EXTM_HRDATA` (64), `DDR_HWDATA` (64), `ROM_HRDATA` (32), `APB_PRDATA` (32), `EXTS_HRDATA` (32), `EXTM_HADDR` (32).
   That resolves 384 of 911 bits
   and leaves the `AE350_SOC` row far short of a usable bel. It satisfies the phase's stop rule but
   not `S19`.
2. **Find the real connectivity source before spending runs.** The vendor tool places `AE350_SOC`
   on this device, so the triples exist somewhere other than the `.dat`. Not yet searched: the
   `.fse` tables, and the post-PnR artefacts of the shipped reference design
   (`ae350_shared_ddr3`, whose `riscv_ae350_soc.vo` is a **Post-PnR** netlist naming the single
   `AE350_SOC \u_RiscV_AE350_SOC/u_AE350_SOC` instance and its 149 connections, but carrying no
   coordinates). A cheap read of a shipped file beats 149 vendor runs, and costs 0 runs to try.
3. **Re-scope the row to `E0` on a reduced port set** — the clocks, resets and the `Emb_TCM`
   subset `P2.T20`-`P2.T23` actually exercise — and record the rest as a named residual.

Option 2 is the only one that costs nothing to attempt and is recommended as the first move; the
choice belongs to `P2.T26`.
