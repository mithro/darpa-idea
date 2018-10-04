#!/bin/bash
# This file runs the Electra executable within the JITPCB pass management system.
#$1 is the working build directory with terminating forward slash
#$2 is the project name stub (output filename before first period in name)
#$3 is the JitPCB installation directory
ELECTRA_BIN="electra"
PROCESS_LOCK_PY="$3/scripts/process_lock.py"

#Timestamping tool
touch "$1$2.rte.start"

#If REMOTE_ELECTRA_BUILD is not set
if [ -z ${REMOTE_ELECTRA_BUILD+x} ]; then
  python $PROCESS_LOCK_PY $1.electra.lock $1$2.rte.continue "$ELECTRA_BIN -nog -design $1$2.dsn -do $1$2.do -quit | true"
  # Move file if not in ./ directory
  if ! [ ./ -ef $1 ]; then
    mv $2.rte $1$2.rte
  fi

#Otherwise use remote electra installation
else
  REMOTE_HOST=${REMOTE_ELECTRA_BUILD%:*}
  REMOTE_DIR=${REMOTE_ELECTRA_BUILD#*:}  

  scp $1$2.dsn $1$2.do $PROCESS_LOCK_PY $REMOTE_ELECTRA_BUILD
  ssh $REMOTE_HOST "cd $REMOTE_DIR && python process_lock.py /usr/local/share/jitpcb/.electra.lock $2.rte.continue \"./$ELECTRA_BIN -nog -design $2.dsn -do $2.do -quit | true\""
  scp $REMOTE_ELECTRA_BUILD/$2.rte.continue $1$2.rte.continue
  scp $REMOTE_ELECTRA_BUILD/$2.rte $1$2.rte

fi
