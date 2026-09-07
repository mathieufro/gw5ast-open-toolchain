# nextpnr: a board-clocked IOLOGIC on GW5AST-138C (`P3.T09`)

## Verdict, literal

```
nextpnr-himbaechel --timing-allow-fail -r --json iddr-boardclk-tangmega138k-synth.json \
  --write iddr-boardclk-tangmega138k.json --device GW5AST-LV138PG484AC1/I0 \
  --vopt cst=tangmega138k.cst
exit status 0, 0 lines matching ^ERROR
iddr-boardclk-tangmega138k.json: 1 IDDR cell at X65Y108/IOLOGICBI,
  clocked through BUFG at X91Y108/BUFG0 from clk (ball V22, X103Y108/IOBB)
gowin_utils / chipdb: HAS_5A_HCLK present in GW5AST-138C chip_flags -> true
```

`examples/gw5a/iddr-boardclk.v` builds and routes end to end: a board input
clock on `V22` reaches an `IDDR`'s clock on this die through the open flow.

## The half that is measured NOT attainable, and why

The blueprint's second assertion — *"the post-PnR JSON contains exactly 1
`IDDR` cell whose `FCLK` net's driver is an `HCLK` wire"* — is **not
attainable in Phase 3's owned surface**, and the reason is a measurement, not
a shortfall of effort:

* the vendor does not do it either. Twelve vendor bitstreams (`P3.T07`) decode
  **zero** pips into any `FCLK*` wire, and a plain `IDDR` clocked from a pin
  is put on an ordinary global (`CLK0 <= GB10`) with no HCLK bel lit anywhere;
* the 138C database has no such edge to route on: `dev.io2hclk == {}` and
  `chipdb.gw5_create_hclk_iol_pip` returns `False` for this device;
* building that table is `apycula/chipdb.py`'s `gw5_create_hclk_iol_pip`,
  which `P3-io-iologic.md` freezes for this phase, and it needs an attribution
  campaign of its own because no bitstream this task produced lights a fuse
  there.

Recorded as `G-FCLK-138C` in `evidence/pin-to-hclk/summary.md`, with an owner.

## What did change in nextpnr, and what it is worth

`himbaechel/uarch/gowin/globals.cc`, `gowin_utils.{h,cc}` on
`gowin/io-iologic-138c`:

1. **`route_direct_net` no longer loses a sink failure.** It folded its result
   through one accumulator that read its own previous value, so a net whose
   *first* sink failed and whose second succeeded came back `ROUTED_ALL`. The
   two orders disagreed on the same net (a DHCE-gated HCLK reaching a `CLKDIV`
   and an IOLOGIC `FCLK`). Reached and missed sinks are now counted
   independently and the result derived from the counts.
2. **A partly routed global network names the sinks it missed.** New
   `report_unreachable_sinks` prints one line per unreachable sink with its
   cell, port, bel and wire, and — via the new
   `GowinUtils::is_iologic_fclk_wire` — says outright when the sink is an
   IOLOGIC fast-clock pin the database carries no HCLK entry for. Before, the
   run died on `It was not possible to completely route the hclk net using
   only global resources` with nothing to act on.

Observed on the `P3.T07` probe design:

```
Warning: Failed to route net 'hclk' from X91Y108/CLK1 to X82Y108/FCLKA using dedicated routing.
Info: net 'hclk': no dedicated path to dut.FCLK (bel X82Y108/IOLOGICAI, wire X82Y108/FCLKA)
Info:   X82Y108/FCLKA is an IOLOGIC fast-clock pin; this device's database carries no HCLK
        entry for it, so no clock network reaches it
ERROR: It was not possible to completely route the hclk net using only global resources.
```

Gate check: `himbaechel/uarch/gowin/tests/check_hclk_to_fclk_138c.py`, wired
into `_gate-fast`; 3 checks, 0 failures.

## Pair

Rebuilt once in the foreground from `gowin/io-iologic-138c`
(`cmake --build build -j8`, 50 s) and installed:

| artefact | sha256 (first 8) | note |
|---|---|---|
| `nextpnr-himbaechel` | `454714cc` | was `d400514b` |
| `chipdb-GW5AST-138C.bin` | `9cce739d` | **byte-identical** — no constids and no chipdb change |
| `GW5AST-138C.msgpack.xz` | `6a776c74` | unchanged |
