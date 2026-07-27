#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo "Python 3.11 or 3.12 is required."; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info[:2] not in {(3, 11), (3, 12)}:
    raise SystemExit("LocalVoice requires Python 3.11 or 3.12.")
PY
if command -v apt-get >/dev/null; then
  echo "Debian/Ubuntu dependencies are expected to be installed by GitHub Actions or the user:"
  echo "python3-venv portaudio19-dev libportaudio2 libasound2-dev libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libgl1 libegl1 libdbus-1-3 desktop-file-utils patchelf fakeroot dpkg-dev zsync file"
fi
rm -rf .venv-linux
python3 -m venv .venv-linux
. .venv-linux/bin/activate
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
echo "LocalVoice is ready. Start it with scripts/Start-Linux.sh"
