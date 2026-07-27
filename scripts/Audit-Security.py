from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = [ROOT / "localvoice", ROOT / "scripts"]
IGNORED = {Path(__file__).resolve()}
issues: list[str] = []

DANGEROUS_CALLS = {"os.system", "subprocess.getoutput", "subprocess.getstatusoutput"}
SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]{8,}['\"]")


def call_name(node: ast.Call) -> str:
    target = node.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


for source_root in SOURCE_ROOTS:
    for path in source_root.rglob("*.py"):
        if path.resolve() in IGNORED:
            continue
        text = path.read_text(encoding="utf-8")
        if SECRET_PATTERN.search(text):
            issues.append(f"{path.relative_to(ROOT)}: possible hard-coded secret")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{path.relative_to(ROOT)}:{exc.lineno}: syntax error")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile"}:
                issues.append(f"{path.relative_to(ROOT)}:{node.lineno}: disallowed call {node.func.id}")
            if name in DANGEROUS_CALLS:
                issues.append(f"{path.relative_to(ROOT)}:{node.lineno}: disallowed call {name}")
            if name.startswith("subprocess."):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        issues.append(f"{path.relative_to(ROOT)}:{node.lineno}: subprocess shell=True")
            if name in {"pickle.load", "pickle.loads", "marshal.load", "marshal.loads", "yaml.load"}:
                issues.append(f"{path.relative_to(ROOT)}:{node.lineno}: unsafe deserialization {name}")


# Scan release scripts for common command-injection and permission hazards.
SCRIPT_PATTERNS = {
    r"(?i)\bInvoke-Expression\b": "PowerShell Invoke-Expression",
    r"(?i)\biex\s": "PowerShell iex",
    r"(?i)-EncodedCommand": "encoded PowerShell command",
    r"(?m)\b(?:curl|wget)\b[^\n]*\|\s*(?:sh|bash)\b": "download piped into a shell",
    r"(?m)\beval\s+[\"']": "shell eval",
    r"(?m)chmod\s+777\b": "world-writable executable permissions",
}
for pattern_path in list((ROOT / "scripts").glob("*.sh")) + list((ROOT / "scripts").glob("*.ps1")) + list((ROOT / "installer").rglob("*.sh")):
    script_text = pattern_path.read_text(encoding="utf-8")
    for pattern, label in SCRIPT_PATTERNS.items():
        if re.search(pattern, script_text):
            issues.append(f"{pattern_path.relative_to(ROOT)}: disallowed {label}")

appimage_installer = (ROOT / "scripts/Install-AppImageTool.sh").read_text(encoding="utf-8")
for required in ("--proto '=https'", "--tlsv1.2", "digest", "sha256sum", "EXPECTED"):
    if required not in appimage_installer:
        issues.append(f"scripts/Install-AppImageTool.sh: missing verified-download control {required}")

# Native audio callbacks must not retain a bound signal owned by a temporary Qt dialog.
dialog_source = (ROOT / "localvoice/ui/dialogs.py").read_text(encoding="utf-8")
mic_section = dialog_source.split("class MicrophoneTestDialog", 1)[-1].split("class OnboardingDialog", 1)[0]
if "level_signal.emit" in mic_section or "recorder.on_level = self." in mic_section:
    issues.append("localvoice/ui/dialogs.py: microphone test exposes a temporary Qt object to PortAudio")

# Qt clipboard callbacks must never be scheduled with a Python background timer.
system_source = (ROOT / "localvoice/core/system.py").read_text(encoding="utf-8")
if "threading.Timer" in system_source:
    issues.append("localvoice/core/system.py: clipboard action scheduled from a background thread")

# Ensure normal dictation cannot opt into a model download.
transcription = (ROOT / "localvoice/core/transcription.py").read_text(encoding="utf-8")
transcribe_section = transcription.split("    def transcribe(", 1)[-1]
if "download_model(" in transcribe_section:
    issues.append("localvoice/core/transcription.py: transcribe path contains a model download")


# Managed model installation must never self-sign files that existed before the
# explicit model-manager download.
ensure_model_section = transcription.split("    def ensure_model(", 1)[-1].split("    def remove_model(", 1)[0]
pre_download_section = ensure_model_section.split("from faster_whisper.utils import download_model", 1)[0]
if "_write_manifest(target" in pre_download_section:
    issues.append("localvoice/core/transcription.py: existing managed model can be self-signed")
if "_discard_unverified_managed_model(target)" not in pre_download_section:
    issues.append("localvoice/core/transcription.py: invalid managed models are not quarantined before download")

# Guard against accidental network clients outside explicit model installers.
for path in (ROOT / "localvoice").rglob("*.py"):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    if any(token in text for token in ("requests.get(", "urllib.request.urlopen(", "httpx.get(")):
        issues.append(f"{rel}: direct network call found")

if issues:
    print("Security audit failed:")
    for issue in issues:
        print(f" - {issue}")
    raise SystemExit(1)
print("Security audit passed: Python and release scripts contain no blocked execution, deserialization, secret, permission, or hidden-download patterns.")
