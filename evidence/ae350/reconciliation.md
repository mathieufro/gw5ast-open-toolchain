# P2.T04 — the AE350_SOC wire-count reconciliation

`S19`'s first sub-item: the `.dat` MCU tables against the measured port
inventory. Both sides are counted (`P2.T02`, `P2.T03`); neither number is
quoted from a document.

## The two counts

- **Fabric wires needed**: **911** — the 149 `AE350_SOC` ports of
  `port-inventory.json` expanded to their bit widths (149 declarations,
  911 bits; four independent sources agree on both).
- **Live `.dat` MCU-table entries**: **0** — `McuIns` (265 slots) and
  `McuOuts` (372 slots) parse cleanly and every one of the 637 slots holds
  the `(-1, -1, -1)` sentinel, which `make_port`'s `if r < 0 or c < 0:
  return` guard (`chipdb.py:3741-3742`) treats as no wire at all.

The 637 in `S19` is a table **length**, not a wire count. The tables exist
and are empty.

### Why that is the table's content and not a parse failure

- `read_portmap` ends on `assert self._cur == 0x7b43e` (`dat_parser.py`),
  so the sequential cursor that reads `McuIns`/`McuOuts` lands exactly
  where the layout says — a misread would have desynced that assert.
- The same `read_outs` code on the same file region returns **224/270**
  live `EMcuIns` and **302/319** live `EMcuOuts` triples for `GW1NS-4`,
  the device that actually carries an EMCU. The reader reads.
- Both shipped IDE editions agree: 0 live on Standard 1.9.12.03 and 0 live
  on the Education 1.9.11.03 archive. Not a version artefact.
- Every one of the 33 `(r, c, wire)` tables in the 138C `.dat` is empty,
  `AluIn`/`MultIn` included — blocks the 138C certainly has. The whole
  legacy triple-portmap block is unused on GW5; these devices carry their
  port maps elsewhere.

## Per-bus coverage

| bus | bits_needed | table_slice | covered |
|---|---|---|---|
| `AHB_CE` | 1 | none | 0 |
| `AHB_CLK` | 1 | none | 0 |
| `APB2AHB_CE` | 1 | none | 0 |
| `APB_CE` | 8 | none | 0 |
| `APB_CLK` | 1 | none | 0 |
| `APB_PADDR` | 32 | none | 0 |
| `APB_PENABLE` | 1 | none | 0 |
| `APB_PPROT` | 3 | none | 0 |
| `APB_PRDATA` | 32 | none | 0 |
| `APB_PREADY` | 1 | none | 0 |
| `APB_PSEL` | 1 | none | 0 |
| `APB_PSLVERR` | 1 | none | 0 |
| `APB_PSTRB` | 4 | none | 0 |
| `APB_PWDATA` | 32 | none | 0 |
| `APB_PWRITE` | 1 | none | 0 |
| `AXI_CE` | 1 | none | 0 |
| `CH0_PWM` | 1 | none | 0 |
| `CH0_PWMOE` | 1 | none | 0 |
| `CH1_PWM` | 1 | none | 0 |
| `CH1_PWMOE` | 1 | none | 0 |
| `CH2_PWM` | 1 | none | 0 |
| `CH2_PWMOE` | 1 | none | 0 |
| `CH3_PWM` | 1 | none | 0 |
| `CH3_PWMOE` | 1 | none | 0 |
| `CORE0_WFI_MODE` | 1 | none | 0 |
| `CORE_CE` | 1 | none | 0 |
| `CORE_CLK` | 1 | none | 0 |
| `DBG_TCK` | 1 | none | 0 |
| `DDR_CE` | 1 | none | 0 |
| `DDR_CLK` | 1 | none | 0 |
| `DDR_HADDR` | 32 | none | 0 |
| `DDR_HBURST` | 3 | none | 0 |
| `DDR_HPROT` | 4 | none | 0 |
| `DDR_HRDATA` | 64 | none | 0 |
| `DDR_HREADY` | 1 | none | 0 |
| `DDR_HRESP` | 1 | none | 0 |
| `DDR_HSIZE` | 3 | none | 0 |
| `DDR_HTRANS` | 2 | none | 0 |
| `DDR_HWDATA` | 64 | none | 0 |
| `DDR_HWRITE` | 1 | none | 0 |
| `DDR_RSTN` | 1 | none | 0 |
| `DMA_ACK` | 8 | none | 0 |
| `DMA_REQ` | 8 | none | 0 |
| `EMA` | 3 | none | 0 |
| `EMAS` | 1 | none | 0 |
| `EMAW` | 2 | none | 0 |
| `EXTM_HADDR` | 32 | none | 0 |
| `EXTM_HBURST` | 3 | none | 0 |
| `EXTM_HPROT` | 4 | none | 0 |
| `EXTM_HRDATA` | 64 | none | 0 |
| `EXTM_HREADY` | 1 | none | 0 |
| `EXTM_HREADYOUT` | 1 | none | 0 |
| `EXTM_HRESP` | 1 | none | 0 |
| `EXTM_HSEL` | 1 | none | 0 |
| `EXTM_HSIZE` | 3 | none | 0 |
| `EXTM_HTRANS` | 2 | none | 0 |
| `EXTM_HWDATA` | 64 | none | 0 |
| `EXTM_HWRITE` | 1 | none | 0 |
| `EXTS_HADDR` | 32 | none | 0 |
| `EXTS_HBURST` | 3 | none | 0 |
| `EXTS_HPROT` | 4 | none | 0 |
| `EXTS_HRDATA` | 32 | none | 0 |
| `EXTS_HREADYIN` | 1 | none | 0 |
| `EXTS_HRESP` | 1 | none | 0 |
| `EXTS_HSEL` | 1 | none | 0 |
| `EXTS_HSIZE` | 3 | none | 0 |
| `EXTS_HTRANS` | 2 | none | 0 |
| `EXTS_HWDATA` | 32 | none | 0 |
| `EXTS_HWRITE` | 1 | none | 0 |
| `GPIO_IN` | 32 | none | 0 |
| `GPIO_OE` | 32 | none | 0 |
| `GPIO_OUT` | 32 | none | 0 |
| `GP_INT` | 16 | none | 0 |
| `HRESETN` | 1 | none | 0 |
| `HW_RSTN` | 1 | none | 0 |
| `I2C_SCL` | 1 | none | 0 |
| `I2C_SCL_IN` | 1 | none | 0 |
| `I2C_SDA` | 1 | none | 0 |
| `I2C_SDA_IN` | 1 | none | 0 |
| `INTEG_TCK` | 1 | none | 0 |
| `INTEG_TDI` | 1 | none | 0 |
| `INTEG_TDO` | 1 | none | 0 |
| `INTEG_TMS` | 1 | none | 0 |
| `INTEG_TRST` | 1 | none | 0 |
| `PGEN_CHAIN_I` | 1 | none | 0 |
| `POR_N` | 1 | none | 0 |
| `PRDYN_CHAIN_O` | 1 | none | 0 |
| `PRESETN` | 1 | none | 0 |
| `RET1N` | 1 | none | 0 |
| `RET2N` | 1 | none | 0 |
| `ROM_HADDR` | 32 | none | 0 |
| `ROM_HRDATA` | 32 | none | 0 |
| `ROM_HREADY` | 1 | none | 0 |
| `ROM_HRESP` | 1 | none | 0 |
| `ROM_HTRANS` | 2 | none | 0 |
| `ROM_HWRITE` | 1 | none | 0 |
| `RTC_CLK` | 1 | none | 0 |
| `RTC_WAKEUP` | 1 | none | 0 |
| `SCAN_EN` | 1 | none | 0 |
| `SCAN_IN` | 20 | none | 0 |
| `SCAN_OUT` | 20 | none | 0 |
| `SCAN_TEST` | 1 | none | 0 |
| `SPI2_CLK_IN` | 1 | none | 0 |
| `SPI2_CLK_OE` | 1 | none | 0 |
| `SPI2_CLK_OUT` | 1 | none | 0 |
| `SPI2_CSN_IN` | 1 | none | 0 |
| `SPI2_CSN_OE` | 1 | none | 0 |
| `SPI2_CSN_OUT` | 1 | none | 0 |
| `SPI2_HOLDN_IN` | 1 | none | 0 |
| `SPI2_HOLDN_OE` | 1 | none | 0 |
| `SPI2_HOLDN_OUT` | 1 | none | 0 |
| `SPI2_MISO_IN` | 1 | none | 0 |
| `SPI2_MISO_OE` | 1 | none | 0 |
| `SPI2_MISO_OUT` | 1 | none | 0 |
| `SPI2_MOSI_IN` | 1 | none | 0 |
| `SPI2_MOSI_OE` | 1 | none | 0 |
| `SPI2_MOSI_OUT` | 1 | none | 0 |
| `SPI2_WPN_IN` | 1 | none | 0 |
| `SPI2_WPN_OE` | 1 | none | 0 |
| `SPI2_WPN_OUT` | 1 | none | 0 |
| `TDI_IN` | 1 | none | 0 |
| `TDO_OE` | 1 | none | 0 |
| `TDO_OUT` | 1 | none | 0 |
| `TEST_CLK` | 1 | none | 0 |
| `TEST_MODE` | 1 | none | 0 |
| `TEST_RSTN` | 1 | none | 0 |
| `TMS_IN` | 1 | none | 0 |
| `TRST_IN` | 1 | none | 0 |
| `UART1_CTSN` | 1 | none | 0 |
| `UART1_DCDN` | 1 | none | 0 |
| `UART1_DSRN` | 1 | none | 0 |
| `UART1_DTRN` | 1 | none | 0 |
| `UART1_OUT1N` | 1 | none | 0 |
| `UART1_OUT2N` | 1 | none | 0 |
| `UART1_RIN` | 1 | none | 0 |
| `UART1_RTSN` | 1 | none | 0 |
| `UART1_RXD` | 1 | none | 0 |
| `UART1_TXD` | 1 | none | 0 |
| `UART2_CTSN` | 1 | none | 0 |
| `UART2_DCDN` | 1 | none | 0 |
| `UART2_DSRN` | 1 | none | 0 |
| `UART2_DTRN` | 1 | none | 0 |
| `UART2_OUT1N` | 1 | none | 0 |
| `UART2_OUT2N` | 1 | none | 0 |
| `UART2_RIN` | 1 | none | 0 |
| `UART2_RTSN` | 1 | none | 0 |
| `UART2_RXD` | 1 | none | 0 |
| `UART2_TXD` | 1 | none | 0 |
| `WAKEUP_IN` | 1 | none | 0 |

## UNCOVERED

All 149 buses (911 bits). No bus has a table
slice, so none is a table read and every one routes to `EC5` differential
wire discovery (`P2.T06` plans it, `P2.T37` executes it).

`AHB_CE`, `AHB_CLK`, `APB2AHB_CE`, `APB_CE`, `APB_CLK`, `APB_PADDR`, `APB_PENABLE`, `APB_PPROT`, `APB_PRDATA`, `APB_PREADY`, `APB_PSEL`, `APB_PSLVERR`, `APB_PSTRB`, `APB_PWDATA`, `APB_PWRITE`, `AXI_CE`, `CH0_PWM`, `CH0_PWMOE`, `CH1_PWM`, `CH1_PWMOE`, `CH2_PWM`, `CH2_PWMOE`, `CH3_PWM`, `CH3_PWMOE`, `CORE0_WFI_MODE`, `CORE_CE`, `CORE_CLK`, `DBG_TCK`, `DDR_CE`, `DDR_CLK`, `DDR_HADDR`, `DDR_HBURST`, `DDR_HPROT`, `DDR_HRDATA`, `DDR_HREADY`, `DDR_HRESP`, `DDR_HSIZE`, `DDR_HTRANS`, `DDR_HWDATA`, `DDR_HWRITE`, `DDR_RSTN`, `DMA_ACK`, `DMA_REQ`, `EMA`, `EMAS`, `EMAW`, `EXTM_HADDR`, `EXTM_HBURST`, `EXTM_HPROT`, `EXTM_HRDATA`, `EXTM_HREADY`, `EXTM_HREADYOUT`, `EXTM_HRESP`, `EXTM_HSEL`, `EXTM_HSIZE`, `EXTM_HTRANS`, `EXTM_HWDATA`, `EXTM_HWRITE`, `EXTS_HADDR`, `EXTS_HBURST`, `EXTS_HPROT`, `EXTS_HRDATA`, `EXTS_HREADYIN`, `EXTS_HRESP`, `EXTS_HSEL`, `EXTS_HSIZE`, `EXTS_HTRANS`, `EXTS_HWDATA`, `EXTS_HWRITE`, `GPIO_IN`, `GPIO_OE`, `GPIO_OUT`, `GP_INT`, `HRESETN`, `HW_RSTN`, `I2C_SCL`, `I2C_SCL_IN`, `I2C_SDA`, `I2C_SDA_IN`, `INTEG_TCK`, `INTEG_TDI`, `INTEG_TDO`, `INTEG_TMS`, `INTEG_TRST`, `PGEN_CHAIN_I`, `POR_N`, `PRDYN_CHAIN_O`, `PRESETN`, `RET1N`, `RET2N`, `ROM_HADDR`, `ROM_HRDATA`, `ROM_HREADY`, `ROM_HRESP`, `ROM_HTRANS`, `ROM_HWRITE`, `RTC_CLK`, `RTC_WAKEUP`, `SCAN_EN`, `SCAN_IN`, `SCAN_OUT`, `SCAN_TEST`, `SPI2_CLK_IN`, `SPI2_CLK_OE`, `SPI2_CLK_OUT`, `SPI2_CSN_IN`, `SPI2_CSN_OE`, `SPI2_CSN_OUT`, `SPI2_HOLDN_IN`, `SPI2_HOLDN_OE`, `SPI2_HOLDN_OUT`, `SPI2_MISO_IN`, `SPI2_MISO_OE`, `SPI2_MISO_OUT`, `SPI2_MOSI_IN`, `SPI2_MOSI_OE`, `SPI2_MOSI_OUT`, `SPI2_WPN_IN`, `SPI2_WPN_OE`, `SPI2_WPN_OUT`, `TDI_IN`, `TDO_OE`, `TDO_OUT`, `TEST_CLK`, `TEST_MODE`, `TEST_RSTN`, `TMS_IN`, `TRST_IN`, `UART1_CTSN`, `UART1_DCDN`, `UART1_DSRN`, `UART1_DTRN`, `UART1_OUT1N`, `UART1_OUT2N`, `UART1_RIN`, `UART1_RTSN`, `UART1_RXD`, `UART1_TXD`, `UART2_CTSN`, `UART2_DCDN`, `UART2_DSRN`, `UART2_DTRN`, `UART2_OUT1N`, `UART2_OUT2N`, `UART2_RIN`, `UART2_RTSN`, `UART2_RXD`, `UART2_TXD`, `WAKEUP_IN`

## Consequence for the phase plan — a `P2.T26` re-scope input

`P2.T37` caps `EC5` at **8** vendor runs and `D50` boxes the phase at 90.
One presence-diff per bus over 149 buses does not fit either, so the
blueprint's shape — *table read for most buses, `EC5` for the leftovers* —
does not survive this measurement. `P2.T06` must either find the GW5 port
map's real home (the `.fse`, where every other GW5 block's ports come from)
or say on the same line that the discovery cost exceeds the cap. Recorded
here, decided there; this task changes no plan and no code.

RECONCILIATION-VERDICT: 0/911 wires covered; uncovered buses: AHB_CE, AHB_CLK, APB2AHB_CE, APB_CE, APB_CLK, APB_PADDR, APB_PENABLE, APB_PPROT, APB_PRDATA, APB_PREADY, APB_PSEL, APB_PSLVERR, APB_PSTRB, APB_PWDATA, APB_PWRITE, AXI_CE, CH0_PWM, CH0_PWMOE, CH1_PWM, CH1_PWMOE, CH2_PWM, CH2_PWMOE, CH3_PWM, CH3_PWMOE, CORE0_WFI_MODE, CORE_CE, CORE_CLK, DBG_TCK, DDR_CE, DDR_CLK, DDR_HADDR, DDR_HBURST, DDR_HPROT, DDR_HRDATA, DDR_HREADY, DDR_HRESP, DDR_HSIZE, DDR_HTRANS, DDR_HWDATA, DDR_HWRITE, DDR_RSTN, DMA_ACK, DMA_REQ, EMA, EMAS, EMAW, EXTM_HADDR, EXTM_HBURST, EXTM_HPROT, EXTM_HRDATA, EXTM_HREADY, EXTM_HREADYOUT, EXTM_HRESP, EXTM_HSEL, EXTM_HSIZE, EXTM_HTRANS, EXTM_HWDATA, EXTM_HWRITE, EXTS_HADDR, EXTS_HBURST, EXTS_HPROT, EXTS_HRDATA, EXTS_HREADYIN, EXTS_HRESP, EXTS_HSEL, EXTS_HSIZE, EXTS_HTRANS, EXTS_HWDATA, EXTS_HWRITE, GPIO_IN, GPIO_OE, GPIO_OUT, GP_INT, HRESETN, HW_RSTN, I2C_SCL, I2C_SCL_IN, I2C_SDA, I2C_SDA_IN, INTEG_TCK, INTEG_TDI, INTEG_TDO, INTEG_TMS, INTEG_TRST, PGEN_CHAIN_I, POR_N, PRDYN_CHAIN_O, PRESETN, RET1N, RET2N, ROM_HADDR, ROM_HRDATA, ROM_HREADY, ROM_HRESP, ROM_HTRANS, ROM_HWRITE, RTC_CLK, RTC_WAKEUP, SCAN_EN, SCAN_IN, SCAN_OUT, SCAN_TEST, SPI2_CLK_IN, SPI2_CLK_OE, SPI2_CLK_OUT, SPI2_CSN_IN, SPI2_CSN_OE, SPI2_CSN_OUT, SPI2_HOLDN_IN, SPI2_HOLDN_OE, SPI2_HOLDN_OUT, SPI2_MISO_IN, SPI2_MISO_OE, SPI2_MISO_OUT, SPI2_MOSI_IN, SPI2_MOSI_OE, SPI2_MOSI_OUT, SPI2_WPN_IN, SPI2_WPN_OE, SPI2_WPN_OUT, TDI_IN, TDO_OE, TDO_OUT, TEST_CLK, TEST_MODE, TEST_RSTN, TMS_IN, TRST_IN, UART1_CTSN, UART1_DCDN, UART1_DSRN, UART1_DTRN, UART1_OUT1N, UART1_OUT2N, UART1_RIN, UART1_RTSN, UART1_RXD, UART1_TXD, UART2_CTSN, UART2_DCDN, UART2_DSRN, UART2_DTRN, UART2_OUT1N, UART2_OUT2N, UART2_RIN, UART2_RTSN, UART2_RXD, UART2_TXD, WAKEUP_IN
