from __future__ import annotations

import ast
import builtins
import compileall
import os
import re
import subprocess
import symtable
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if not compileall.compile_dir(ROOT / "localvoice", quiet=1):
    raise SystemExit("Python compilation failed.")
if not compileall.compile_dir(ROOT / "tests", quiet=1):
    raise SystemExit("Test compilation failed.")

# Catch unresolved global names that Python bytecode compilation alone does not detect.
unresolved: list[str] = []
for path in (ROOT / "localvoice").rglob("*.py"):
    table = symtable.symtable(path.read_text(encoding="utf-8"), str(path), "exec")
    module_definitions = {
        symbol.get_name()
        for symbol in table.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_parameter()
    }
    allowed_globals = set(dir(builtins)) | module_definitions | {"__file__", "__name__", "__package__", "__spec__"}

    def scan_symbols(current: symtable.SymbolTable) -> None:
        for symbol in current.get_symbols():
            if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in allowed_globals:
                unresolved.append(f"{path.relative_to(ROOT)}:{current.get_name()}:{symbol.get_name()}")
        for child in current.get_children():
            scan_symbols(child)

    scan_symbols(table)
if unresolved:
    raise SystemExit("Unresolved global names: " + ", ".join(sorted(set(unresolved))))

from localvoice.core import i18n  # noqa: E402

missing = i18n.validate_translations()
if any(missing.values()):
    raise SystemExit(f"Incomplete UI translations: {missing}")

from localvoice import __version__  # noqa: E402

pyproject_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
inno_text = (ROOT / "installer/windows/LocalVoice.iss").read_text(encoding="utf-8")
deb_text = (ROOT / "installer/linux/build-deb.sh").read_text(encoding="utf-8")
inno_match = re.search(r'#define MyAppVersion "([^"]+)"', inno_text)
deb_match = re.search(r'Version:\s*([0-9][^\s]*)', deb_text)
versions = {
    "package": __version__,
    "pyproject": str(pyproject_version),
    "windows installer": inno_match.group(1) if inno_match else "missing",
    "linux package": deb_match.group(1) if deb_match else "missing",
}
if len(set(versions.values())) != 1:
    raise SystemExit(f"Version mismatch: {versions}")

used_keys: set[str] = set()
for path in (ROOT / "localvoice").rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "tr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            used_keys.add(node.args[1].value)
undefined = sorted(used_keys - set(i18n._EN))
if undefined:
    raise SystemExit(f"Undefined UI translation keys: {undefined}")

windows_build = (ROOT / "scripts/Build-Windows.ps1").read_text(encoding="utf-8")
linux_build = (ROOT / "scripts/Build-Linux.sh").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
if ".venv-windows" not in windows_build or ".venv-linux" not in linux_build:
    raise SystemExit("Windows and Linux builds must use separate virtual environments.")
for action in ("actions/checkout@v7", "actions/setup-python@v7", "actions/upload-artifact@v7"):
    if action not in workflow:
        raise SystemExit(f"Expected reviewed GitHub Action version is missing: {action}")

if "--package-smoke-test" not in windows_build or "--package-smoke-test" not in linux_build:
    raise SystemExit("Native build scripts must execute the frozen package smoke test.")
if "https://timestamp.digicert.com" not in windows_build:
    raise SystemExit("Windows signing must use an HTTPS timestamp endpoint.")
if "APPIMAGE_EXTRACT_AND_RUN=1" not in linux_build:
    raise SystemExit("Linux AppImage build must not require a FUSE mount in CI.")

if "pynput.keyboard._dummy" not in (ROOT / "LocalVoice.spec").read_text(encoding="utf-8"):
    raise SystemExit("The frozen application must include pynput's dummy backend for package smoke tests.")
if "wtype" not in deb_text:
    raise SystemExit("The Debian package must recommend wtype for Wayland text insertion.")
requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
spec_text = (ROOT / "LocalVoice.spec").read_text(encoding="utf-8")
if "dbus-next" not in requirements or "dbus-next" not in pyproject_text or "collect_submodules('dbus_next')" not in spec_text:
    raise SystemExit("The Wayland portal backend is missing from a release dependency or PyInstaller bundle.")
if "_discard_unverified_managed_model(target)" not in (ROOT / "localvoice/core/transcription.py").read_text(encoding="utf-8"):
    raise SystemExit("Managed speech models must reject pre-existing unverified files.")

ui_locale_source = (ROOT / "localvoice/core/ui_locale.py").read_text(encoding="utf-8")
settings_source = (ROOT / "localvoice/core/settings.py").read_text(encoding="utf-8")
language_fix_source = (ROOT / "scripts/Fix-Language-Windows.ps1").read_text(encoding="utf-8")
if "LOCALE_FILE_SCHEMA = 4" not in ui_locale_source or "confirmation_generation" not in ui_locale_source:
    raise SystemExit("Durable UI-language confirmation schema 4 is missing.")
if "data.get(\"schema_version\") != LOCALE_FILE_SCHEMA" not in ui_locale_source:
    raise SystemExit("Legacy poisoned locale records are not rejected.")
if "CURRENT_SCHEMA_VERSION = 10" not in settings_source:
    raise SystemExit("Settings language-repair migration version is missing.")
if "confirmation_generation = 4" not in language_fix_source:
    raise SystemExit("Windows non-destructive language repair script is outdated.")

from localvoice.core.languages import SUPPORTED_SPEECH_LANGUAGE_CODES  # noqa: E402
if len(SUPPORTED_SPEECH_LANGUAGE_CODES) != 100:
    raise SystemExit("The current Whisper speech-language catalogue is incomplete.")
if set(i18n.SPEECH_LANGUAGES) != {"auto", *SUPPORTED_SPEECH_LANGUAGE_CODES}:
    raise SystemExit("Speech-language UI and validation catalogues have drifted apart.")

subprocess.run([sys.executable, str(ROOT / "scripts/Audit-Security.py")], check=True)
environment = dict(os.environ)
environment["PYTHONPATH"] = str(ROOT)
subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True, env=environment)

required_gui_modules = ("PySide6", "pynput", "sounddevice", "faster_whisper", "argostranslate", "dbus_next")
try:
    for module in required_gui_modules:
        __import__(module)
except (ImportError, OSError) as exc:
    print(f"GUI smoke test skipped in this validation environment: {exc}")
else:
    gui_environment = dict(environment)
    gui_environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    gui_environment.setdefault("PYNPUT_BACKEND", "dummy")
    subprocess.run([sys.executable, str(ROOT / "scripts/Smoke-GUI.py")], check=True, env=gui_environment)

print(f"All available checks passed. UI languages: {len(i18n.LANGUAGES)}; translated keys: {len(i18n._EN)}.")
