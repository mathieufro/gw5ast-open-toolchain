# `DHCE` on lane 3 of a GW5AST-138C HCLK block (`P1.F3`)

`P1.T27` closed lanes 0-2 at `E1` and left lane 3 measured but unbuildable:

> lane 3's entry is an ordinary fabric wire, so a clock reaches it over
> fabric, and `route_dhcen_net` rejects a DHCE-managed net that is not routed
> on global resources end to end.

The vendor's own bitstream for that lane lights `LSR2 <= W212` and no
`CLK*`/`GB*` pip (`lane-138c.md` §5, batch `p1t27-dhce-lane` point `b5l3`), so
refusing the fabric hop does not protect the network — it makes the lane
unusable while the hardware has no other way in.

## 1. Where the asymmetry lives in the database

`chipdb.gw5_make_hclk_pips` joins a block's four logic->HCLK entries to the
block cell's `CLK0, CLK1, CLK2, LSR2`, in that order. Three are the tile's
clock wires; the fourth is an ordinary fabric wire. That list was a literal
inside the loop, so nothing downstream could tell lane 3 from lanes 0-2.

## 2. The change

`apycula/chipdb.py`

* `_gw5_hclk_logic_entry_wires` — the entry list, hoisted out of the loop and
  cited to the `P1.T27` measurement;
* `_gw5_hclk_fabric_entry_lanes()` — the lanes whose entry is not a clock
  wire, **derived** from that list rather than written out again;
* each block cell records `extra_func['hclk_fabric_entry'] = {'lanes': [3],
  'sinks': ['CLKDIV_I<blk>3']}`. Recorded only for devices where the entry
  table has been checked against a vendor bitstream, so the GW5A-25A database
  is byte-identical.

`nextpnr`

* `Extra_chip_data_POD.hclk_fabric_entry_sinks` + `add_hclk_fabric_entry_sink`
  carry those sink wire names into the chipdb;
* `GowinUtils::is_hclk_fabric_entry_sink`;
* `globals.cc is_relaxed_sink` — the upstream extension point that has always
  been called by `route_direct_net` and has always returned `false` — now
  returns `true` for exactly those sinks. The global filter is lifted for that
  one sink, so the dedicated router takes the same last hop the vendor takes,
  the returned path still contains the lane's own `HCLK_MUX_BETA<blk>3` pip,
  and `get_dhcen_bel` finds the hardware `DHCE` and sets `DHCEN_USED` exactly
  as it does on lanes 0-2.

No other sink on the die is relaxed, and a device whose entry table has not
been measured relaxes nothing.

## 3. Verdict

Shape `clocking_dhce`, point `b5l3` — the point `p1t27-dhce-e1b` recorded
`aborted`. The batch line and the `EQUIV` line are in `summary.md` §6.
