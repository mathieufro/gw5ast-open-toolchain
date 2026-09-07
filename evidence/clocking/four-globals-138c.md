# Four independent global clock nets on the GW5AST-138C (`P1.F3`)

`P1.T40` recorded, without diagnosing it, that four independent global clock
nets break nextpnr. They do. This is what actually happens and why.

## 1. Reproduction — the smallest design that shows it

`$DATASTORE/batch/p1f3-open/c-4globals/`: four input pins, four flops, one
flop per pin, nothing else. `yosys -p 'synth_gowin -family gw5a'` promotes
each clock to a `BUFG`. Against the pair the gaps were measured on
(binary `cfc97099…`, `.bin` `d700cade…`):

```
Info: Routing globals...
Warning: Failed to route net 'clk3_IBUF_I_O' from X91Y99/CLK1 to X76Y107/CLK0 using dedicated routing.
ERROR: Can't route the clk3_IBUF_I_O net. It might be worth removing the BUFG buffer flag.
1 warning, 1 error
```

## 2. It is not capacity, and it is not the fourth net

`--verbose` names the net being routed before each attempt, and the only line
printed is `route buffered net 'clk3_IBUF_I_O'`: the **first** buffered net
handled is already refused, with every spine on the die still free. So the
failure has nothing to do with there being four of them — four is simply the
number at which the placer is bound to get one of them wrong.

The same design with the four clocks going to four `CLKDIV`s pinned to the
four lanes of block 5 (`$DATASTORE/batch/p1f3-open/c-4div/`) routes and exits
`0` on the same pair. Four independent global nets are not the problem.

## 3. Root cause — a `BUFG` bel is a logic-to-clock gate, and gates are local

`chipdb.add_buf_bel` puts a `BUFG` bel on every logic-to-clock gate wire, 24
per half of the clock plane. `globals.cc route_buffered_net` routes the net
from the buffer's `I` wire, i.e. from that gate — and a gate drives only the
spines its own `.fse` rows list, which is a part of the plane, not all of it.
`X91Y99/CLK1` is one such gate; `X76Y107/CLK0` is a load it cannot reach.

nextpnr's placer has no cost term for that: `BUFG` bels are interchangeable as
far as placement is concerned, so which gate a buffer lands on is arbitrary.
With one or two buffers the draw is usually kind; with four it is not.

## 4. A second defect the first one was hiding

`route_buffered_net` routes the net in two legs: after the buffer from the
buffer's `I` wire, then before it from the true source **to** that wire. The
second leg's binding loop stops "when it hits already-bound routing" — and the
wire it starts from is exactly the wire the first leg already bound. So the
second leg can report success and bind **nothing**, leaving the net with two
disconnected trees: the driver's wire on its own, and everything from the
buffer's gate onwards.

Nothing in the global router notices. What notices is `TimingAnalyser::
get_route_delays`, which walks a sink back to the source wire and never gets
there: with the buffer moved but the legs disconnected the run does not fail,
it **hangs** — 10+ minutes at `Setting up routing queue`, 98 % CPU, the whole
sample in `Context::getNetinfoRouteDelay`. That is the same inconsistency
`router1.cc:347`'s `log_assert(net_info->wires.count(wire))` fires on in a
build with assertions, which is the form `P1.T40` saw.

## 5. The change — `himbaechel/uarch/gowin/globals.cc`

* `route_buffered_net` now routes **both legs or neither**, and if the buffer's
  own gate cannot serve both, it moves the buffer: every other free `BUFG` bel
  whose `I` wire is not already taken is tried, the net is ripped up between
  attempts, and the original bel is restored if none works. A placement repair
  made at the only point where the information exists.
* `global_route_is_connected` walks every sink back to the driver's wire over
  the bound routing. A net that does not pass is ripped up and left to the
  ordinary router — slower than dedicated routing and always correct — instead
  of being handed on in a state that later loops. Nothing else in the file may
  leave a global net half-bound again without this catching it.

Both are needed: with only the first, this design still hangs; with both it
builds. MEASURED, same design, same pair:

```
Info:     'clk2_IBUF_I_O' net was routed but not connected end to end; leaving it to the router.
Warning: Routing the clk2_IBUF_I_O net with the ordinary router: no clock gate reaches both its source and its loads.
Info: Program finished normally.
```

`nextpnr` exit `0` in 12 s, against `ERROR: Can't route the clk3_IBUF_I_O net`
on the pre-fix pair.

## 6. Verdict

Shape `clocking_four_globals`: the four buffered clocks that break it, plus one
`CLKDIV` on block 5 lane 0 pinned on both sides so the comparison has a
fuse-backed scope. MEASURED on the pre-fix pair: `ERROR: Can't route the
clk0_IBUF_I_O net`, exit 125. The batch line and the `EQUIV` line are in
`summary.md` §6.
