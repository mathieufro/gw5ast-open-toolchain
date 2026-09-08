# The on-die oscillator of the GW5AST-138C (`P3.T30`, `P3.T31`)

## Verdict: **the die has no oscillator. The vendor says so by name.**

`refused:ERROR (RP0008) : There is no OSCA resource in current device, please change device`

| run | primitive | vendor |
|---|---|---|
| `p3-osc-osc-0000` | `OSCA`, `FREQ_DIV=100` | refused, `RP0008` |
| `p3-osc-osc-0001` | `OSCA`, `FREQ_DIV=2` | refused, `RP0008` |
| `p3-osc-osc-0002` | `OSCB`, `FREQ_DIV=10` | refused, `RP0008` |

GowinSynthesis stops before place-and-route in all three; no `run.fs` is
written. Both oscillators the GW5A cell library declares were asked —
`OSCA(OSCOUT, OSCEN)` and `OSCB(OSCOUT, OSCREF, OSCEN, FMODE, RTRIM, RTCTRIM)`
(`cells_xtra_gw5a.v:1202-1215`) — and the die has neither. The `FREQ_DIV` sweep
the blueprint budgets is therefore **not** run: an axis of a primitive that does
not exist measures nothing, and the two unrun corners (`126`, `3`) stay in
`OSC_POINTS` marked unmeasured rather than being quietly dropped.

## What this settles in `chipdb.py`

`fse_create_osc` returns immediately for `{'GW5AT-60B', 'GW5AST-138C'}`
(`chipdb.py:4507-4509`). That early return is **correct**, and it is now correct
by measurement rather than by omission — the comment beside it says so and
quotes these three runs.

### The near-miss worth recording

The 138C `.fse` **does** carry the oscillator's `shortval` table 51: 63 rows, in
exactly one cell, `(108, 0)`, tile type 48. `P3.T30`'s stated method was "find
which cells carry OSC fuses in table 51 and create the bel there", and following
it literally would have produced a bel — in the bottom-left corner, from real
fuse rows — for a resource the vendor refuses to place. A fuse table in the
device file is evidence that the *family* has the block, not that this *die*
bonds it. That is the same class of error as reading a drifted `.dat` base: the
data parses, so nothing complains.

`GW5AT-60B` is untouched: it is out of this epic's scope and no run here says
anything about it.
