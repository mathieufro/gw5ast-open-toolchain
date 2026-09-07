#!/bin/bash
# P3.T11 driver: two vendor runs, one log file, one completion marker.
set -u
BATCH=p3-oddr-iddr-audit
OTC=/Users/alex/fine-line/.atelier/worktrees/2026-09-03-open-toolchain-gw5ast-7e84/open-toolchain
LOG=$OTC/evidence/_runs/$BATCH.log
export PYTHONPATH=/Users/alex/fine-line/apicula-wt/p3ddr
export DATASTORE=/Users/alex/fine-line-data/open-toolchain-gw5ast
export GOWINHOME=/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA
export DYLD_LIBRARY_PATH=$GOWINHOME/IDE/lib
export DYLD_FRAMEWORK_PATH=$GOWINHOME/IDE/lib
PY=/Users/alex/fine-line/vendor/venv/bin/python
cd /Users/alex/fine-line/apicula-wt/p3ddr
echo "BATCH_START $BATCH pid=$$ $(date -u +%FT%TZ)" >> "$LOG"
OK=0; DIFF=0; ABORT=0; N=0
for STEP in oddr-pair iddr-pair; do
  echo "RUN_START $BATCH-$STEP $(date -u +%FT%TZ)" >> "$LOG"
  $PY $OTC/evidence/oddr-iddr/audit_oddr_iddr_attrs.py \
      --design-root $DATASTORE/p3t11 --run all --only "$STEP" >> "$LOG" 2>&1
  RC=$?
  N=$((N+1))
  if [ $RC -eq 0 ]; then OK=$((OK+1)); else ABORT=$((ABORT+1)); fi
  echo "RUN_DONE $BATCH-$STEP rc=$RC $(date -u +%FT%TZ)" >> "$LOG"
done
# The full table, both steps decoded together, spending no further oracle run.
$PY $OTC/evidence/oddr-iddr/audit_oddr_iddr_attrs.py \
    --design-root $DATASTORE/p3t11 --run decode-only >> "$LOG" 2>&1
echo "BATCH_COMPLETE $BATCH runs=$N ok=$OK diff=$DIFF aborted=$ABORT" >> "$LOG"
