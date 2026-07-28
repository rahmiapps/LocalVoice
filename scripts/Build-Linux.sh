#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x .venv-linux/bin/python ]]; then
  bash ./scripts/Setup-Linux.sh
fi

. .venv-linux/bin/activate

python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements-build.txt
python -m pip check
PYTHONPATH=. python scripts/Run-Checks.py
python -m pip_audit \
  -r requirements.txt \
  --progress-spinner off \
  --ignore-vuln PYSEC-2026-3075

rm -rf build dist release/linux
mkdir -p release/linux

# Validate the actual application entry point with all Linux runtime dependencies.
QT_QPA_PLATFORM=offscreen \
PYNPUT_BACKEND=dummy \
python run_localvoice.py --package-smoke-test

# Create the small DEB bootstrap installer.
bash ./installer/linux/build-deb.sh

# Create a small portable source package. The private runtime is installed once
# in the user's local data folder on first launch.
PORTABLE_ROOT="release/linux/LocalVoice-Linux-x64-Portable"
mkdir -p "$PORTABLE_ROOT/app" "$PORTABLE_ROOT/bin"
cp -a localvoice "$PORTABLE_ROOT/app/localvoice"
cp -a resources "$PORTABLE_ROOT/app/resources"
cp run_localvoice.py "$PORTABLE_ROOT/app/run_localvoice.py"
cp requirements-linux-runtime.txt "$PORTABLE_ROOT/app/requirements-linux-runtime.txt"
cp LICENSE "$PORTABLE_ROOT/app/LICENSE"
cp installer/linux/bootstrap-localvoice.sh "$PORTABLE_ROOT/bin/bootstrap-localvoice.sh"
chmod +x "$PORTABLE_ROOT/bin/bootstrap-localvoice.sh"
cat > "$PORTABLE_ROOT/LocalVoice.sh" <<'EOF_PORTABLE'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export LOCALVOICE_APP_ROOT="$HERE/app"
exec "$HERE/bin/bootstrap-localvoice.sh" "$@"
EOF_PORTABLE
chmod +x "$PORTABLE_ROOT/LocalVoice.sh"
tar -C release/linux -czf release/linux/LocalVoice-Linux-x64-Portable.tar.gz LocalVoice-Linux-x64-Portable
rm -rf "$PORTABLE_ROOT"

# Create a source-only AppImage bootstrap. Large Python, Torch and model files
# are installed once per user instead of being duplicated in every package.
APPDIR="release/linux/AppDir"
mkdir -p \
  "$APPDIR/usr/share/localvoice/app" \
  "$APPDIR/usr/lib/localvoice" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp -a localvoice "$APPDIR/usr/share/localvoice/app/localvoice"
cp -a resources "$APPDIR/usr/share/localvoice/app/resources"
cp run_localvoice.py "$APPDIR/usr/share/localvoice/app/run_localvoice.py"
cp requirements-linux-runtime.txt "$APPDIR/usr/share/localvoice/app/requirements-linux-runtime.txt"
cp LICENSE "$APPDIR/usr/share/localvoice/app/LICENSE"
cp installer/linux/bootstrap-localvoice.sh "$APPDIR/usr/lib/localvoice/bootstrap-localvoice.sh"
cp installer/linux/localvoice.desktop "$APPDIR/usr/share/applications/localvoice.desktop"
cp resources/localvoice.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/localvoice.svg"
cp installer/linux/AppRun "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/lib/localvoice/bootstrap-localvoice.sh"
ln -sf usr/share/applications/localvoice.desktop "$APPDIR/localvoice.desktop"
ln -sf usr/share/icons/hicolor/scalable/apps/localvoice.svg "$APPDIR/localvoice.svg"

APPIMAGE_TOOL="$(command -v appimagetool || true)"
if [[ -z "$APPIMAGE_TOOL" ]]; then
  APPIMAGE_TOOL="$PWD/.tools/appimagetool"
  bash ./scripts/Install-AppImageTool.sh "$APPIMAGE_TOOL"
fi
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$APPIMAGE_TOOL" \
  "$APPDIR" release/linux/LocalVoice-Linux-x86_64.AppImage
rm -rf "$APPDIR"

[[ -f release/linux/LocalVoice-Linux-amd64.deb ]] || { echo "DEB package missing." >&2; exit 1; }
[[ -f release/linux/LocalVoice-Linux-x64-Portable.tar.gz ]] || { echo "Portable package missing." >&2; exit 1; }
[[ -f release/linux/LocalVoice-Linux-x86_64.AppImage ]] || { echo "AppImage missing." >&2; exit 1; }

cp requirements-linux-runtime.txt release/linux/LINUX-RUNTIME-DEPENDENCIES.txt

# GitHub releases allow at most 2 GiB per file. Fail early at 1.8 GiB.
MAX_BYTES=$((1800 * 1024 * 1024))
while IFS= read -r -d '' file; do
  size="$(stat -c '%s' "$file")"
  printf '%-58s %12s bytes\n' "$(basename "$file")" "$size"
  if (( size > MAX_BYTES )); then
    echo "Release file exceeds the 1.8 GiB safety limit: $file" >&2
    exit 1
  fi
done < <(find release/linux -maxdepth 1 -type f \
  \( -name '*.AppImage' -o -name '*.deb' -o -name '*.tar.gz' \) -print0)

find release/linux -maxdepth 1 -type f \
  \( -name '*.AppImage' -o -name '*.deb' -o -name '*.tar.gz' -o -name '*.txt' \) \
  ! -name SHA256SUMS-Linux.txt \
  -print0 | sort -z | xargs -0 sha256sum | sed 's#  release/linux/#  #' \
  > release/linux/SHA256SUMS-Linux.txt

echo "Slim Linux release created in release/linux"
