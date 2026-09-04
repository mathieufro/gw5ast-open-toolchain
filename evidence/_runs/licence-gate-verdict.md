GATE OPEN (Standard 1.9.12.03, licensed)

- Standard 1.9.12.03 (`/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA`): PASS
  (re-run 2026-09-04 as P0.T05b, after the node-locked licence landed)
- Education 1.9.11.03 (`/Users/alex/Desktop/GowinIDE.app/...`): install removed 2026-09-04
  — not re-run; `licence-gate-edu.log` is retained as the historical 2026-09-04 record.

Verbatim `TCL_ALIVE` line from `licence-gate-std.log` (this run):
> TCL_ALIVE 8.6.4

Selection (owner constraint C9, decision D79): `gowinhome.selected` =
`/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA`, `edu-provisional.flag` = `false`.
Standard is GOWINHOME for everything from now on; the Education install no longer exists on
disk. Parser tests that need 1.9.11 device files read the archived bare device tree
`$DATASTORE/ide-share-device/edu-1.9.11.03/<dev>/<dev>.fse` (no gw_sh available there).

Superseded: the 2026-09-04 morning verdict `GATE DEFERRED (Education 1.9.11.03,
edu-provisional)`, recorded when Standard printed
`License verification failed  Connection timeout.` (F64/D52). That failure is now cleared by
measurement, not worked around: no patched binary, no Docker, no 1.9.10.03 install
(C2, C3, D2, D25b).
