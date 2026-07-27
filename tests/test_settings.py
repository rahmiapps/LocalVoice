import tempfile
import unittest
from pathlib import Path
from localvoice.core.settings import SettingsStore


class SettingsTests(unittest.TestCase):
    def test_roundtrip_with_umlauts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path, system_language="de-DE")
            store.update(hotkey="ctrl+space", recording_mode="toggle")
            store.confirm_ui_language("de")
            loaded = SettingsStore(path, system_language="de-DE").current
            self.assertEqual(loaded.ui_language, "de")
            self.assertEqual(loaded.hotkey, "ctrl+space")
            self.assertEqual(loaded.recording_mode, "toggle")

    def test_new_cross_platform_preferences_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)
            store.update(
                microphone_gain=1.75,
                hotkey_enabled=False,
                auto_profile_switching=False,
                target_language="de",
                overlay_position="custom",
            )
            loaded = SettingsStore(path).current
            self.assertEqual(loaded.microphone_gain, 1.75)
            self.assertFalse(loaded.hotkey_enabled)
            self.assertFalse(loaded.auto_profile_switching)
            self.assertEqual(loaded.target_language, "de")
            self.assertEqual(loaded.overlay_position, "custom")

    def test_untrusted_settings_are_sanitized_and_clamped(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({
                "ui_language": "../../bad",
                "recording_mode": "execute",
                "hotkey": "ctrl+alt+delete+bad+bad",
                "microphone_gain": 999,
                "max_recording_seconds": -1,
                "overlay_opacity": 99,
                "hotkey_include_apps": ["chrome.exe", "x" * 5000],
            }), encoding="utf-8")
            loaded = SettingsStore(path, system_language="de-DE").current
            self.assertEqual(loaded.ui_language, "de")
            self.assertEqual(loaded.recording_mode, "hold")
            self.assertLessEqual(loaded.microphone_gain, 8.0)
            self.assertGreaterEqual(loaded.max_recording_seconds, 10)
            self.assertLessEqual(loaded.overlay_opacity, 1.0)
            self.assertTrue(all(len(item) <= 180 for item in loaded.hotkey_include_apps))

    def test_safe_application_wildcards_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)
            store.update(hotkey_include_apps=["chrome*.exe", "code?", "bad/command"])
            loaded = SettingsStore(path).current
            self.assertEqual(loaded.hotkey_include_apps, ["chrome*.exe", "code?"])

    def test_language_routes_are_sanitized_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)
            store.update(language_target_rules={"en": "de", "fr": "it", "../../bad": "de"})
            loaded = SettingsStore(path).current
            self.assertEqual(loaded.language_target_rules, {"en": "de", "fr": "it"})


if __name__ == "__main__":
    unittest.main()


def test_private_mode_and_disabled_history_cannot_leave_orphan_audio_settings():
    from localvoice.core.models import AppSettings, Profile

    private_settings = AppSettings.from_dict({"private_mode": True, "save_history": True, "save_audio": True})
    assert private_settings.private_mode
    assert not private_settings.save_history
    assert not private_settings.save_audio

    no_history = AppSettings.from_dict({"private_mode": False, "save_history": False, "save_audio": True})
    assert not no_history.save_history
    assert not no_history.save_audio

    profile = Profile.from_dict({"private_mode": False, "save_history": False, "save_audio": True})
    assert not profile.save_history
    assert not profile.save_audio


def test_pre_140_settings_migrate_without_deleting_models_or_history():
    import json
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "settings.json"
        path.write_text(json.dumps({
            "ui_language": "de",
            "ui_size": "large",
            "beam_size": 5,
            "noise_reduction": True,
            "preferred_languages": ["en", "de", "fr"],
            "first_run_complete": True,
        }), encoding="utf-8")
        loaded = SettingsStore(path, system_language="de-DE").current
        assert loaded.ui_size == "medium"
        assert loaded.recognition_mode == "balanced"
        assert loaded.beam_size == 2
        assert loaded.preload_model is True
        assert loaded.noise_reduction is False
        assert loaded.preferred_languages[0] == "de"
        assert loaded.first_run_complete is False


def test_pre_15_large_ui_is_migrated_once_to_new_medium(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"ui_language":"de","ui_size":"large","settings_schema_version":4}', encoding="utf-8")
    store = SettingsStore(path)
    assert store.current.ui_size == "medium"
    assert store.current.settings_schema_version == 9
    store.current.ui_size = "large"
    store.save()
    reloaded = SettingsStore(path, system_language="de-DE")
    assert reloaded.current.ui_size == "large"
