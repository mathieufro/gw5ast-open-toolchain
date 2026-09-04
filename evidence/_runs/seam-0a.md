# Seam 0a verdict — P0.T17

Run 2026-09-04, foreground, worktree /Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84 on branch atelier/open-toolchain-gw5ast.

apicula fork: epic/gw5ast138c @ 33e2148 (origin, pushed). nextpnr: unchanged @ 8dbcee5.
Worktree pointer bump commit: a447a9c (apicula gitlink 2f1dec7 -> 33e2148), pushed to origin/atelier/open-toolchain-gw5ast.

S1 pass
S2 pass
S3 pass
S28-creation pass
edu-provisional: true

## V1 (S28, forks are submodules)
- two submodule lines (apicula @ 33e2148ef805897d0da4bc34df8b54e5f04d3e36, nextpnr @ 8dbcee5c3c4415770b6fd06d5ccb2db89545b8ec), no +/- prefix (worktree matches index)
- `.gitmodules` apicula path/url block present, url = git@github.com:mathieufro/apicula.git
- OK-vendor-clean ($FL/vendor/apicula and $FL/vendor/nextpnr absent)

## V2 (S1/S3, six chipdb builds)
GOWINHOME_STD=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
GOWINHOME_EDU=/Users/alex/Desktop/GowinIDE.app/Contents/Resources/Gowin_EDA
venv: /Users/alex/fine-line/vendor/venv (resolves to worktree apicula @ 33e2148)
No FAIL line. Six builds, six sha256s (match P0.T15 evidence):
- std GW5AST-138C ab1339e4cfb6d58cd5f646fca35d42b9a4b53b629c0edf27dd7ae1e9702bb88d
- std GW5A-25A    fa431045b35965ca96ed829dfebe7931ebc1bcab8563c084675bbafcc1b5a12e
- std GW5AT-60B   5a921a831b923899d03a70ce1791f0d938d8fb7c7794608a55e3cec0527acf18
- edu GW5AST-138C c80837c522ae6bec65f4d2cb9b8f3e4fcb24aad64bc48f6c709432cecf663728
- edu GW5A-25A    7f366f87ec53a244824e04f6ab03ba1b001f25af03a541b2b20ae69197531d5d
- edu GW5AT-60B   4ae3c57356e059b147394213282d7fbd4f55dffc0b2f9221484dd5f4b673ed2c

## V3 (S2, no opaque parser failure)
`cd $FL/apicula && python -m pytest tests -k "fse_version" -q` with GOWINHOME=$GOWINHOME_EDU,
DYLD_LIBRARY_PATH/DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib exported: 11 passed, 78 deselected.
(Without GOWINHOME exported, ide_version resolves to "unknown" and 2 of the 11 fail —
GOWINHOME must be set for this test to run correctly; recorded, not a defect since the
task env section requires it for anything touching the installed .fse files.)

## Done-when tests
- test_seam_0a_all_pass: 4 criterion lines, 0 lines ending in `fail` — confirmed above.
- test_no_attribution_trailers_apicula_branch:
  `git -C $FL/apicula log upstream/master..HEAD --format=%B | grep -Eic 'Co-Authored-By|Generated with'` = 0

## Deviation
No `make gate` / pre-commit/pre-push hooks exist yet (P0.T41-T43 not yet landed — they are
scheduled to run immediately after P0.T07 per the blueprint's declared execution order, but
have not been executed by this loop as of this task). The commit above was made without a
local gate hook firing. Recorded per LOOP-BRIEF guidance to run the equivalent explicit
validation commands (V1/V2/V3 above) in their place and note the deviation rather than
inventing a gate.
