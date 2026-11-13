#!/bin/bash
# Watches for Docker Desktop's VM process (com.docker.virtualization) dying
# under memory pressure (observed twice: the kernel appears to kill it when
# the host is critically low on free RAM, and it does not auto-restart).
# When that happens, nothing can build/run sandboxed containers, and any
# `inspect eval` run on a Docker-sandboxed task just hangs forever waiting
# on a backend that's gone -- it does not error out visibly.
#
# This script polls every $INTERVAL seconds and runs `docker desktop
# restart` whenever the VM process is missing. It also logs free-memory
# stats each tick so the pattern (VM death correlating with low free RAM)
# can be confirmed from the log afterward.
#
# Usage: bash docker_vm_guard.sh [interval_seconds] > docker_vm_guard.log 2>&1 &

INTERVAL="${1:-20}"
LOGFILE="${2:-/Users/cristal/Desktop/discoverybench-baseline-runs/pilot/docker_vm_guard.log}"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

log "docker_vm_guard started, interval=${INTERVAL}s"

while true; do
  free_pages=$(vm_stat | awk '/Pages free/ {gsub("\\.", "", $3); print $3}')
  free_mb=$(( free_pages * 16384 / 1024 / 1024 ))

  if ! pgrep -f "com.docker.virtualization" >/dev/null 2>&1; then
    log "DOCKER_VM_DOWN (free=${free_mb}MB) -- restarting Docker Desktop"
    docker desktop restart >>"$LOGFILE" 2>&1
    # give it a moment to come up before the next check
    sleep 10
    if pgrep -f "com.docker.virtualization" >/dev/null 2>&1; then
      log "DOCKER_VM_RESTARTED_OK"
    else
      log "DOCKER_VM_RESTART_FAILED -- will retry next tick"
    fi
  else
    log "ok (free=${free_mb}MB, vm=up)"
  fi

  sleep "$INTERVAL"
done
