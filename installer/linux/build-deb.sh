#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VERSION="2.1.1"
ARCH="amd64"
PKG="$ROOT/build/deb/localvoice_${VERSION}_${ARCH}"
OUTPUT="$ROOT/release/linux/LocalVoice-Linux-${ARCH}.deb"

rm -rf "$PKG"
mkdir -p \
  "$PKG/DEBIAN" \
  "$PKG/opt/localvoice/app" \
  "$PKG/opt/localvoice/bin" \
  "$PKG/usr/bin" \
  "$PKG/usr/share/applications" \
  "$PKG/usr/share/icons/hicolor/256x256/apps"

cat > "$PKG/DEBIAN/control" <<EOF_CONTROL
Package: localvoice
Version: 2.1.1
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Rahmi Apps
Depends: python3 (>= 3.11), python3-venv, python3-pip, libportaudio2, libasound2, libgl1, libegl1, libdbus-1-3, libxcb-xinerama0, libxcb-cursor0, libxkbcommon-x11-0
Recommends: zenity, wtype
Description: Private offline speech-to-text and local translation for Windows and Linux.
 LocalVoice installs its private Python runtime in the current user's local data
 directory on first launch. Speech and translation models remain optional local
 downloads managed by the application.
EOF_CONTROL

cp -a "$ROOT/localvoice" "$PKG/opt/localvoice/app/localvoice"
cp -a "$ROOT/resources" "$PKG/opt/localvoice/app/resources"
cp "$ROOT/run_localvoice.py" "$PKG/opt/localvoice/app/run_localvoice.py"
cp "$ROOT/requirements-linux-runtime.txt" "$PKG/opt/localvoice/app/requirements-linux-runtime.txt"
cp "$ROOT/LICENSE" "$PKG/opt/localvoice/app/LICENSE"
cp "$ROOT/installer/linux/bootstrap-localvoice.sh" "$PKG/opt/localvoice/bin/bootstrap-localvoice.sh"
chmod 0755 "$PKG/opt/localvoice/bin/bootstrap-localvoice.sh"

cat > "$PKG/usr/bin/localvoice" <<'EOF_LAUNCHER'
#!/usr/bin/env bash
export LOCALVOICE_APP_ROOT=/opt/localvoice/app
exec /opt/localvoice/bin/bootstrap-localvoice.sh "$@"
EOF_LAUNCHER
chmod 0755 "$PKG/usr/bin/localvoice"

cp "$ROOT/installer/linux/localvoice.desktop" "$PKG/usr/share/applications/localvoice.desktop"
cp "$ROOT/resources/localvoice.png" "$PKG/usr/share/icons/hicolor/256x256/apps/localvoice.png"

mkdir -p "$ROOT/release/linux"
dpkg-deb --root-owner-group --build "$PKG" "$OUTPUT"
echo "Created $OUTPUT"
