#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${LOCALVOICE_APP_ROOT:-/opt/localvoice/app}"
DATA_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/Rahmi Apps/LocalVoice"
RUNTIME_ROOT="$DATA_ROOT/linux-runtime"
VENV="$RUNTIME_ROOT/venv"
LOG_FILE="$RUNTIME_ROOT/setup.log"
MARKER="$RUNTIME_ROOT/requirements.sha256"
REQUIREMENTS="$APP_ROOT/requirements-linux-runtime.txt"

show_error() {
  local message="$1"
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="LocalVoice" --text="$message" --width=520 || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "LocalVoice" "$message" || true
  else
    printf 'LocalVoice: %s\n' "$message" >&2
  fi
}

find_python() {
  local candidate
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 13) else 1)
PY
      then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

if [[ ! -f "$REQUIREMENTS" ]]; then
  show_error "The Linux runtime requirements file is missing. Reinstall LocalVoice."
  exit 1
fi

SYSTEM_PYTHON="$(find_python || true)"
if [[ -z "$SYSTEM_PYTHON" ]]; then
  show_error "LocalVoice requires Python 3.11 or 3.12 and python3-venv."
  exit 1
fi

mkdir -p "$RUNTIME_ROOT"
CURRENT_HASH="$(sha256sum "$REQUIREMENTS" | awk '{print $1}')"
INSTALLED_HASH="$(cat "$MARKER" 2>/dev/null || true)"
NEEDS_SETUP=0

if [[ ! -x "$VENV/bin/python" || "$CURRENT_HASH" != "$INSTALLED_HASH" ]]; then
  NEEDS_SETUP=1
elif ! "$VENV/bin/python" - <<'PY' >/dev/null 2>&1
import PySide6, sounddevice, faster_whisper, argostranslate, pynput, cryptography
PY
then
  NEEDS_SETUP=1
fi

install_runtime() {
  rm -rf "$VENV"
  "$SYSTEM_PYTHON" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip wheel setuptools
  "$VENV/bin/python" -m pip install --only-binary=:all: -r "$REQUIREMENTS"
  "$VENV/bin/python" -m pip check
  printf '%s\n' "$CURRENT_HASH" > "$MARKER"
}

if (( NEEDS_SETUP )); then
  : > "$LOG_FILE"
  if command -v zenity >/dev/null 2>&1; then
    install_runtime >>"$LOG_FILE" 2>&1 &
    INSTALL_PID=$!
    (
      while kill -0 "$INSTALL_PID" 2>/dev/null; do
        echo "# Installing the private LocalVoice Linux runtime…"
        sleep 1
      done
    ) | zenity --progress --pulsate --auto-close --no-cancel \
        --title="LocalVoice" \
        --text="Installing the local runtime. This happens once and can take several minutes." \
        --width=560 || true
    if ! wait "$INSTALL_PID"; then
      show_error "The LocalVoice Linux runtime could not be installed. Details: $LOG_FILE"
      exit 1
    fi
  else
    if ! install_runtime >>"$LOG_FILE" 2>&1; then
      show_error "The LocalVoice Linux runtime could not be installed. Details: $LOG_FILE"
      exit 1
    fi
  fi
fi

export PYTHONNOUSERSITE=1
exec "$VENV/bin/python" "$APP_ROOT/run_localvoice.py" "$@"
