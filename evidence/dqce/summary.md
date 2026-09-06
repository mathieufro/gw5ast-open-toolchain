# `evidence/dqce/` — P1.T28 summary

**This row is the tile-type re-derivation, not the full DQCE sweep** (that
is P1.T29/T30). See `tiletypes-138c.md` + `tiletypes-138c.json` for the
full artefact.

## Row

8 oracle runs (`p1-dqce-types`, `evidence/_runs/p1-dqce-types.log`), all
`verdict=ok`, 0 aborted. Ledger: `runs/oracle-runs.jsonl`.

## Sweep

`n_dqce = 1..4` simultaneous `DCE` instances, two CE-assignment sequences
(A, B) — `fuzz.gw5ast138c.shapes.clocking_dqce_probe.PLAN`.

## Verdict

3 of 4 grid-derived 138C tile-type cells (80, 84, 85) confirmed live by
presence-diff; the 4th (81) unconfirmed-but-unrefuted (needs a
>=6-instance, spine-distinct design, out of this task's budget). See
`tiletypes-138c.md`.

## Artefacts

`tiletypes-138c.md`, `tiletypes-138c.json`, `runs/oracle-runs.jsonl`,
`_runs/p1-dqce-types.log`.
