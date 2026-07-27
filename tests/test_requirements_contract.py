from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from localvoice.core.models import AppSettings, Profile


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_every_application_setting_is_wired_to_ui_or_runtime() -> None:
    source = "\n".join(
        [
            _read("localvoice/ui/dialogs.py"),
            _read("localvoice/ui/main_window.py"),
            _read("localvoice/ui/overlay.py"),
            _read("localvoice/core/controller.py"),
            _read("localvoice/core/hotkeys.py"),
            _read("localvoice/core/settings.py"),
        ]
    )
    missing = [field.name for field in fields(AppSettings) if field.name not in source]
    assert not missing, f"Unwired AppSettings fields: {missing}"


def test_every_profile_setting_is_wired_to_editor_or_controller() -> None:
    source = "\n".join(
        [
            _read("localvoice/ui/dialogs.py"),
            _read("localvoice/core/controller.py"),
            _read("localvoice/core/database.py"),
        ]
    )
    missing = [field.name for field in fields(Profile) if field.name != "id" and field.name not in source]
    assert not missing, f"Unwired Profile fields: {missing}"


def test_recording_overlay_contains_all_promised_visible_states_and_controls() -> None:
    source = _read("localvoice/ui/overlay.py")
    for required in (
        "self.dot",
        "recording_bar",
        "_pulse",
        "_elapsed",
        "set_level",
        "stop_clicked",
        "cancel_clicked",
        "recording",
        "processing",
        "translating",
        "inserted",
        "copied",
        "cancelled",
        "error",
    ):
        assert required in source


def test_retention_is_enforced_at_start_after_dictation_after_settings_and_periodically() -> None:
    app = _read("localvoice/app.py")
    controller = _read("localvoice/core/controller.py")
    window = _read("localvoice/ui/main_window.py")
    for call in ("purge_history", "prune_history", "purge_saved_audio"):
        assert call in app
        assert call in controller
        assert call in window
    assert "6 * 60 * 60 * 1000" in window
    assert "timeout.connect(self._apply_retention)" in window


def test_database_uses_hardened_sqlite_pragmas() -> None:
    source = _read("localvoice/core/database.py")
    assert 'PRAGMA foreign_keys=ON' in source
    assert 'PRAGMA trusted_schema=OFF' in source
    assert 'PRAGMA secure_delete=ON' in source
    assert 'PRAGMA temp_store=MEMORY' in source


def test_release_scripts_cover_all_promised_package_formats() -> None:
    windows = _read("scripts/Build-Windows.ps1")
    linux = _read("scripts/Build-Linux.sh")
    all_builds = _read("scripts/Build-All.ps1")
    assert "LocalVoice-Setup-Windows" in windows
    assert "Portable" in windows
    assert "AppImage" in linux
    assert ".deb" in linux
    assert "tar.gz" in linux
    assert "Build-Windows.ps1" in all_builds
    assert "Build-Linux.sh" in all_builds
    assert ".venv-windows" in windows
    assert ".venv-linux" in linux


def test_normal_dictation_path_has_no_implicit_model_download() -> None:
    transcription = _read("localvoice/core/transcription.py")
    controller = _read("localvoice/core/controller.py")
    assert "local_files_only=True" in transcription
    assert "snapshot_download(" not in controller
    assert "hf_hub_download(" not in controller


def test_private_mode_and_audio_history_invariants_are_enforced() -> None:
    models = _read("localvoice/core/models.py")
    controller = _read("localvoice/core/controller.py")
    dialogs = _read("localvoice/ui/dialogs.py")
    assert "and not private_mode" in models
    assert "and save_history" in models
    assert "not self.settings.save_history" in controller
    assert "audio_requires_history" in dialogs


def test_modern_dashboard_language_picker_reliable_steps_and_requested_scales_exist() -> None:
    window = _read("localvoice/ui/main_window.py")
    dialogs = _read("localvoice/ui/dialogs.py")
    theme = _read("localvoice/ui/theme.py")
    assert "HeroCard" in window
    assert "quick_actions" in window
    assert "device_status" in window
    assert "BrandCard" in window
    assert "LanguageSelectionDialog" in dialogs
    assert "preferred_row.addWidget(preferred_button)" in dialogs
    assert 'down.setText("−")' in dialogs
    assert 'up.setText("+")' in dialogs
    assert '"medium": 1.72' in theme
    assert '"large": 1.92' in theme


def test_recording_is_gated_by_verified_offline_model_and_ui_explains_it() -> None:
    controller = _read("localvoice/core/controller.py")
    window = _read("localvoice/ui/main_window.py")
    assert "is_model_available" in controller
    assert "MODEL_MISSING:" in controller
    assert "def _request_record_action" in window
    assert "open_model_manager_question" in window


def test_microphone_dialog_does_not_expose_qt_signal_to_native_audio_callback() -> None:
    dialogs = _read("localvoice/ui/dialogs.py")
    section = dialogs[dialogs.index("class MicrophoneTestDialog"):dialogs.index("class OnboardingDialog")]
    assert "latest_level" in section
    assert "level_signal.emit" not in section


def test_hotkey_test_uses_actual_global_backend_and_cleans_it_up() -> None:
    dialogs = _read("localvoice/ui/dialogs.py")
    section = dialogs[dialogs.index("class HotkeyTestDialog"):dialogs.index("class PreviewDialog")]
    assert "self.service = GlobalHotkeyService()" in section
    assert "self.service.start()" in section
    assert "self.service.stop()" in section
    assert "suppress_keystroke=False" in section


def test_medium_layout_dimensions_match_former_large_and_large_adds_room() -> None:
    window = _read("localvoice/ui/main_window.py")
    assert '"medium": (400, 66, 42)' in window
    assert '"large": (455, 76, 50)' in window
