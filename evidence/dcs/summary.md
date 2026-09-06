# `evidence/dcs/` — P1.T28 summary (DCS half)

**This row is the tile-type cross-reference, not the full DCS sweep** (that
is P1.T31/T32). See `tiles-138c.md` + `tiles-138c.json`.

## Row

No separate oracle campaign — derived from the DQCE 8-run probe
(`evidence/dqce/`), since DCS searches the identical 4 grid values.

## Sweep

No sweep of this row's own: the 4 grid values are read from the DQCE 8-run
probe recorded in `evidence/dqce/`, so this row varies nothing itself. The
DCS sweep proper is `P1.T31`/`P1.T32`.

## Verdict

Same 4 cells as DQCE: 3 confirmed live (80, 84, 85), 1
unconfirmed-but-unrefuted (81). DCS's own port-table trace and quadrant
allow-list fix are P1.T31's job, not this task's.

## Artefacts

`tiles-138c.md`, `tiles-138c.json`.
