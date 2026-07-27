#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# ZIP extraction and Windows Git clients may not preserve Linux executable bits.
if [[ ! -x .venv-linux/bin/python ]]; then
  bash ./scripts/Setup-Linux.sh
fi

. .venv-linux/bin/activate

python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements-build.txt
python -m pip check
PYTHONPATH=. python scripts/Run-Checks.py

# Argos Translate 1.11.0 currently requires stanza==1.10.1 exactly.
# PYSEC-2026-3075 cannot be upgraded independently without breaking Argos.
# The exception is explicit and limited to that transitive dependency.
python -m pip_audit \
  -r requirements.txt \
  --progress-spinner off \
  --ignore-vuln PYSEC-2026-3075

rm -rf build dist release/linux

python -m PyInstaller --clean --noconfirm LocalVoice.spec

[[ -x dist/LocalVoice/LocalVoice ]] || {
  echo "PyInstaller did not create the Linux executable." >&2
  exit 1
}

QT_QPA_PLATFORM=offscreen \
PYNPUT_BACKEND=dummy \
dist/LocalVoice/LocalVoice --package-smoke-test

mkdir -p \
  release/linux/AppDir/usr/bin \
  release/linux/AppDir/usr/share/applications \
  release/linux/AppDir/usr/share/icons/hicolor/scalable/apps

cp -a dist/LocalVoice/. release/linux/AppDir/usr/bin/LocalVoice/
test -f installer/linux/localvoice.desktop || { echo "Missing installer/linux/localvoice.desktop" >&2; exit 1; }
test -f installer/linux/AppRun || { echo "Missing installer/linux/AppRun" >&2; exit 1; }
cp installer/linux/localvoice.desktop release/linux/AppDir/usr/share/applications/
cp resources/localvoice.svg release/linux/AppDir/usr/share/icons/hicolor/scalable/apps/localvoice.svg
cp installer/linux/AppRun release/linux/AppDir/AppRun
chmod +x release/linux/AppDir/AppRun

ln -sf usr/share/applications/localvoice.desktop release/linux/AppDir/localvoice.desktop
ln -sf usr/share/icons/hicolor/scalable/apps/localvoice.svg release/linux/AppDir/localvoice.svg

tar -C release/linux/AppDir/usr/bin \
  -czf release/linux/LocalVoice-Linux-x64-Portable.tar.gz \
  LocalVoice

APPIMAGE_TOOL="$(command -v appimagetool || true)"
if [[ -z "$APPIMAGE_TOOL" ]]; then
  APPIMAGE_TOOL="$PWD/.tools/appimagetool"
  bash ./scripts/Install-AppImageTool.sh "$APPIMAGE_TOOL"
fi

APPIMAGE_EXTRACT_AND_RUN=1 \
ARCH=x86_64 \
"$APPIMAGE_TOOL" \
  release/linux/AppDir \
  release/linux/LocalVoice-Linux-x86_64.AppImage

bash ./installer/linux/build-deb.sh

[[ -f release/linux/LocalVoice-Linux-amd64.deb ]] || {
  echo "DEB package missing." >&2
  exit 1
}

[[ -f release/linux/LocalVoice-Linux-x86_64.AppImage ]] || {
  echo "AppImage missing." >&2
  exit 1
}

python -m pip freeze > release/linux/PYTHON-DEPENDENCIES.txt

find release/linux -maxdepth 1 -type f \
  \( -name "*.AppImage" -o -name "*.deb" -o -name "*.tar.gz" -o -name "*.txt" \) \
  ! -name SHA256SUMS.txt \
  -print0 \
  | sort -z \
  | xargs -0 sha256sum \
  | sed "s#  release/linux/#  #" \
  > release/linux/SHA256SUMS.txt

echo "Linux release created in release/linux"
