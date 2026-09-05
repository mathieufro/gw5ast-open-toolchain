# GW5AST-138C DHCEN `CE` wires — MEASURED (P1.T25)

Task: `blueprints/P1-clocking.md` P1.T25. Device `GW5AST-138C`, part
`GW5AST-LV138PG484AC1/I0`, `device_version C`. Oracle: Gowin IDE **1.9.12.03
Standard, licensed** (`edu-provisional: false`). Grid 109 rows x 182 cols.
Machine-readable twin: `ce-wires-138c.json`. Method, evidence and the two
refutations: `trace-138c.md`.

**The primitive is `DHCE`, not `DHCEN`, and its enable port is `CEN`, not
`CE`.** `DHCEN` does not exist on this family: GowinSynthesis answers
`ERROR (EX3937) : Instantiating unknown module 'DHCEN'`, and
`IDE/ipcore/DHCEN/dhcen.ipspec` lists no `GW5*` device. The GW5A primitive
table `IDE/bin/prim_syns/gw5a/primitive.xml` spells it `DHCE(CLKIN, CEN,
CLKOUT)`. Everything below is that primitive; the column is still called `CE`
because that is what `_dhcen_ce` calls it.

## The table

`24` sites, the vendor's own stated capacity (`DHCE 24/24` in the
`Clock Resource Usage Summary`; `25` is refused). Six HCLK block cells
(`../clocking/hclk-topology.md`, P1.T04) x **4** sites each. **There is no top
side and there are no interbank entries** — see `trace-138c.md` §5.

| side | idx | row | col | wire | idx measured | first seen at n |
|---|---|---|---|---|---|---|
| L | 0 | 27 | 0 | `C2` | yes | 21 |
| L | 1 | 27 | 0 | `C5` | yes | 22 |
| L | 2 | 27 | 0 | `C7` | yes | 23 |
| L | 3 | 27 | 0 | `D2` | yes | 24 |
| L | 0 | 81 | 0 | `C2` | yes | 17 |
| L | 1 | 81 | 0 | `A5` | yes | 18 |
| L | 2 | 81 | 0 | `C7` | yes | 19 |
| L | 3 | 81 | 0 | `A4` | yes | 20 |
| R | 0 | 27 | 181 | `C2` | no | 5 |
| R | 1 | 27 | 181 | `C5` | no | 12 |
| R | 2 | 27 | 181 | `C7` | no | 12 |
| R | 3 | 27 | 181 | `D2` | no | 12 |
| R | 0 | 81 | 181 | `C2` | no | 12 |
| R | 1 | 81 | 181 | `C5` | no | 12 |
| R | 2 | 81 | 181 | `C7` | no | 12 |
| R | 3 | 81 | 181 | `D2` | no | 12 |
| B | 0 | 108 | 64 | `C2` | yes | 1 |
| B | 1 | 108 | 64 | `C5` | yes | 2 |
| B | 2 | 108 | 64 | `C7` | yes | 3 |
| B | 3 | 108 | 64 | `D2` | yes | 4 |
| B | 0 | 108 | 117 | `C2` | no | 16 |
| B | 1 | 108 | 117 | `C5` | no | 16 |
| B | 2 | 108 | 117 | `C7` | no | 16 |
| B | 3 | 108 | 117 | `D2` | no | 16 |

All six wire names (`A4 A5 C2 C5 C7 D2`) resolve in `wirenames_5ast138c`.
No `(row, col, wire)` triple repeats. Every `(row, col)` is one of P1.T04's six
measured HCLK block cells.

## What `idx` is, and is not

`idx` is the **vendor's allocation order inside a block**, read off the
incremental sweep: each `n -> n+1` adds exactly one site, and the site it adds
is the next index. It is a *hypothesis* for `HCLK_IN{idx}` — the 138C carries
**zero fuse-bearing HCLK pips** (`gw5_hclk_idx` returns `-1`, P1.T05-T09
FINDINGS), so there is no fuse to read the multiplexer number off, and nothing
in this campaign proves the allocation order equals the multiplexer order.
`P1.T26` must consume it as an ordering, not as a proven mux index.

`idx measured = no` marks the three blocks whose four sites were first observed
together rather than one at a time (the sweep has no `n = 7..11, 13..15`
points). Their order is the canonical one the three measured blocks agree on,
`C2 -> C5 -> C7 -> D2`. Their **set** of four wires is measured; only the order
within the block is inferred.

## The shape `P1.T26` needs

```python
_dhcen_ce['GW5AST-138C'] = {
    'R': [(27, 181, 'C2'), (27, 181, 'C5'), (27, 181, 'C7'), (27, 181, 'D2'),
          (81, 181, 'C2'), (81, 181, 'C5'), (81, 181, 'C7'), (81, 181, 'D2')],
    'B': [(108,  64, 'C2'), (108,  64, 'C5'), (108,  64, 'C7'), (108,  64, 'D2'),
          (108, 117, 'C2'), (108, 117, 'C5'), (108, 117, 'C7'), (108, 117, 'D2')],
    'L': [(27,   0, 'C2'), (27,   0, 'C5'), (27,   0, 'C7'), (27,   0, 'D2'),
          (81,   0, 'C2'), (81,   0, 'A5'), (81,   0, 'C7'), (81,   0, 'A4')],
}
```

This is **eight entries per side over two blocks**, not the six-entry
single-block shape the GW1N/GW2A devices use, and there is no `'T'` key.
`fse_create_dhcen`'s `idx < 4 -> HCLK_IN{idx} else HCLK_BANK_OUT{idx-4}` rule
therefore does not carry over unchanged; `P1.T26` owns that decision.
