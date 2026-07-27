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
  "$PKG/opt/localvoice" \
  "$PKG/usr/bin" \
  "$PKG/usr/share/applications" \
  "$PKG/usr/share/icons/hicolor/256x256/apps"

cat > "$PKG/DEBIAN/control" <<EOF
Package: localvoice
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Rahmi Apps
Depends: libc6, libstdc++6, libportaudio2
Recommends: wtype
Description: Private offline speech-to-text and translation for Windows and Linux.
EOF

cp -a "$ROOT/dist/LocalVoice/." "$PKG/opt/localvoice/"

cat > "$PKG/usr/bin/localvoice" <<'EOF'
#!/usr/bin/env bash
exec /opt/localvoice/LocalVoice "$@"
EOF
chmod 0755 "$PKG/usr/bin/localvoice"

cp "$ROOT/installer/linux/localvoice.desktop" \
  "$PKG/usr/share/applications/localvoice.desktop"
cp "$ROOT/resources/localvoice.png" \
  "$PKG/usr/share/icons/hicolor/256x256/apps/localvoice.png"

mkdir -p "$ROOT/release/linux"
dpkg-deb --build "$PKG" "$OUTPUT"
echo "Created $OUTPUT"
