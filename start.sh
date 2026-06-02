#!/usr/bin/env bash
set -e

# Resolve data directory (default: ./local-notebook-data next to this script)
DATA_DIR="${LOCAL_NOTEBOOK_DATA_DIR:-./local-notebook-data}"
mkdir -p "$DATA_DIR"

# Linux only: pass host UID/GID so files written into the bind-mounted data
# directory are owned by the host user instead of root.
# macOS / Windows Docker Desktop handle this transparently; leave defaults (0:0).
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  export CURRENT_UID
  export CURRENT_GID
  CURRENT_UID=$(id -u)
  CURRENT_GID=$(id -g)
fi

exec docker compose "$@"