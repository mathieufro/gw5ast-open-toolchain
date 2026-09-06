# GW5A-25A support status — measured fact (P1.T44)

Date: 2026-09-06. Branches measured: apicula `integration/p1-clocking` @ `4232744`
(worktree `apicula-wt/t44`, detached from `origin/integration/p1-clocking`), nextpnr
`integration/p1-clocking` @ `527c7169` (worktree `nextpnr-wt/integ`). Read-only probing
only; no source edited in either fork.

## 1. Chipdb build

`python -m apycula.chipdb_builder GW5A-25A` on the installed Standard 1.9.12.03
(`GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA`): **exit 0**, no
`FseShapeError`/`KeyError` (the `P0.T15` failure class is gone, consistent with `P0.T13b`
onward). Output `GW5A-25A.msgpack.xz`, 321,484 B,
`sha256 6311219d52b996b8431d573cd5c547426370db00852aed285033a19a5518c3ca` — matches the
`6311219d…` value every `ws_01` task (`P1.T07`,`T08d`,`T21`,`T22`,`T26`,`T38a`) has recorded
as unchanged since `P0.T40`. **Fact: GW5A-25A's chipdb is byte-identical across every
`ws_01` clocking commit measured so far; the clocking branches carry no unguarded
regression on this device's chipdb.**

## 2. nextpnr `.bin` + smoke

Built a matching `.bin` from that chipdb with the installed nextpnr's own tools
(`himbaechel/uarch/gowin/gowin_arch_gen.py -d GW5A-25A` → `bba/bbasm --l`), both from
`nextpnr-wt/integ`: `chipdb-GW5A-25A.bin`, 17,513,391 B,
`sha256 1c16b7b8c279976619bcf0ff1fc4e530f7f73941d65594deb7b11c2755df1598`, installed
locally at `nextpnr-wt/integ/build/share/himbaechel/gowin/` (worktree-local only, not the
shared `$DATASTORE` install).

- `nextpnr-himbaechel --device GW5A-LV25MG121NC1/I0 --chipdb <that .bin> --test` (a valid
  package at grade `C1/I0`, present in the chipdb's `packages` dict): **exit 0**, full
  architecture DB integrity check passes cleanly.
- `nextpnr-himbaechel --device GW5A-LV25MG121NES --chipdb <that .bin> --test` — this is the
  **exact device string `examples/gw5a/Makefile` uses for every `primer25k` target**:
  **`ERROR: Speed grade 'ES' not found in database.`** (uarch resolves to `gowin`, package
  lookup succeeds, only the grade lookup fails).

Root cause traced in `apycula/chipdb.py`: no code path anywhere in the chipdb builder (or
in the fork's chipdb.py changes, `62` `GW5A-25A` occurrences today vs `55` at upstream
`3328095`) ever populates an `'ES'`-keyed entry in `db.timing`; the built chipdb's `timing`
dict has exactly `{'C1/I0', 'C2/I1', 'unidentified_1', 'unidentified_2'}` for GW5A-25A — no
device has an `ES` timing model. On the nextpnr side, `gowin.cc`'s package/grade parser
(the block at `gowin.cc:203-220` handling the `ES`-suffix case) is **byte-identical** to
`nextpnr@8dbcee5c` (upstream base pin, `P0.T07`) — this is a pre-existing upstream
limitation, not something introduced by this fork's HCLK/PLL/DHCE clocking work. The only
fork change in that file is the postRoute `hclk_up_wire` table (6 rows for the 6-block
138C vs 4 for 25A, table-driven, device-generic) — unrelated to speed-grade resolution.

**Fact: the vendor-spec'd `primer25k` device string (`GW5A-LV25MG121NES`) cannot reach
place-and-route today on either the fork or upstream nextpnr — the block is upstream
apicula's chipdb never emitting an `ES` timing model, not a regression from this phase's
work.**

## 3. Representative `primer25k` example builds

`examples/gw5a/Makefile` primer25k targets (from the `primer25k:` rule, 39 total `.fs`
targets): `in-out`, `in-inv-out`, `in-or-inv-out`, `lut8`, `big-shift`, `alu-simple`,
`lutram`, `blinky-osc`, `pll7`, `dcs`, 12 `bsram-*` variants, 3 `femto-riscv-*`, 4
`dsp-*`, 3 `adc-*`, `attosoc`, 10 IO-serdes variants (`oddr`/`oser*`/`iddr*`/`ides*`/
`ivideo`/`ovideo`), all built via the same two-stage rule: `yosys → nextpnr-himbaechel
--device GW5A-LV25MG121NES → gowin_pack -d GW5A-25A`.

Three representative targets built through the unmodified Makefile recipe (yosys 0.63,
the installed nextpnr binary, `--chipdb` pointed at the `.bin` from §2 by installing it
into `nextpnr-wt/integ/build/share/himbaechel/gowin/`, no other Makefile edits):

| target | primitive class | yosys | nextpnr | gowin_pack | exit |
|---|---|---|---|---|---|
| `lut8-primer25k` | LUT/DFF | OK (313 cells) | **`ERROR: Speed grade 'ES' not found in database.`** | not reached | 2 |
| `bsram-DPB-primer25k` | BSRAM | OK | same `ES` error | not reached | 2 |
| `pll7-primer25k` | PLL | OK | same `ES` error | not reached | 2 |

All three fail identically, at the identical point (nextpnr device init, before any
placement work begins), with the identical error text. Logs: `build-lut8.log`,
`build-bsram.log`, `build-pll7.log` (paths recorded in the evidence row, §5).

No vendor (`gw_sh`) comparison runs were used (0 of the ≤3 budget): since the open flow
never reaches a bitstream for any of the three targets, there is nothing yet to compare
against a vendor oracle build, and spending oracle-run budget on it would not add
information over the point already established (pre-existing upstream gap, not a
regression this phase caused).

## 4. Fork vs upstream: GW5A-25A-affecting code paths

- `apycula/chipdb.py`: `62` `GW5A-25A`-gated lines today vs `55` at upstream `3328095`
  (+7 net; consistent with `PROGRESS.md`'s `P0.T13b`/`T35`/`T36` device-gated fixes —
  drpfuse width, ADC absence, `.tm` de-alias — plus this phase's HCLK/PLL/DHCE work, all
  already-landed and not re-verified line-by-line here per the task's read-only scope).
- `apycula/chipdb_builder.py` (+5 lines) and `apycula/gowin_pack.py` (+6 lines) carry the
  matching device-gated adjustments.
- `himbaechel/uarch/gowin/gowin.cc`: 26 insertions / 8 deletions vs `nextpnr@8dbcee5c`,
  entirely the `postRoute` HCLK up-wire table generalised from 4 hardcoded blocks to a
  6-row, block-count-agnostic table (`P1.T10`). The speed-grade/package-resolution block
  (§2 above) is untouched, byte-identical to upstream.
- No GW5A-25-only (as opposed to GW5A-25A) gate exists in either fork; `constids.inc`/
  `cst.cc`/`pack*.cc` device gates found by grep are all keyed on the family strings
  already catalogued in `grounding-facts.md` §5/§9 (`GW5A-25A`, `GW5AT-60B`,
  `GW5AST-138C`) — none reference a bare `GW5A-25` or `GW5A` string that would imply a
  second, distinct part.

## 5. Fact table

| # | question | answer | evidence |
|---|---|---|---|
| 1 | Does GW5A-25A's chipdb build today? | **Yes**, exit 0, deterministic | §1, sha256 `6311219d…` |
| 2 | Does the vendor-spec'd device string route today? | **No** — `ES` speed grade absent from the chipdb's timing table | §2 |
| 3 | Is that a regression from this phase's clocking work? | **No** — byte-identical to upstream `nextpnr@8dbcee5c`'s grade-parsing code; apicula never builds an `ES` timing model for any device | §2, §4 |
| 4 | Do representative LUT/DFF, BSRAM, PLL examples build end to end? | **No**, all 3 fail identically at the nextpnr device-init step | §3 |
| 5 | Does a non-`ES` grade of the same package route? | **Yes** — `GW5A-LV25MG121NC1/I0` passes nextpnr's full architecture integrity check | §2 |

Evidence row: `open-toolchain/evidence/chipdb/runs.jsonl`, `run_id
p1-t44-gw5a25a-status-0001`, `verdict: refused`, `level: E0`, notes carries the exact
nextpnr error text and the cross-reference to the upstream-identical code path (`D30`
convention: a refusal is a recorded deliverable).
