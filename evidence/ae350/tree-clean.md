# Phase 2 close — the tree, in the ratified `V11` form

A raw `git status` in the pipeline worktree is **never** clean while the
pipeline runs: the Atelier harness writes `state.json`, `.await-since` and
`.heartbeat` continuously. So the check has two halves, and the raw output is
kept verbatim beside the filtered one — `tree-status-raw.txt` in this
directory — so the filter hides nothing. The exclusion list is **closed and
named**: exactly those three paths, no wildcards. Deleting them, or
`git add`-ing them to make the raw command pass, is forbidden and was not
done; the pipeline-doc commit `8cfba0a` deliberately left them out of its
own diff for that reason.

`<epic-base-sha>` = **`b001aec`** — `open-toolchain: Phase 1 (Clocking)
complete`, the `fine-line` commit on `main` this pipeline's branch
`atelier/open-toolchain-gw5ast` was cut from.

## 1. Raw, verbatim

```
$ git -C $FL status --porcelain
 M .atelier/pipelines/2026-09-03-open-toolchain-gw5ast-7e84/.heartbeat
```

Kept byte for byte in `tree-status-raw.txt` beside this file.

## 2. Filtered — must be empty, and is

```
$ git -C $FL status --porcelain | grep -vE '(state\.json|\.await-since|\.heartbeat)$'
$ echo $?
1
```

No output: `grep` exits 1 because it matched nothing, which is the passing
result. Nothing but the harness's own files is uncommitted.

## 3. What this phase moved

```
$ git -C $FL diff --name-only b001aec HEAD -- apicula nextpnr open-toolchain
apicula
nextpnr
open-toolchain
```

**Three gitlinks and nothing else.** The blueprint's form names two; the
third is `open-toolchain`, which became a submodule of this worktree at
`C10`/`D80` when the evidence tree and the `DEL-e` tools moved into it — so
every phase from 0 on bumps three, and the phase report records that as a
standing consequence of `C10`.

| gitlink | at the Phase-1 close | at the Phase-2 close | branch |
|---|---|---|---|
| `apicula` | `4a2accb` | `ebef8e9` | `epic/gw5ast138c` |
| `nextpnr` | `7dd337b` (Phase 1) | `97d54b3` | `epic/gw5ast138c` |
| `open-toolchain` | `71133cc` | the commit that carries this file | `main` |

Each pointer commit's own diff is gitlinks only — asserted by
`tools/tests/test_phase_branches_and_pointers.py::PointerCommitTest`, which
walks every `Submodule pointer:` commit since `b001aec` and fails if one
touches anything else.

## 4. Ordering, and the observer effect

Two things make recording a tree's cleanliness from inside that tree less
trivial than it looks, and both are stated rather than tidied away.

**The write is observed.** `git status --porcelain > tree-status-raw.txt`
redirects into the evidence tree, so the shell truncates the file — dirtying
the `open-toolchain` gitlink — *before* `git status` runs, and the output then
records that gitlink as modified. The capture therefore writes to a scratch
file first and the result is copied in, so what is recorded is the status as
it stood, not the status of recording it.

**One commit follows.** Storing the file is itself a commit, so a final
pointer bump follows it, and that bump is what leaves the tree in exactly the
state recorded above. There is no way to avoid this one-step tail, and
pretending otherwise would be the sort of tidying the `V11` form exists to
forbid.

## 5. Branches

Every `ae350/*` branch is an ancestor of its fork's `epic/gw5ast138c`, and
both forks' `epic/gw5ast138c` equals `origin/epic/gw5ast138c`:

- **apicula** — `bookkeeping`, `create`, `dat-scaledgrid`, `dualpins`, `e0`,
  `examples`, `gate-chipdb-pin`, `input-tail`, `ram-row`, `route`, `row`,
  `tile-wires`, `wire-map-reconcile` (all `-138c`)
- **nextpnr** — `ae350/e0-138c`, `ae350/route-138c`

Asserted by `MergedBranchTest::test_every_ae350_branch_is_merged`, which
walks the branch list rather than a written-down one, so a branch left behind
fails the test instead of going unnoticed.
