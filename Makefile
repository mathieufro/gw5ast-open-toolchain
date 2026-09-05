# The local blocking gate's single entry point for this repo (S23b closure,
# C8, D75-D77). `pre-commit`, `pre-push` and a human/agent typing `make
# gate` all invoke this same target -- there is exactly one definition of
# "green".

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

.PHONY: gate _gate-fast _gate-full _gate-all

gate:
	@case "$(GATE_SCOPE)" in \
	  fast) $(MAKE) --no-print-directory _gate-fast ;; \
	  full) $(MAKE) --no-print-directory _gate-full ;; \
	  all)  $(MAKE) --no-print-directory _gate-all ;; \
	  *) echo "GATE $(GATE_SCOPE): unknown GATE_SCOPE (legal: fast full all)"; exit 1 ;; \
	esac

# fast: this repo's own tool tests, check_evidence.py, check_criteria.py
# --phase 0 against the live table. Builds no bitstream.
_gate-fast:
	@echo "GATE fast: pytest tools/tests"
	@$(PYTHON) -m pytest $(OTC)/tools/tests -q || { echo "GATE fast: pytest FAILED"; exit 1; }
	@echo "GATE fast: check_evidence.py"
	@$(PYTHON) $(OTC)/tools/check_evidence.py $(PIPE_DOCS)/spec-primitives.md $(OTC)/evidence || { echo "GATE fast: check_evidence.py FAILED"; exit 1; }
	@echo "GATE fast: check_criteria.py --phase 0"
	@$(PYTHON) $(OTC)/tools/check_criteria.py $(PIPE_DOCS)/spec-primitives.md $(OTC)/evidence --phase 0 || { echo "GATE fast: check_criteria.py FAILED"; exit 1; }
	@echo "GATE fast: ok, 3 checks"

# full: no additional checks owned by this repo yet -- identical to fast.
_gate-full: _gate-fast
	@echo "GATE full: ok, 3 checks (no additional checks yet)"

# all: the whole suite -- identical to full for now.
_gate-all: _gate-full
	@echo "GATE all: ok, 3 checks"
