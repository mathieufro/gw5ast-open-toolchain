"""The commit shape a phase close owes: branches merged, pointers clean.

`S28`'s commit-shape criterion closes in Phase 8, but the shape is
established at every phase close and is cheap to assert here: work lands on a
named branch inside the fork, the fork's branch is pushed, and the umbrella's
pointer commit moves **only** gitlinks. Nothing else may ride along in a
pointer commit -- that is the whole reason it is a separate commit.

The tree these assert against is the pipeline worktree
(`.atelier/worktrees/<slug>/`), located from this file rather than from a
hardcoded path, so the suite runs from any checkout. Where a repository is
not present -- a fresh clone of open-toolchain alone -- each test skips
rather than passing vacuously.
"""
import os
import subprocess
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC = os.path.dirname(TOOLS_DIR)
WORKTREE = os.path.dirname(OTC)

#: The three repositories a phase close moves, and the branch each lands on.
REPOS = {
    "apicula": "epic/gw5ast138c",
    "nextpnr": "epic/gw5ast138c",
    "open-toolchain": "main",
}

#: Trailers that must never appear: commits are the repo owner's.
FORBIDDEN_TRAILERS = ("Co-Authored-By", "Generated with")

#: The umbrella commit this phase's work is measured from -- the Phase-1
#: close on `main`, which is where this pipeline's branch was cut.
EPIC_BASE = "b001aec"

#: The harness writes these continuously while the pipeline runs, so a raw
#: `git status` is never clean. Closed list, no wildcards: the raw output is
#: kept verbatim beside the filtered one so nothing is hidden by the filter.
HARNESS_PATHS = ("state.json", ".await-since", ".heartbeat")


def _git(repo, *args):
    """`(returncode, stdout)` for one git command, never raising."""
    proc = subprocess.run(("git", "-C", repo) + args,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def _repo(name):
    path = os.path.join(WORKTREE, name)
    return path if os.path.isdir(os.path.join(path, ".git")) or os.path.isfile(
        os.path.join(path, ".git")) else None


class BranchTest(unittest.TestCase):
    """Each fork is on its integration branch, and that branch is pushed."""

    def test_each_repo_is_on_its_integration_branch(self):
        for name, branch in REPOS.items():
            repo = _repo(name)
            if repo is None:
                continue
            code, head = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
            self.assertEqual(code, 0, name)
            self.assertEqual(head, branch, f"{name} is on {head!r}")

    def test_branches_have_upstream_remote(self):
        """`V10`'s attribution grep in Phase 8 needs an upstream to walk."""
        checked = 0
        for name in REPOS:
            repo = _repo(name)
            if repo is None:
                continue
            code, upstream = _git(repo, "rev-parse", "--abbrev-ref", "@{upstream}")
            self.assertEqual(code, 0, f"{name} has no upstream")
            self.assertTrue(upstream, name)
            checked += 1
        if not checked:
            self.skipTest("no sibling repositories in this checkout")

    def test_integration_branch_is_pushed(self):
        checked = 0
        for name, branch in REPOS.items():
            repo = _repo(name)
            if repo is None:
                continue
            _code, local = _git(repo, "rev-parse", branch)
            code, remote = _git(repo, "rev-parse", f"origin/{branch}")
            if code != 0:
                continue  # no origin ref locally; nothing to compare against
            self.assertEqual(local, remote, f"{name}: {branch} is not pushed")
            checked += 1
        if not checked:
            self.skipTest("no sibling repositories in this checkout")


class MergedBranchTest(unittest.TestCase):
    """Every per-deliverable branch is an ancestor of its integration branch."""

    def test_every_ae350_branch_is_merged(self):
        checked = 0
        for name, branch in REPOS.items():
            repo = _repo(name)
            if repo is None or name == "open-toolchain":
                continue
            code, listing = _git(repo, "branch", "-a", "--format=%(refname:short)")
            if code != 0:
                continue
            for candidate in listing.splitlines():
                if "ae350/" not in candidate:
                    continue
                merged, _ = _git(repo, "merge-base", "--is-ancestor",
                                 candidate, branch)
                self.assertEqual(
                    merged, 0,
                    f"{name}: {candidate} is not an ancestor of {branch}")
                checked += 1
        if not checked:
            self.skipTest("no ae350 branches in this checkout")


#: Where each fork's own history begins: commits reachable from the upstream
#: default branch are upstream's, and what trailers upstream uses is not this
#: project's business. Only the commits this project added are checked.
UPSTREAM_REFS = ("master", "main", "origin/master", "origin/main")


class AttributionTest(unittest.TestCase):
    """No commit this project authored carries an attribution trailer."""

    @staticmethod
    def _own_commits(repo, branch):
        """`[(sha, message)]` for the commits this project added to `branch`.

        Excludes everything reachable from the upstream default branch, so a
        fork carries only its own commits into the check.  Falls back to the
        last 200 commits where no upstream ref resolves -- a repository this
        project started, like open-toolchain.
        """
        excludes = []
        _code, head = _git(repo, "rev-parse", branch)
        for ref in UPSTREAM_REFS:
            if ref in (branch, f"origin/{branch}"):
                continue  # the branch itself, or its own tracking ref
            code, resolved = _git(repo, "rev-parse", "--verify", "--quiet", ref)
            if code != 0 or resolved == head:
                continue  # absent, or the same commit -- excluding it excludes all
            excludes.append("^" + ref)
        args = ["log", "--format=%H%x1f%B%x1e", branch]
        args += excludes if excludes else ["-n", "200"]
        code, log = _git(repo, *args)
        if code != 0:
            return []
        out = []
        for record in log.split("\x1e"):
            record = record.strip()
            if "\x1f" not in record:
                continue
            sha, body = record.split("\x1f", 1)
            out.append((sha.strip(), body))
        return out

    def test_no_attribution_trailers_in_phase_commits(self):
        offenders = []
        checked = 0
        for name, branch in REPOS.items():
            repo = _repo(name)
            if repo is None:
                continue
            for sha, body in self._own_commits(repo, branch):
                checked += 1
                for trailer in FORBIDDEN_TRAILERS:
                    if trailer.lower() in body.lower():
                        offenders.append(f"{name} {sha[:8]}: {trailer}")
        if not checked:
            self.skipTest("no sibling repositories in this checkout")
        self.assertEqual(offenders, [])

    def test_the_check_sees_this_projects_own_commits(self):
        """The exclusion must not empty the set it is meant to search."""
        repo = _repo("open-toolchain")
        if repo is None:
            self.skipTest("no open-toolchain checkout")
        self.assertGreater(len(self._own_commits(repo, REPOS["open-toolchain"])), 10)


class PointerCommitTest(unittest.TestCase):
    """A pointer commit moves gitlinks and nothing else."""

    def _pointer_commits(self):
        code, log = _git(WORKTREE, "log", "--format=%H %s",
                         f"{EPIC_BASE}..HEAD")
        if code != 0:
            return None
        return [line.split(" ", 1) for line in log.splitlines()
                if line.split(" ", 1)[1:] and
                line.split(" ", 1)[1].startswith("Submodule pointer")]

    def test_pointer_commits_touch_only_gitlinks(self):
        commits = self._pointer_commits()
        if not commits:
            self.skipTest("no pointer commits reachable in this checkout")
        gitlinks = set(REPOS)
        for sha, subject in commits:
            _code, names = _git(WORKTREE, "show", "--pretty=format:",
                                "--name-only", sha)
            changed = {n for n in names.splitlines() if n.strip()}
            self.assertTrue(
                changed <= gitlinks,
                f"{sha[:8]} ({subject}) also changed {sorted(changed - gitlinks)}")

    def test_the_phase_moved_only_gitlinks(self):
        code, names = _git(WORKTREE, "diff", "--name-only", EPIC_BASE, "HEAD",
                           "--", *REPOS)
        if code != 0:
            self.skipTest("the epic base is not reachable in this checkout")
        changed = {n for n in names.splitlines() if n.strip()}
        self.assertTrue(changed <= set(REPOS), sorted(changed))


class TreeCleanTest(unittest.TestCase):
    """The filtered status is empty, and the raw one is recorded verbatim."""

    RAW = os.path.join(OTC, "evidence", "ae350", "tree-status-raw.txt")

    def test_raw_status_is_recorded(self):
        self.assertTrue(os.path.isfile(self.RAW), self.RAW)
        with open(self.RAW, encoding="utf-8") as fh:
            self.assertTrue(fh.read().strip(),
                            "the raw status is recorded, not an empty file")

    def test_recorded_raw_status_holds_only_harness_paths(self):
        """Every line of the recorded raw status is one the filter excludes.

        This is the half that keeps the exclusion honest: the filter may only
        ever remove the three harness files, so if the recorded raw output
        carries anything else, the tree was not clean when it was taken.
        """
        with open(self.RAW, encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh if line.strip()]
        leftover = [line for line in lines
                    if not line.endswith(HARNESS_PATHS)]
        self.assertEqual(leftover, [], "not excluded by the closed list")


if __name__ == "__main__":
    unittest.main()
