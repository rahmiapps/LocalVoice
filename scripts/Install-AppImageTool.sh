#!/usr/bin/env bash
set -euo pipefail
DESTINATION="${1:-$HOME/.local/bin/appimagetool}"
mkdir -p "$(dirname "$DESTINATION")"
API="https://api.github.com/repos/AppImage/appimagetool/releases/tags/continuous"
TMP_JSON="$(mktemp)"
TMP_BIN="$(mktemp)"
trap 'rm -f "$TMP_JSON" "$TMP_BIN"' EXIT
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location "$API" -o "$TMP_JSON"
readarray -t META < <(python3 - "$TMP_JSON" <<'PY'
import json, sys
record=json.load(open(sys.argv[1], encoding='utf-8'))
assets=[a for a in record.get('assets',[]) if a.get('name')=='appimagetool-x86_64.AppImage']
if len(assets)!=1:
    raise SystemExit('Expected exactly one official x86_64 appimagetool asset.')
asset=assets[0]
url=str(asset.get('browser_download_url',''))
digest=str(asset.get('digest',''))
if not url.startswith('https://github.com/AppImage/appimagetool/releases/download/continuous/'):
    raise SystemExit('Unexpected appimagetool download URL.')
if not digest.startswith('sha256:') or len(digest)!=71:
    raise SystemExit('GitHub did not provide a SHA-256 digest; refusing an unverified tool download.')
print(url)
print(digest.split(':',1)[1].lower())
PY
)
URL="${META[0]}"
EXPECTED="${META[1]}"
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location "$URL" -o "$TMP_BIN"
ACTUAL="$(sha256sum "$TMP_BIN" | awk '{print tolower($1)}')"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "appimagetool SHA-256 mismatch" >&2
  exit 1
fi
install -m 0755 "$TMP_BIN" "$DESTINATION"
echo "Verified appimagetool installed at $DESTINATION"
