from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import AppSettings
from .paths import CONFIG_DIR, ensure_directories
from .ui_locale import UiLocaleStore, detect_system_ui_language, normalize_ui_language


class SettingsStore:
    """Atomic, bounded and validated storage for non-secret application settings.

    UI language confirmation is stored redundantly in a tiny independent file.
    This lets LocalVoice recover from legacy settings that accidentally stored
    Chinese, without deleting models, history, profiles or dictionaries.
    """

    MAX_SETTINGS_BYTES = 2 * 1024 * 1024
    CURRENT_SCHEMA_VERSION = 10

    def __init__(
        self,
        path: Path | None = None,
        *,
        system_language: str | None = None,
        locale_path: Path | None = None,
    ) -> None:
        ensure_directories()
        self.path = path or CONFIG_DIR / "settings.json"
        self.system_language = detect_system_ui_language(system_language)
        if locale_path is None:
            locale_path = self.path.with_name("ui-locale.json")
        self.locale_store = UiLocaleStore(locale_path)
        self._lock = threading.RLock()
        self._settings = self._load()

    @property
    def current(self) -> AppSettings:
        return self._settings

    @property
    def needs_language_confirmation(self) -> bool:
        return not self._settings.ui_language_confirmed

    def _fresh_settings(self) -> AppSettings:
        settings = AppSettings()
        settings.ui_language = self.system_language
        settings.ui_language_confirmed = False
        settings.first_run_complete = False
        settings.preferred_languages = list(
            dict.fromkeys([self.system_language, *settings.preferred_languages])
        )[:12]
        return settings

    def _broken_backup_path(self) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return self.path.with_name(f"{self.path.stem}.broken-{stamp}{self.path.suffix}")

    def _load(self) -> AppSettings:
        confirmed_locale = self.locale_store.load_confirmed()
        if not self.path.exists():
            settings = self._fresh_settings()
            if confirmed_locale:
                settings.ui_language = confirmed_locale
                settings.ui_language_confirmed = True
            return settings
        try:
            size = self.path.stat().st_size
            if size <= 0 or size > self.MAX_SETTINGS_BYTES:
                raise ValueError("The settings file has an invalid size.")
            raw = self.path.read_bytes()
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("The settings file must contain an object.")
            try:
                schema_version = int(data.get("settings_schema_version", 1))
            except (TypeError, ValueError):
                schema_version = 1

            # Existing performance/UI migrations.
            if "recognition_mode" not in data:
                data["recognition_mode"] = "balanced"
                try:
                    data["beam_size"] = min(2, max(1, int(data.get("beam_size", 2))))
                except (TypeError, ValueError):
                    data["beam_size"] = 2
                data["preload_model"] = True
                data["noise_reduction"] = False
            if schema_version < 5:
                if str(data.get("ui_size", "")).lower() == "large":
                    data["ui_size"] = "medium"
                data.setdefault("auto_microphone_gain", True)
                data.setdefault("prefer_primary_language", True)
            if schema_version < 7:
                data.setdefault("live_transcription_enabled", True)
                data.setdefault("live_preview_enabled", True)
                data.setdefault("live_chunk_seconds", 3.0)
                data.setdefault("live_overlap_seconds", 0.8)

            # Durable language repair. Builds before 1.9.0 could poison both
            # settings.json and the old schema-1 ui-locale.json with Chinese.
            # Only the new independently verified schema-3 confirmation is
            # trusted. Everything else triggers a one-time chooser using the
            # Windows/Linux system language, without deleting user data.
            if confirmed_locale:
                data["ui_language"] = confirmed_locale
                data["ui_language_confirmed"] = True
            else:
                data["ui_language"] = self.system_language
                data["ui_language_confirmed"] = False
                data["first_run_complete"] = False

            data["settings_schema_version"] = self.CURRENT_SCHEMA_VERSION
            preferred = data.get("preferred_languages", [])
            chosen_language = normalize_ui_language(data.get("ui_language"), self.system_language)
            if isinstance(preferred, list):
                data["preferred_languages"] = [
                    chosen_language,
                    *[item for item in preferred if str(item).lower() != chosen_language],
                ]

            settings = AppSettings.from_dict(data)
            if not settings.ui_language_confirmed:
                settings.first_run_complete = False
            self._settings = settings
            self.save(settings)
            return settings
        except (OSError, json.JSONDecodeError, UnicodeError, TypeError, ValueError):
            backup = self._broken_backup_path()
            try:
                self.path.replace(backup)
                try:
                    os.chmod(backup, 0o600)
                except OSError:
                    pass
            except OSError:
                pass
            return self._fresh_settings()

    def save(self, settings: AppSettings | None = None) -> None:
        with self._lock:
            if settings is not None:
                self._settings = AppSettings.from_dict(settings.to_dict())
            if not self._settings.ui_language_confirmed:
                self._settings.first_run_complete = False
            self._settings.settings_schema_version = self.CURRENT_SCHEMA_VERSION
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(self.path.parent, 0o700)
            except OSError:
                pass
            payload = json.dumps(self._settings.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
            if len(payload) > self.MAX_SETTINGS_BYTES:
                raise ValueError("The validated settings payload is unexpectedly large.")
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
            if self._settings.ui_language_confirmed:
                self.locale_store.save_confirmed(self._settings.ui_language)

    def confirm_ui_language(self, language: str) -> AppSettings:
        """Persist and verify an explicit language choice made by the user."""
        normalized = normalize_ui_language(language, default="")
        if not normalized:
            raise ValueError("Unsupported UI language")
        with self._lock:
            self._settings.ui_language = normalized
            self._settings.ui_language_confirmed = True
            self.save(self._settings)
            saved_locale = self.locale_store.load_confirmed()
            if saved_locale != normalized:
                raise OSError("The selected UI language could not be verified.")
            saved_data = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                saved_data.get("ui_language") != normalized
                or saved_data.get("ui_language_confirmed") is not True
            ):
                raise OSError("The selected UI language could not be verified.")
            return self._settings

    def prepare_language_selection(self) -> AppSettings:
        """Show onboarding again without deleting any user data."""
        with self._lock:
            self.locale_store.clear()
            self._settings.ui_language = self.system_language
            self._settings.ui_language_confirmed = False
            self._settings.first_run_complete = False
            self.save(self._settings)
            return self._settings

    def update(self, **changes: object) -> AppSettings:
        with self._lock:
            merged = self._settings.to_dict()
            merged.update(changes)
            self._settings = AppSettings.from_dict(merged)
            self.save()
            return self._settings
