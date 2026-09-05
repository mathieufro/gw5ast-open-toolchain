# The local gate's single entry point for this repo (C12, D94, D95;
# supersedes C8/D75-D78's blocking pre-commit shape). `.githooks/pre-push`
# is the only hook: task-branch pushes get no gate; a push to
# main/dev/integration/epic spawns this gate detached at GATE_SCOPE=branch.
# A human/agent typing `make gate` invokes this same target -- there is
# exactly one definition of "green".

include gate.env

GATE_SCOPE ?= fast

# Every root below is derived from where THIS makefile is, so the gate runs
# from any checkout on any box (no hardcoded /Users/alex): this repo is a
# sibling of `apicula`/`nextpnr` under the pipeline worktree, which itself
# sits three levels below the umbrella (`fine-line/.atelier/worktrees/<slug>`),
# matching apicula's gate.mk derivation.
OTC := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
WORKTREE_DIR := $(patsubst %/,%,$(dir $(OTC)))
PIPELINE_SLUG ?= 2026-09-03-open-toolchain-gw5ast-7e84
PIPE_DOCS ?= $(WORKTREE_DIR)/.atelier/pipelines/$(PIPELINE_SLUG)
FL_ROOT ?= $(abspath $(WORKTREE_DIR)/../../..)
PYTHON ?= $(FL_ROOT)/vendor/venv/bin/python

.PHONY: gate _gate-fast _gate-branch _gate-full

gate:
	@case "$(GATE_SCOPE)" in \
	  fast)   $(MAKE) --no-print-directory _gate-fast ;; \
	  branch) $(MAKE) --no-print-directory _gate-branch ;; \
	  full)   $(MAKE) --no-print-directory _gate-full ;; \
	  *) echo "GATE $(GATE_SCOPE): unknown GATE_SCOPE (legal: fast branch full)"; exit 1 ;; \
	esac

# fast: unit tests only -- this repo's own tool tests (check_criteria.py /
# check_evidence.py / gate_status.py self-tests). Builds no bitstream,
# touches no evidence.
_gate-fast:
	@echo "GATE fast: pytest tools/tests"
	@$(PYTHON) -m pytest $(OTC)/tools/tests -q || { echo "GATE fast: pytest FAILED"; exit 1; }
	@echo "GATE fast: ok, 1 check"

# branch: fast, plus the evidence/criteria tools run for real against the
# live table (C12/D94: this is the scope the detached pre-push gate runs on
# main/dev/integration/epic pushes).
_gate-branch: _gate-fast
	@echo "GATE branch: check_evidence.py"
	@$(PYTHON) $(OTC)/tools/check_evidence.py $(PIPE_DOCS)/spec-primitives.md $(OTC)/evidence || { echo "GATE branch: check_evidence.py FAILED"; exit 1; }
	@echo "GATE branch: check_criteria.py --phase 0"
	@$(PYTHON) $(OTC)/tools/check_criteria.py $(PIPE_DOCS)/spec-primitives.md $(OTC)/evidence --phase 0 || { echo "GATE branch: check_criteria.py FAILED"; exit 1; }
	@echo "GATE branch: ok, 3 checks"

# full: everything, including heavy checks -- orchestrator-only, run in the
# foreground at phase close / pre-merge, never from a hook. No additional
# checks owned by this repo yet.
_gate-full: _gate-branch
	@echo "GATE full: ok, 3 checks (no additional checks yet)"
