from __future__ import annotations

import json
from pathlib import Path

from localvoice.core.settings import SettingsStore
from localvoice.core.ui_locale import UiLocaleStore, detect_system_ui_language


def test_clean_install_preselects_windows_language_but_requires_confirmation(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json", system_language="de-DE")
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False


def test_legacy_chinese_bug_is_repaired_without_deleting_other_preferences(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({
        "settings_schema_version": 5,
        "ui_language": "zh",
        "first_run_complete": True,
        "model_size": "medium",
        "hotkey": "f9",
        "preferred_languages": ["zh", "de", "en"],
    }), encoding="utf-8")
    store = SettingsStore(path, system_language="de-DE")
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False
    assert store.current.model_size == "medium"
    assert store.current.hotkey == "f9"
    assert store.current.preferred_languages[0] == "de"


def test_confirmed_language_survives_reinstall_style_reload(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path, system_language="de-DE")
    store.current.first_run_complete = True
    store.confirm_ui_language("de")
    store.save(store.current)
    reloaded = SettingsStore(path, system_language="en-US")
    assert reloaded.current.ui_language == "de"
    assert reloaded.current.ui_language_confirmed is True
    assert reloaded.current.first_run_complete is True


def test_confirmed_locale_record_repairs_mismatched_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    locale_path = tmp_path / "ui-locale.json"
    path.write_text(json.dumps({
        "settings_schema_version": 6,
        "ui_language": "zh",
        "ui_language_confirmed": True,
        "first_run_complete": True,
    }), encoding="utf-8")
    UiLocaleStore(locale_path).save_confirmed("de")
    store = SettingsStore(path, system_language="en-US", locale_path=locale_path)
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is True


def test_choose_language_reset_preserves_models_and_preferences(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path, system_language="de-DE")
    store.current.model_size = "large"
    store.current.hotkey = "f9"
    store.current.first_run_complete = True
    store.confirm_ui_language("de")
    store.save(store.current)
    store.prepare_language_selection()
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False
    assert store.current.model_size == "large"
    assert store.current.hotkey == "f9"


def test_system_language_detection_is_allowlisted(monkeypatch) -> None:
    monkeypatch.setenv("LOCALVOICE_SYSTEM_LANGUAGE", "de-DE")
    assert detect_system_ui_language() == "de"
    monkeypatch.setenv("LOCALVOICE_SYSTEM_LANGUAGE", "../../bad")
    assert detect_system_ui_language() in {"de", "en", "fr", "it", "es", "zh"}


def test_installer_has_language_recovery_and_optional_data_removal() -> None:
    source = Path("installer/windows/LocalVoice.iss").read_text(encoding="utf-8")
    assert "--choose-language" in source
    assert "RemoveUserDataPrompt" in source
    assert "DelTree" in source


def test_poisoned_legacy_locale_record_is_never_trusted(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    locale_path = tmp_path / "ui-locale.json"
    path.write_text(json.dumps({
        "settings_schema_version": 7,
        "ui_language": "zh",
        "ui_language_confirmed": True,
        "first_run_complete": True,
        "model_size": "medium",
    }), encoding="utf-8")
    locale_path.write_text(json.dumps({
        "schema_version": 1,
        "ui_language": "zh",
        "confirmed": True,
    }), encoding="utf-8")
    store = SettingsStore(path, system_language="de-DE", locale_path=locale_path)
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False
    assert store.current.model_size == "medium"


def test_schema_four_explicit_choice_is_trusted_after_reinstall(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    locale_path = tmp_path / "ui-locale.json"
    path.write_text(json.dumps({
        "settings_schema_version": 9,
        "ui_language": "zh",
        "ui_language_confirmed": True,
        "first_run_complete": True,
    }), encoding="utf-8")
    UiLocaleStore(locale_path).save_confirmed("de")
    store = SettingsStore(path, system_language="zh-CN", locale_path=locale_path)
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is True
    assert store.current.first_run_complete is True


def test_language_fix_script_writes_new_confirmation_schema() -> None:
    source = Path("scripts/Fix-Language-Windows.ps1").read_text(encoding="utf-8")
    assert "confirmation_generation = 4" in source
    assert "confirmation_source = 'explicit-user-choice'" in source
    assert "ui_language_confirmed' $true" in source


def test_generation_two_confirmation_is_rejected_once_for_release_migration(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    locale_path = tmp_path / "ui-locale.json"
    path.write_text(json.dumps({
        "settings_schema_version": 8,
        "ui_language": "zh",
        "ui_language_confirmed": True,
        "first_run_complete": True,
        "model_size": "medium",
    }), encoding="utf-8")
    locale_path.write_text(json.dumps({
        "schema_version": 2,
        "confirmation_generation": 2,
        "confirmation_source": "explicit-user-choice",
        "ui_language": "zh",
        "confirmed": True,
    }), encoding="utf-8")
    store = SettingsStore(path, system_language="de-DE", locale_path=locale_path)
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False
    assert store.current.model_size == "medium"


def test_language_choice_happens_before_main_window_construction() -> None:
    source = Path("localvoice/app.py").read_text(encoding="utf-8")
    chooser = source.index("onboarding = OnboardingDialog(store, None)")
    window = source.index("window = MainWindow(")
    assert chooser < window


def test_dedicated_language_chooser_uses_direct_buttons_and_verifies_choice() -> None:
    source = Path("localvoice/ui/dialogs.py").read_text(encoding="utf-8")
    assert "class LanguageSelectionDialog" in source
    assert "button.clicked.connect" in source
    assert "self.store.confirm_ui_language(language)" in source
    assert "self.store.locale_store.load_confirmed() != language" in source


def test_language_chooser_runs_before_onboarding_and_main_window() -> None:
    source = Path("localvoice/app.py").read_text(encoding="utf-8")
    chooser = source.index("language_dialog = LanguageSelectionDialog")
    onboarding = source.index("onboarding = OnboardingDialog")
    window = source.index("window = MainWindow(")
    assert chooser < onboarding < window


def test_generation_three_confirmation_is_rejected_for_21_migration(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    locale_path = tmp_path / "ui-locale.json"
    path.write_text(json.dumps({
        "settings_schema_version": 9,
        "ui_language": "zh",
        "ui_language_confirmed": True,
        "first_run_complete": True,
    }), encoding="utf-8")
    locale_path.write_text(json.dumps({
        "schema_version": 3,
        "confirmation_generation": 3,
        "confirmation_source": "explicit-user-choice",
        "ui_language": "zh",
        "confirmed": True,
    }), encoding="utf-8")
    store = SettingsStore(path, system_language="de-DE", locale_path=locale_path)
    assert store.current.ui_language == "de"
    assert store.current.ui_language_confirmed is False
    assert store.current.first_run_complete is False
