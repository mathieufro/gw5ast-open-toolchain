# P1 clocking — checkpoint

## Entry

- Edition: 1.9.12.03 Standard
- installs_available: 1
- edu-provisional: false
- gowinhome.selected: /Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
- chipdb sha256 (apycula/GW5AST-138C.msgpack.xz): fd1d112d0c463d9e7ba918b0651cac0c9b4e90dac392ae36e8cec297bf9ee2bb
- Full detail: $OTC/evidence/_runs/p1-entry.log

## Oracle runs (D62 box = 290 for Phase 1)

| task | runs | cumulative | ledger |
|---|---|---|---|
| P1.T04 | 14 | 14 | `$OTC/evidence/clocking/oracle-runs.jsonl` (13 rows in the batch ledger + 1 exploratory `clkdiv24` recorded in `hclk-topology.md` §9) |

P1.T03's `$OTC/evidence/_budget/clocking-runs.tsv` did not exist when P1.T04
ran; T04's rows are in `evidence/clocking/oracle-runs.jsonl` per the task
instruction. Whoever lands T03 must fold this row into the .tsv, not
re-count it.
