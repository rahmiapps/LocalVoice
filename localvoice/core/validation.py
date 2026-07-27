from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .languages import SUPPORTED_SPEECH_LANGUAGE_CODES

SUPPORTED_UI_LANGUAGES = {"de", "en", "fr", "it", "es", "zh"}
SUPPORTED_SPEECH_LANGUAGES = {"auto", *SUPPORTED_SPEECH_LANGUAGE_CODES}

RECORDING_MODES = {"hold", "toggle"}
OUTPUT_MODES = {"insert", "clipboard", "preview", "app"}
THEMES = {"dark", "light", "system"}
MODEL_SIZES = {"tiny", "base", "small", "medium", "large", "turbo"}
COMPUTE_DEVICES = {"auto", "cpu", "cuda"}
COMPUTE_TYPES = {"auto", "int8", "int8_float16", "float16", "float32"}
RECOGNITION_MODES = {"fast", "balanced", "accurate"}
WRITING_STYLES = {"neutral", "email", "chat", "code"}
OVERLAY_POSITIONS = {"bottom_right", "bottom_center", "top_right", "near_cursor", "custom"}

# Deliberately conservative. Global hotkeys should be short and should not contain
# shell syntax, control characters, paths, or arbitrary long text.
_HOTKEY_TOKEN = re.compile(r"^(?:ctrl|alt|shift|meta|space|enter|tab|escape|esc|backspace|delete|insert|num(?:[0-9]|_decimal)|f(?:[1-9]|1[0-9]|2[0-4])|mouse(?:4|5|middle)|[a-z0-9])$")
_APP_NAME = re.compile(r"^[\w .+@()*?\-]{1,180}$", re.UNICODE)


def clamp_number(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))



def normalize_max_recording_seconds(value: Any, default: int = 1800) -> int:
    """Allow an explicit zero for unlimited, but never turn invalid negatives into it."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number == 0:
        return 0
    if number < 0:
        return default
    return max(10, min(86_400, number))

def safe_choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value).strip().lower()
    return candidate if candidate in allowed else default


def normalize_language(value: Any, *, allow_auto: bool = True, allow_same: bool = False, default: str = "auto") -> str:
    candidate = str(value).strip().lower().replace("_", "-")
    if candidate.startswith("zh-"):
        candidate = "zh"
    allowed = set(SUPPORTED_SPEECH_LANGUAGES)
    if not allow_auto:
        allowed.discard("auto")
    if allow_same:
        allowed.add("same")
    if candidate in allowed:
        return candidate
    return default


def normalize_language_list(values: Any, *, maximum: int = 12) -> list[str]:
    if isinstance(values, str):
        values = values.split(",")
    if not isinstance(values, Iterable):
        return []
    result: list[str] = []
    for value in values:
        code = normalize_language(value, allow_auto=False, default="")
        if code and code not in result:
            result.append(code)
        if len(result) >= maximum:
            break
    return result



def normalize_language_target_rules(values: Any, *, maximum: int = 50) -> dict[str, str]:
    """Validate source-to-target translation rules such as ``en:de, fr:it``."""
    pairs: list[tuple[Any, Any]] = []
    if isinstance(values, dict):
        pairs = list(values.items())
    elif isinstance(values, str):
        for item in values.split(","):
            if ":" in item:
                source, target = item.split(":", 1)
                pairs.append((source, target))
    result: dict[str, str] = {}
    for source_value, target_value in pairs:
        source = normalize_language(source_value, allow_auto=False, default="")
        target = normalize_language(target_value, allow_auto=False, default="")
        if source and target and source != target:
            result[source] = target
        if len(result) >= maximum:
            break
    return result

def normalize_hotkey(value: Any, default: str = "f8") -> str:
    raw = str(value or "").strip().lower().replace(" ", "")
    aliases = {
        "control": "ctrl", "return": "enter", "esc": "escape",
        "numpad0": "num0", "numpad1": "num1", "numpad2": "num2",
        "numpad3": "num3", "numpad4": "num4", "numpad5": "num5",
        "numpad6": "num6", "numpad7": "num7", "numpad8": "num8",
        "numpad9": "num9",
    }
    parts = [aliases.get(part, part) for part in raw.split("+") if part]
    if not parts or len(parts) > 5 or any(not _HOTKEY_TOKEN.fullmatch(part) for part in parts):
        return default
    order = {"ctrl": 0, "alt": 1, "shift": 2, "meta": 3}
    unique = sorted(set(parts), key=lambda item: (order.get(item, 10), item))
    return "+".join(unique)


def normalize_optional_hotkey(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = normalize_hotkey(raw, default="")
    return normalized


def normalize_app_list(values: Any, *, maximum: int = 100) -> list[str]:
    if isinstance(values, str):
        values = values.split(",")
    if not isinstance(values, Iterable):
        return []
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or not _APP_NAME.fullmatch(item):
            continue
        folded = item.casefold()
        if folded not in {existing.casefold() for existing in result}:
            result.append(item)
        if len(result) >= maximum:
            break
    return result


def safe_text(value: Any, *, maximum: int, strip: bool = True) -> str:
    text = str(value or "")
    text = text.replace("\x00", "")
    if strip:
        text = text.strip()
    return text[:maximum]


def safe_existing_directory(value: Any) -> str:
    text = safe_text(value, maximum=4096)
    if not text:
        return ""
    try:
        path = Path(text).expanduser()
    except (TypeError, ValueError, OSError):
        return ""
    return str(path) if path.exists() and path.is_dir() else ""
