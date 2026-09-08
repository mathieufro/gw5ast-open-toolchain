# IODELAY shape-A sweep on GW5AST-138C

`P3.T21` (the sweep) and `P3.T22` (the decode). Shape `iodelay_a`: one
`IODELAY` on a 3.3 V bank-5 input ball (`AA9`, `IOB53A`, cell `(52,108)`),
`DO` captured in a flop, `SDTAP`/`VALUE` from pads, `DF` to a pad. 28 sweep
points: 24 `C_STATIC_DLY` values in Gray-code order, then `DYN_DLY_EN` and
`ADAPT_EN` false/true.

```
BATCH_COMPLETE p3-iodelay-a runs=28 ok=0 diff=16 aborted=12
```

## The `C_STATIC_DLY` fuse table (MEASURED, 28 vendor bitstreams)

Baseline `c-static-dly-0`, which sets **no** delay fuse at all. Every other
point adds exactly the bits of its own binary weight in tile `(52,108)`, row
21 — nothing else in the tile moves:

| `C_STATIC_DLY` bit | weight | fuse (row, col) |
|---|---|---|
| 0 | 1 | `(21, 3)` |
| 1 | 2 | `(21, 4)` |
| 2 | 4 | `(21, 5)` |
| 3 | 8 | `(21, 6)` |
| 4 | 16 | `(21, 7)` |
| 5 | 32 | `(21, 8)` |
| 6 | 64 | `(21, 9)` |
| 7 | **128** | `(21, 10)` |

All 24 points are consistent with it, including the ten that carry bit 7
(128, 129, 130, 131, 132, 134, 136, 140, 152, 192).

**This is not the pre-5A `DELAY_DEL` map.** The GW5AST-138C spends **one**
enumerated IOLOGIC attribute — number **118**, unnamed in the shipped
`attrids` table — on the whole 0-255 step, where GW1N/GW2A spend seven
one-bit attributes `DELAY_DEL0`-`DELAY_DEL6` (ids 32-38). Its value ids are
`2` for one step and `1000 + n` for every `n >= 2`; step 0 has no row. The
shortval table carries all 255 non-zero steps. So **`DELAY_DEL7` was never
the question**: bit 7 *is* fuse-backed on this die, and the refusal
`P3.T20` recorded ("needs `DELAY_DEL7`, which the IOLOGIC attribute table
does not have") is an artefact of reading the pre-5A window on a die that
does not use it. The attribute is now named `C_STATIC_DLY` in `attrids`,
and `gowin_unpack` recovers the step from any bitstream:

```
c-static-dly-1    IOLOGICA {'C_STATIC_DLY=1'}
c-static-dly-16   IOLOGICA {'C_STATIC_DLY=16'}
c-static-dly-64   IOLOGICA {'C_STATIC_DLY=64'}
c-static-dly-128  IOLOGICA {'C_STATIC_DLY=128'}
c-static-dly-152  IOLOGICA {'C_STATIC_DLY=152'}
```

## Dynamic and adaptive mode are fuse-backed too

`dyn-dly-en-true` moves **37** bits of the same tile (and clears `(0,65)`
and `(0,68)`); `adapt-en-true` moves **41**, a superset of the dynamic set
plus `(7,84)`, `(7,94)`, `(20,109)`, `(20,118)`. Both light six further
IOLOGIC attributes the shipped table does not name — ids 77, 78, 89, 106,
108 and 135, decoding as `ENABLE`/`ENABLE`/`ENABLE`/`INV`/`TRUE`. The two
`false` points are bit-identical to the baseline, so the deltas are the
modes' own. Naming those six is the next IODELAY task; the bit lists are in
`fuse-attribution.json`.

## Verdicts

| verdict | n | why |
|---|---|---|
| `diff` | 16 | 14 static points that build, plus `dyn-dly-en-false` and `adapt-en-false` |
| `aborted` | 12 | the 10 bit-7 points and the two `true` points: `gowin_pack` exits 1 on its own named refusal, which `openflow` records as a failed step rather than `verdict: refused` |

No point reaches `verdict: ok`, and the reason is **not** the delay value:
`cells` and `attrs` are 0 and `conns` is 1 on every built point. It is that
the open flow's whole IODELAY fuse set is the pre-5A one. Comparing the two
bitstreams' IO tile at four different steps gives the **same** difference
every time — the delta does not move with the sweep:

* vendor-only, constant: `(8,99) (8,100) (9,95) (9,96) (20,12) (20,20)
  (20,98) (21,80)`, plus that point's own delay bits;
* open-only, constant: `(2,38) (3,28) (3,29) (3,36) (3,107) (3,110) (8,57)
  (8,58) (9,53) (9,54) (9,106) (9,107) (9,109) (9,111) (21,49) (21,54)
  (21,66)`.

So `gowin_pack` writes **no** `C_STATIC_DLY` bit at all on this die (the
open set is identical at steps 0, 1, 16 and 64) and writes seventeen
enable-path bits the vendor does not. Closing the row at `E1` needs the
138C's IODELAY *enable* attributes attributed the same way this task
attributed the step — a packer task, and `P3.T22` may not touch
`gowin_pack.py`. **Named, measured, and open**, with the exact bit lists
above.

## Budget

49 oracle runs, against a 28-run allocation. The first 21 were spent on the
shape's original ball `N15` (`IOB146A`, ttyp 63) before the open half was
known to be impossible there: `chipdb.dat_portmap` builds a GW5A IOLOGIC
portmap only for a tile that carries an `IOBB`, so fourteen of this die's
326 IOLOGIC bels — ttyps 63, 64, 65, 86, 87, 251 — carry no ports at all,
and every open half aborted with "No wire found for port DF". Those 21 rows
are archived at `archive/runs-ttyp63-unmodelled.jsonl`; the ball moved to
`AA9` and the 28 were run again. **The phase is now 89/110 with ~32 runs of
allocation left — an overrun the owner should price.**

## Files

* `runs.jsonl` — the 28 measured rows.
* `fuse-attribution.json` — per point: every bit set in the scoped tile, the
  delta against the baseline, and the decoded IOLOGIC attributes
  (`tools/attribute_iodelay_fuses.py`).
* `archive/runs-ttyp63-unmodelled.jsonl` — the 21 rows on the unmodelled ball.
* Designs and logs: `$DATASTORE/p3t21b/`, batch log
  `evidence/_runs/p3-iodelay-a.log` (and `-ttyp63.log` for the first attempt).

| artefact | sha256 |
|---|---|
| `apycula/GW5AST-138C.msgpack.xz` | `df0ae17df04eeb3ce23a9edf56d37adcd5fc5d231ebccfc7fd1d3daf7613a958` |
| `chipdb-GW5AST-138C.bin` | `3df1431840852dbdb9f22953c584927d7f3e5bf259f902ff7cd8be5b53c82d18` |
| `nextpnr-himbaechel` | `084bbbfa61c1f2ff225640b80ce0440ba8ce45b2bb304ef295bf3729c318436e` (this task's build; the pair's `.bin` is unchanged -- no constids moved) |

## `P3.F2`: the packer emits the step, and the row's fuses close

**0 oracle runs.** Re-diffed with `tools/redo_open_half.py` against the 27
vendor bitstreams still on disk.

`gowin_pack` now spends the measured attribute instead of the pre-5A one:

* `GW5AST_138C.delay_step_attrs` emits **one** `C_STATIC_DLY`, by value id --
  `2` for step 1, `1000 + n` above it -- through
  `ChipDB.get_iologic_attr_val`, which now takes a numeric value the way
  `get_osc_attr_val` already does. The fuses come from the attribute-value
  table, never from a bit list, and the base class's `DELAY_DEL7` refusal does
  not apply here: bit 7 is fuse-backed on this die, so the ten points that
  used to abort now build.
* `GW5AST_138C.iodelay_enable_attrs` emits the enable set the vendor
  programs -- `INDEL` alone, fuse (20, 81) -- and not the inherited
  `CLKOMUX`/`IMARG`/`INDEL_0`/`INDEL_1`. Of those only `CLKOMUX` cost a fuse,
  (21, 54), one of the seventeen bits the open bitstream set on every point
  and the vendor's set on none.
* `DYN_DLY_EN` / `ADAPT_EN` stay **refused by name**. `P3.T21` measured their
  bits but not their meaning: both modes move six IOLOGIC attributes (77, 78,
  89, 106, 108, 135) the shipped table does not name, so neither is
  attributed and a guessed fuse is still worse than a refusal.

```
runs=28 ok=0 diff=25 aborted=3
```

| before (`P3.T21`) | after (`P3.F2`) |
|---|---|
| `ok` 0, `diff` 16, `aborted` 12 | `ok` 0, `diff` **25**, `aborted` **3** |
| `attrs` 0, `conns` 1, no `C_STATIC_DLY` bit written | `cells` 0, **`attrs` 0**, `conns` 8 (three points 1), 0 unexplained bits |
| 17 open-only bits at every step, constant | those are gone; the delay tile's attribute sets are identical |

The three that abort are named, not counted as failures: two are
`dyn-dly-en-true` and `adapt-en-true`, which the packer refuses by name, and
`p3-iodelay-a-iodelay_a-0018`'s vendor bitstream has been deleted from the
datastore, so its row is kept exactly as the oracle left it rather than
rebuilt without its oracle output (`redo_open_half --skip-missing-vendor`).

**The row does not reach `E1`, and the reason is no longer the delay line.**
`cells` 0, `attrs` 0 and no unexplained bit says the packer's IOLOGIC fuse set
now equals the vendor's at the delay tile. What is left is `conns`: the shape
carries a `DLYSTEP` counter in fabric that neither flow is constrained to
place identically, and the first difference of every point is the pad's own
`CE`/`O` port on a different net (`vendor=CE->net:VCC`,
`open=CE->net:<hash>`). The count went 1 -> 8 with `P3.F2`'s `EW10`/`W11`
wire alias, which is the alias working as intended: those differences were
previously hidden inside nets the decode had split in two.

Two decode items, both named:

* **Fixed.** `decode_check` `c1` compared the netlist's parameter as text
  against the recovered attribute, so `C_STATIC_DLY = 0…01` against `1` read
  as a mismatch on every point. `equiv._params_agree` now compares what the
  two spellings mean (`apicula tests/test_equiv_param_spellings.py`), and
  `c1_attr_mismatch` is empty on every point.
* **Open.** `c1` still reports `mismatch`: 8 of the 27 required cells are the
  shape's `ALU` cells, which `gowin_unpack` does not recover from the
  bitstream. That is an ALU decode gap this shape is the only one to exercise;
  it is unrelated to the delay line and is named here rather than folded into
  the row.

## The `conns` residual, closed by re-shape (`P3.T22`, `D105`)

The row's one open item was `conns` 8: `iodelay_a` drove `DLYSTEP` from a
fabric counter, and a counter is placed freely by each flow, so eight of the
delay cell's port nets carried two different endpoint digests for a reason
that had nothing to do with `IODELAY`. `D105` is the rule that closes it — *a
shape whose context cells the vendor renames must keep every net inside the
scope* — and `iodelay_a_balls` is that rule applied: the eight step bits come
off package balls, `DO` goes straight to a ball, and the design holds **no
fabric cell at all**.

**2 oracle runs** (`p3-iodelay-b`, ledger cumulative 100/140).

| point | level | verdict | cells / attrs / conns | decode c1 / c2 |
|---|---|---|---|---|
| `c-static-dly-0` | `E1` | ok | 0 / 0 / **0** | ok / ok |
| `c-static-dly-128` | `E1` | diff | 1 / 1 / 57 | ok / ok |

`conns` 8 -> **0**. The connectivity model was right; the residual was the
context, exactly as `D105` predicted, and the row's `E1` is now reached from
the bitstream-addressed bel with a real tile scope.

### And a new measured fact, which is why the row still does not close

At `c-static-dly-128` the two flows disagree by one cell and one attribute,
and the disagreement is the vendor's:

    tile (52,108) bel 0: cell vendor=<absent> open=IOLOGIC
    open  attrs: ('IOLOGIC', 0, 'C_STATIC_DLY', '128')
    vendor attrs: (none)

**The vendor programs no IOLOGIC fuse at all in that tile.** It kept the
primitive — `run.vg` and `run.vo` both instantiate `IODELAY dut` — and still
left the delay unprogrammed. The same `C_STATIC_DLY` values *are* programmed
by the vendor in `P3.T21`/`P3.F2`'s sweep, whose designs differ from this one
in exactly one respect: there the delayed output fed a fabric flop and a
counter drove `DLYSTEP`. So on this die the vendor's static delay is
**context-dependent** — an `IODELAY` whose output goes straight to a pad, in a
design with no clocked fabric, gets none — and a fabric-free shape therefore
cannot carry the delay line even though it is the only shape that can carry
the connectivity.

That is the row's measured reason for staying `E0`, and it replaces the old
one. The two halves are now proven separately: connectivity by
`iodelay_a_balls` (`conns` 0), fuses and attributes by `iodelay_a`
(`attrs` 0 on every built point, `P3.F2`). What no single Phase-3 shape has
yet shown is both at once. Naming the vendor's condition precisely enough to
build that shape is the open work.

### One decode gap fixed on the way

`nextpnr` puts an `IOLOGICI_EMPTY`/`IOLOGICO_EMPTY` half on an IOLOGIC site
when the design has no gearbox for that direction. Its configuration is
*nothing*, so no bitstream on any device decodes a cell at its site — the same
case as `IOLOGIC_DUMMY`, minus the main cell that stands in for it. Both
`equiv.bitstream_bel_exported` and `decode_check`'s `c1` now exempt it by
name; before, it read as a misplaced bel and a missing cell and held
`c-static-dly-0` at `E0` with `c1=mismatch`.

---

## The context rule, named (`p3-iodelay-c`, one run)

The section above left the row open on one question: *what*, exactly, does the
vendor need to see before it programs a static delay? The answer is one run.

`iodelay_a_clocked` is `iodelay_a_balls` with **one** change — the delayed
output is captured by a fabric flop clocked by the board oscillator, and the
harness writes a `create_clock` for it — and at the same `C_STATIC_DLY = 128`
the vendor now programs **bit `(21,10)` of tile `(52,108)`**, with `(21,3)`
through `(21,9)` clear. That is exactly the encoding of 128 in the fuse table
measured over 28 bitstreams at the top of this file, bit 7, weight 128.

> **A static delay is a timing quantity, and the vendor programs it only when
> the delayed net reaches a clocked fabric endpoint.** A pad-to-pad path has no
> endpoint for the delay to move, so the parameter is silently dropped.

That is the rule `P3.T25` measured the consequence of and could not name.

`cells` 0 and `attrs` 0: the open flow emitted the same configuration, so the
model is right in this context too. `conns` is 8, and the eight are the `D105`
residual and nothing else — the capture flop is placed freely by each flow, and
GowinSynthesis renames it, so `INS_LOC` cannot pin it (`P3.T12`, MEASURED).

So the row stays `E0`, now for a fully named reason, and the shape that would
close it is specified rather than guessed: it needs a clocked endpoint whose
placement **both** flows can be made to agree on. One further gap is named on
the way: in this context the vendor also sets `IOLOGIC` attribute id `133`,
which `apycula.attrids` does not name — `Unknown attr name for table: IOLOGIC
code:133`. It costs no bits in the comparison here (`attrs` 0) but it is an
unnamed vendor attribute on a die this epic ships, and it belongs in the
attribute table.
