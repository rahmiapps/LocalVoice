from __future__ import annotations

import ctypes
import json
import locale
import os
import sys
from pathlib import Path
from typing import Any

from .paths import CONFIG_DIR
from .validation import SUPPORTED_UI_LANGUAGES


DEFAULT_UI_LANGUAGE = "en"
LOCALE_FILE_SCHEMA = 4
LANGUAGE_CONFIRMATION_GENERATION = 4


def normalize_ui_language(value: Any, default: str = DEFAULT_UI_LANGUAGE) -> str:
    """Return one of the supported UI language codes from an OS/locale value."""
    candidate = str(value or "").strip().lower().replace("_", "-")
    if not candidate:
        return default
    primary = candidate.split("-", 1)[0]
    if primary == "zh":
        return "zh"
    return primary if primary in SUPPORTED_UI_LANGUAGES else default


def _windows_ui_locale() -> str:
    """Return the Windows display locale using the native locale-name API.

    ``GetUserDefaultLocaleName`` is more reliable than translating a numeric
    LANGID through Python's static mapping, especially in frozen builds.
    """
    if not sys.platform.startswith("win"):
        return ""
    try:
        buffer = ctypes.create_unicode_buffer(85)
        length = int(ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, len(buffer)))
        if length > 0 and buffer.value:
            return buffer.value
    except (AttributeError, OSError, TypeError, ValueError):
        pass
    try:
        language_id = int(ctypes.windll.kernel32.GetUserDefaultUILanguage())
        name = locale.windows_locale.get(language_id, "")
        if name:
            return name
    except (AttributeError, OSError, TypeError, ValueError):
        pass
    return ""


def detect_system_ui_language(explicit: str | None = None) -> str:
    """Detect a safe initial UI language without trusting application settings.

    ``LOCALVOICE_SYSTEM_LANGUAGE`` is intentionally supported for automated
    tests and managed deployments. It never bypasses the supported-language
    allowlist.
    """
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    override = os.environ.get("LOCALVOICE_SYSTEM_LANGUAGE", "")
    if override:
        candidates.append(override)
    windows_name = _windows_ui_locale()
    if windows_name:
        candidates.append(windows_name)
    try:
        current_locale = locale.getlocale()[0]
        if current_locale:
            candidates.append(current_locale)
    except (TypeError, ValueError):
        pass
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value:
            candidates.extend(part for part in value.split(":") if part)
    for candidate in candidates:
        normalized = normalize_ui_language(candidate, default="")
        if normalized:
            return normalized
    return DEFAULT_UI_LANGUAGE


class UiLocaleStore:
    """Small, independent and atomic record of the confirmed UI language.

    Keeping this value separate from the larger settings file makes language
    recovery possible even when the settings file is stale, partially migrated
    or replaced during an upgrade.
    """

    MAX_BYTES = 4096

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG_DIR / "ui-locale.json"

    def load_confirmed(self) -> str:
        if not self.path.exists():
            return ""
        try:
            raw = self.path.read_bytes()
            if not raw or len(raw) > self.MAX_BYTES:
                return ""
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict) or data.get("confirmed") is not True:
                return ""
            # All records from builds before 1.9.0 are intentionally untrusted,
            # because earlier release candidates could confirm the wrong language.
            # Schema/generation 4 is written only after the new pre-window chooser.
            if data.get("schema_version") != LOCALE_FILE_SCHEMA:
                return ""
            if data.get("confirmation_generation") != LANGUAGE_CONFIRMATION_GENERATION:
                return ""
            if data.get("confirmation_source") != "explicit-user-choice":
                return ""
            return normalize_ui_language(data.get("ui_language"), default="")
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return ""

    def save_confirmed(self, language: str) -> None:
        normalized = normalize_ui_language(language, default="")
        if not normalized:
            raise ValueError("Unsupported UI language")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        payload = json.dumps(
            {
                "schema_version": LOCALE_FILE_SCHEMA,
                "confirmation_generation": LANGUAGE_CONFIRMATION_GENERATION,
                "confirmation_source": "explicit-user-choice",
                "ui_language": normalized,
                "confirmed": True,
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        temp = self.path.with_name(self.path.name + ".tmp")
        with temp.open("wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        temp.replace(self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass
