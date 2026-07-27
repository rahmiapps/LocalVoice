#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x .venv-linux/bin/python ] || ./scripts/Setup-Linux.sh
exec .venv-linux/bin/python run_localvoice.py "$@"
