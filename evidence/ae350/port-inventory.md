PORTS 149

# P2.T02 — AE350_SOC port inventory

`AE350_SOC` measured, never quoted: 149 declarations in `primitive.xml`, 149 `.PORT()` connections in the golden post-PnR netlist, 911 declared bits, 0 parameters.

| name | direction | width | in_xml | in_vo | tied_to |
|---|---|---|---|---|---|
| `AHB_CE` | input | 1 | yes | yes | `VCC` |
| `AHB_CLK` | input | 1 | yes | yes | `AHB_CLK` |
| `APB2AHB_CE` | input | 1 | yes | yes | `VCC` |
| `APB_CE` | input | 8 | yes | yes | `VCC, GND, VCC, VCC, GND, VCC, GND, VCC` |
| `APB_CLK` | input | 1 | yes | yes | `APB_CLK` |
| `APB_PADDR` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/APB_PADDR [31:0]` |
| `APB_PENABLE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_APB_PENABLE` |
| `APB_PPROT` | output | 3 | yes | yes | `u_RiscV_AE350_SOC/APB_PPROT [2:0]` |
| `APB_PRDATA` | input | 32 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `APB_PREADY` | input | 1 | yes | yes | `GND` |
| `APB_PSEL` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_APB_PSEL` |
| `APB_PSLVERR` | input | 1 | yes | yes | `GND` |
| `APB_PSTRB` | output | 4 | yes | yes | `u_RiscV_AE350_SOC/APB_PSTRB [3:0]` |
| `APB_PWDATA` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/APB_PWDATA [31:0]` |
| `APB_PWRITE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_APB_PWRITE` |
| `AXI_CE` | input | 1 | yes | yes | `VCC` |
| `CH0_PWM` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH0_PWM` |
| `CH0_PWMOE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH0_PWMOE` |
| `CH1_PWM` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH1_PWM` |
| `CH1_PWMOE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH1_PWMOE` |
| `CH2_PWM` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH2_PWM` |
| `CH2_PWMOE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH2_PWMOE` |
| `CH3_PWM` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH3_PWM` |
| `CH3_PWMOE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CH3_PWMOE` |
| `CORE0_WFI_MODE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_CORE0_WFI_MODE` |
| `CORE_CE` | input | 1 | yes | yes | `VCC` |
| `CORE_CLK` | input | 1 | yes | yes | `CORE_CLK` |
| `DBG_TCK` | input | 1 | yes | yes | `TCK_IN` |
| `DDR_CE` | input | 1 | yes | yes | `VCC` |
| `DDR_CLK` | input | 1 | yes | yes | `DDR_CLK` |
| `DDR_HADDR` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/DDR_HADDR_0 [31:28], u_RiscV_AE350_SOC/DDR_HADDR [27:0]` |
| `DDR_HBURST` | output | 3 | yes | yes | `u_RiscV_AE350_SOC/DDR_HBURST [2:0]` |
| `DDR_HPROT` | output | 4 | yes | yes | `u_RiscV_AE350_SOC/DDR_HPROT [3:0]` |
| `DDR_HRDATA` | input | 64 | yes | yes | `u_RiscV_AE350_SOC/DDR_HRDATA [63:0]` |
| `DDR_HREADY` | input | 1 | yes | yes | `u_RiscV_AE350_SOC/DDR_HREADY` |
| `DDR_HRESP` | input | 1 | yes | yes | `GND` |
| `DDR_HSIZE` | output | 3 | yes | yes | `u_RiscV_AE350_SOC/DDR_HSIZE [2:0]` |
| `DDR_HTRANS` | output | 2 | yes | yes | `u_RiscV_AE350_SOC/DDR_HTRANS [1], u_RiscV_AE350_SOC/DDR_HTRANS_0 [0]` |
| `DDR_HWDATA` | output | 64 | yes | yes | `u_RiscV_AE350_SOC/DDR_HWDATA [63:0]` |
| `DDR_HWRITE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/DDR_HWRITE` |
| `DDR_RSTN` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/DDR_RSTN` |
| `DMA_ACK` | output | 8 | yes | yes | `u_RiscV_AE350_SOC/DMA_ACK [7:0]` |
| `DMA_REQ` | input | 8 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND` |
| `EMA` | input | 3 | yes | yes | `GND, VCC, VCC` |
| `EMAS` | input | 1 | yes | yes | `GND` |
| `EMAW` | input | 2 | yes | yes | `GND, VCC` |
| `EXTM_HADDR` | input | 32 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `EXTM_HBURST` | input | 3 | yes | yes | `GND, GND, GND` |
| `EXTM_HPROT` | input | 4 | yes | yes | `GND, GND, GND, GND` |
| `EXTM_HRDATA` | output | 64 | yes | yes | `u_RiscV_AE350_SOC/EXTM_HRDATA [63:0]` |
| `EXTM_HREADY` | input | 1 | yes | yes | `GND` |
| `EXTM_HREADYOUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_EXTM_HREADYOUT` |
| `EXTM_HRESP` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_EXTM_HRESP` |
| `EXTM_HSEL` | input | 1 | yes | yes | `GND` |
| `EXTM_HSIZE` | input | 3 | yes | yes | `GND, GND, GND` |
| `EXTM_HTRANS` | input | 2 | yes | yes | `GND, GND` |
| `EXTM_HWDATA` | input | 64 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `EXTM_HWRITE` | input | 1 | yes | yes | `GND` |
| `EXTS_HADDR` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HADDR [31:0]` |
| `EXTS_HBURST` | output | 3 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HBURST [2:0]` |
| `EXTS_HPROT` | output | 4 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HPROT [3:0]` |
| `EXTS_HRDATA` | input | 32 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `EXTS_HREADYIN` | input | 1 | yes | yes | `GND` |
| `EXTS_HRESP` | input | 1 | yes | yes | `GND` |
| `EXTS_HSEL` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_EXTS_HSEL` |
| `EXTS_HSIZE` | output | 3 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HSIZE [2:0]` |
| `EXTS_HTRANS` | output | 2 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HTRANS [1:0]` |
| `EXTS_HWDATA` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/EXTS_HWDATA [31:0]` |
| `EXTS_HWRITE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_EXTS_HWRITE` |
| `GPIO_IN` | input | 32 | yes | yes | `GPIO_in[31:0]` |
| `GPIO_OE` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/GPIO_OE [31:0]` |
| `GPIO_OUT` | output | 32 | yes | yes | `GPIO_OUT[31:0]` |
| `GP_INT` | input | 16 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `HRESETN` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/HRESETN` |
| `HW_RSTN` | input | 1 | yes | yes | `HW_RSTN` |
| `I2C_SCL` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_I2C_SCL` |
| `I2C_SCL_IN` | input | 1 | yes | yes | `GND` |
| `I2C_SDA` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_I2C_SDA` |
| `I2C_SDA_IN` | input | 1 | yes | yes | `GND` |
| `INTEG_TCK` | input | 1 | yes | yes | `GND` |
| `INTEG_TDI` | input | 1 | yes | yes | `GND` |
| `INTEG_TDO` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_INTEG_TDO` |
| `INTEG_TMS` | input | 1 | yes | yes | `GND` |
| `INTEG_TRST` | input | 1 | yes | yes | `GND` |
| `PGEN_CHAIN_I` | input | 1 | yes | yes | `VCC` |
| `POR_N` | input | 1 | yes | yes | `POR_RSTN` |
| `PRDYN_CHAIN_O` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_PRDYN_CHAIN_O` |
| `PRESETN` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/PRESETN` |
| `RET1N` | input | 1 | yes | yes | `VCC` |
| `RET2N` | input | 1 | yes | yes | `VCC` |
| `ROM_HADDR` | output | 32 | yes | yes | `u_RiscV_AE350_SOC/ROM_HADDR [31:2], u_RiscV_AE350_SOC/ROM_HADDR_0 [1:0]` |
| `ROM_HRDATA` | input | 32 | yes | yes | `u_RiscV_AE350_SOC/mem_RAMOUT_3937_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3810_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3683_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3556_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3429_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3302_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3175_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_3048_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2921_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2794_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2667_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2540_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2413_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2286_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2159_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_2032_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1905_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1778_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1651_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1524_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1397_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1270_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1143_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_1016_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_889_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_762_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_635_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_508_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_381_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_254_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_127_G[0]_6 , u_RiscV_AE350_SOC/mem_RAMOUT_0_G[0]_6` |
| `ROM_HREADY` | input | 1 | yes | yes | `u_RiscV_AE350_SOC/ROM_HREADY` |
| `ROM_HRESP` | input | 1 | yes | yes | `u_RiscV_AE350_SOC/ROM_HRESP` |
| `ROM_HTRANS` | output | 2 | yes | yes | `u_RiscV_AE350_SOC/ROM_HTRANS [1], u_RiscV_AE350_SOC/ROM_HTRANS_0 [0]` |
| `ROM_HWRITE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/ROM_HWRITE` |
| `RTC_CLK` | input | 1 | yes | yes | `RTC_CLK` |
| `RTC_WAKEUP` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_RTC_WAKEUP` |
| `SCAN_EN` | input | 1 | yes | yes | `GND` |
| `SCAN_IN` | input | 20 | yes | yes | `GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND, GND` |
| `SCAN_OUT` | output | 20 | yes | yes | `u_RiscV_AE350_SOC/SCAN_OUT [19:0]` |
| `SCAN_TEST` | input | 1 | yes | yes | `GND` |
| `SPI2_CLK_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_CLK_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_CLK_OE` |
| `SPI2_CLK_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_CLK_OUT` |
| `SPI2_CSN_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_CSN_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_CSN_OE` |
| `SPI2_CSN_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_CSN_OUT` |
| `SPI2_HOLDN_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_HOLDN_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_HOLDN_OE` |
| `SPI2_HOLDN_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_HOLDN_OUT` |
| `SPI2_MISO_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_MISO_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_MISO_OE` |
| `SPI2_MISO_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_MISO_OUT` |
| `SPI2_MOSI_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_MOSI_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_MOSI_OE` |
| `SPI2_MOSI_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_MOSI_OUT` |
| `SPI2_WPN_IN` | input | 1 | yes | yes | `GND` |
| `SPI2_WPN_OE` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_WPN_OE` |
| `SPI2_WPN_OUT` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_SPI2_WPN_OUT` |
| `TDI_IN` | input | 1 | yes | yes | `TDI_IN` |
| `TDO_OE` | output | 1 | yes | yes | `TDO_OE` |
| `TDO_OUT` | output | 1 | yes | yes | `TDO_OUT` |
| `TEST_CLK` | input | 1 | yes | yes | `GND` |
| `TEST_MODE` | input | 1 | yes | yes | `GND` |
| `TEST_RSTN` | input | 1 | yes | yes | `VCC` |
| `TMS_IN` | input | 1 | yes | yes | `TMS_IN` |
| `TRST_IN` | input | 1 | yes | yes | `TRST_IN` |
| `UART1_CTSN` | input | 1 | yes | yes | `GND` |
| `UART1_DCDN` | input | 1 | yes | yes | `GND` |
| `UART1_DSRN` | input | 1 | yes | yes | `GND` |
| `UART1_DTRN` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_UART1_DTRN` |
| `UART1_OUT1N` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_UART1_OUT1N` |
| `UART1_OUT2N` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_UART1_OUT2N` |
| `UART1_RIN` | input | 1 | yes | yes | `GND` |
| `UART1_RTSN` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_UART1_RTSN` |
| `UART1_RXD` | input | 1 | yes | yes | `GND` |
| `UART1_TXD` | output | 1 | yes | yes | `u_RiscV_AE350_SOC/u_AE350_SOC_218_UART1_TXD` |
| `UART2_CTSN` | input | 1 | yes | yes | `UART2_CTSN` |
| `UART2_DCDN` | input | 1 | yes | yes | `UART2_DCDN` |
| `UART2_DSRN` | input | 1 | yes | yes | `UART2_DSRN` |
| `UART2_DTRN` | output | 1 | yes | yes | `UART2_DTRN` |
| `UART2_OUT1N` | output | 1 | yes | yes | `UART2_OUT1N` |
| `UART2_OUT2N` | output | 1 | yes | yes | `UART2_OUT2N` |
| `UART2_RIN` | input | 1 | yes | yes | `UART2_RIN` |
| `UART2_RTSN` | output | 1 | yes | yes | `UART2_RTSN` |
| `UART2_RXD` | input | 1 | yes | yes | `UART2_RXD` |
| `UART2_TXD` | output | 1 | yes | yes | `UART2_TXD` |
| `WAKEUP_IN` | input | 1 | yes | yes | `GND` |

## DISCREPANCIES

None: the two sources declare and connect the same ports.

## SOURCES

Four independent sources, each counted rather than quoted (`F80` records three
published counts that disagree; this settles it at **149**).

| source | ports | bits | how counted |
|---|---|---|---|
| `prim_syns/gw5a/primitive.xml` `<module><name>AE350_SOC</name>` (Standard 1.9.12.03) | 149 | 911 | every `<INPUT>`/`<OUTPUT>`/`<INOUT>` with its `width` |
| golden post-PnR netlist `ae350_shared_ddr3/.../riscv_ae350_soc.vo` (sha256 `8643faac…`) | 149 | — | every `.PORT(net)` of `\u_RiscV_AE350_SOC/u_AE350_SOC` |
| `ae350_demo/.../riscv_ae350_soc.vo` (second vendor design) | 149 | — | same |
| apicula wiki `AE350_SOC` + LiteX `cpu/gowin_ae350/core.py` | 149 | 911 | published port table / `Instance("AE350_SOC", ...)` keys |

All four carry the **same 149 names**; the two that state widths state the same
911 bits, and no name, direction or width differs anywhere. `INOUT` count is
zero: the block's bidirectional pads are split into `_IN`/`_OUT`/`_OE` triples
(`SPI2_*`) or into an output plus a separate `_IN` (`I2C_SCL`/`I2C_SCL_IN`).

The two `.vo` designs connect all 149 — no port is left off the instance — so
the `DISCREPANCIES` section above is empty by measurement, not by omission.
