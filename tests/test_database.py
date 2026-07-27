import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localvoice.core.database import LocalDatabase
from localvoice.core.models import Profile, TranscriptionResult
from localvoice.core.security import SecureStore


class DatabaseTests(unittest.TestCase):
    @staticmethod
    def _result(**overrides):
        values = dict(
            original_text="Hallo Welt",
            final_text="Hello world",
            detected_language="de",
            language_probability=0.99,
            translated=True,
            duration_seconds=1.5,
            word_count=2,
            target_application="editor.exe",
            audio_path="",
        )
        values.update(overrides)
        return TranscriptionResult(**values)

    def test_history_is_encrypted_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secure = SecureStore(root / "security.json")
            db = LocalDatabase(secure, root / "localvoice.db")
            db.add_history(self._result())
            raw = (root / "localvoice.db").read_bytes()
            self.assertNotIn(b"Hallo Welt", raw)
            self.assertNotIn(b"Hello world", raw)
            self.assertNotIn(b"editor.exe", raw)
            rows = db.list_history()
            self.assertEqual(rows[0]["final_text"], "Hello world")
            self.assertEqual(rows[0]["target_application"], "editor.exe")

    def test_vocabulary_and_full_profiles_are_encrypted_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secure = SecureStore(root / "security.json")
            db = LocalDatabase(secure, root / "localvoice.db")
            entry_id = db.add_vocabulary("dayter x", "DateraX", "de", True, False)
            profile = Profile(
                name="Browser",
                applications=["chrome.exe"],
                hotkey="f9",
                secondary_hotkey="mouse4",
                recording_mode="toggle",
                microphone_device=3,
                input_language="auto",
                preferred_languages=["en", "fr"],
                target_language="de",
                language_target_rules={"de": "en", "fr": "de"},
                translation_enabled=True,
                translation_intermediate_language="en",
                language_detection_threshold=0.65,
                show_original_and_translation=True,
                output_mode="preview",
                auto_press_enter=True,
                spoken_commands=False,
                remove_filler_words=True,
                numbers_as_digits=True,
                automatic_punctuation=False,
                model_size="medium",
                compute_device="cpu",
                compute_type="int8",
                beam_size=7,
                noise_reduction=False,
                normalize_audio=False,
                microphone_gain=1.5,
                silence_stop_enabled=True,
                silence_seconds=6.0,
                silence_threshold=0.03,
                max_recording_seconds=0,
                start_stop_sound=False,
                save_history=False,
                private_mode=True,
                writing_style="email",
            )
            profile_id = db.save_profile(profile)
            raw = (root / "localvoice.db").read_bytes()
            for secret in (b"dayter x", b"DateraX", b"Browser", b"chrome.exe"):
                self.assertNotIn(secret, raw)
            entries = db.list_vocabulary()
            self.assertEqual(entries[0]["id"], entry_id)
            self.assertEqual(entries[0]["written_form"], "DateraX")
            loaded = db.list_profiles()[0]
            self.assertEqual(loaded.id, profile_id)
            self.assertEqual(loaded.secondary_hotkey, "mouse4")
            self.assertEqual(loaded.recording_mode, "toggle")
            self.assertEqual(loaded.language_target_rules, {"de": "en", "fr": "de"})
            self.assertEqual(loaded.microphone_device, 3)
            self.assertEqual(loaded.language_detection_threshold, 0.65)
            self.assertFalse(loaded.automatic_punctuation)
            self.assertEqual(loaded.model_size, "medium")
            self.assertEqual(loaded.max_recording_seconds, 0)
            self.assertFalse(loaded.start_stop_sound)
            self.assertTrue(loaded.private_mode)
            self.assertTrue(loaded.show_original_and_translation)
            self.assertEqual(loaded.output_mode, "preview")
            self.assertEqual(loaded.writing_style, "email")

    def test_history_edit_csv_safety_and_encrypted_audio_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            audio_dir = data_dir / "audio"
            audio_dir.mkdir(parents=True)
            secure = SecureStore(root / "security.json")
            with patch("localvoice.core.database.DATA_DIR", data_dir):
                db = LocalDatabase(secure, root / "localvoice.db")
                plaintext = root / "voice.wav"
                plaintext.write_bytes(b"RIFF" + b"voice-data" * 200)
                encrypted = audio_dir / "recording-test.lva"
                secure.encrypt_file(plaintext, encrypted)
                entry_id = db.add_history(self._result(final_text="=2+2", word_count=1, audio_path=str(encrypted)))
                self.assertIsNotNone(entry_id)
                self.assertTrue(db.update_history_text(int(entry_id), "Original geändert", "+SUM(A1:A2)"))
                exported_csv = root / "history.csv"
                db.export_history(exported_csv, "csv")
                with exported_csv.open(encoding="utf-8-sig", newline="") as file:
                    row = next(csv.DictReader(file))
                self.assertTrue(str(row["final_text"]).startswith("'"))
                exported_audio = root / "export.wav"
                self.assertTrue(db.export_history_audio(int(entry_id), exported_audio))
                self.assertEqual(exported_audio.read_bytes(), plaintext.read_bytes())
                self.assertGreaterEqual(db.clear_saved_audio(), 1)
                self.assertFalse(encrypted.exists())
                self.assertEqual(db.get_history(int(entry_id))["audio_path"], "")


if __name__ == "__main__":
    unittest.main()


def test_history_statistics_and_audio_path_privacy(tmp_path, monkeypatch):
    from localvoice.core import database as database_module
    from localvoice.core.models import TranscriptionResult

    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path)
    secure = SecureStore(tmp_path / "security-stats.json")
    db = LocalDatabase(secure, tmp_path / "stats.db")
    audio = audio_root / "recording-private.lva"
    audio.write_bytes(b"encrypted")
    result = TranscriptionResult(
        original_text="hello",
        final_text="hallo welt",
        detected_language="en",
        language_probability=0.9,
        translated=True,
        duration_seconds=12.5,
        word_count=2,
        target_application="editor.exe",
        audio_path=str(audio),
    )
    entry_id = db.add_history(result)
    assert entry_id
    raw = (tmp_path / "stats.db").read_bytes()
    assert str(tmp_path).encode() not in raw
    row = db.get_history(entry_id)
    assert row and row["audio_path"] == "recording-private.lva"
    stats = db.history_statistics()
    assert stats["total_items"] == 1
    assert stats["total_words"] == 2
    assert stats["translated_items"] == 1
    assert stats["audio_items"] == 1


def test_legacy_plaintext_audio_is_migrated_and_orphans_are_removed(tmp_path, monkeypatch):
    from localvoice.core import database as database_module

    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path)
    secure = SecureStore(tmp_path / "security-legacy.json")
    db_path = tmp_path / "legacy.db"
    db = LocalDatabase(secure, db_path)
    audio_root = tmp_path / "audio"
    audio_root.mkdir(exist_ok=True)
    legacy = audio_root / "recording-legacy.wav"
    legacy_payload = b"RIFF" + b"legacy-voice" * 100
    legacy.write_bytes(legacy_payload)
    orphan = audio_root / "recording-orphan.wav"
    orphan.write_bytes(b"RIFF-orphan")
    entry_id = db.add_history(DatabaseTests._result(audio_path=str(legacy)))
    assert entry_id

    migrated = LocalDatabase(secure, db_path)
    row = migrated.get_history(int(entry_id))
    assert row and row["audio_path"] == "recording-legacy.lva"
    assert not legacy.exists()
    assert not orphan.exists()
    encrypted = audio_root / "recording-legacy.lva"
    assert encrypted.exists() and legacy_payload not in encrypted.read_bytes()
    exported = tmp_path / "legacy-export.wav"
    assert migrated.export_history_audio(int(entry_id), exported)
    assert exported.read_bytes() == legacy_payload


def test_audio_retention_clears_database_reference(tmp_path, monkeypatch):
    import os
    import time
    from localvoice.core import database as database_module

    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path)
    secure = SecureStore(tmp_path / "security-retention.json")
    db = LocalDatabase(secure, tmp_path / "retention.db")
    audio_root = tmp_path / "audio"
    audio_root.mkdir(exist_ok=True)
    audio = audio_root / "recording-old.lva"
    audio.write_bytes(b"encrypted")
    old = time.time() - 5 * 86400
    os.utime(audio, (old, old))
    entry_id = db.add_history(DatabaseTests._result(audio_path=str(audio)))
    assert entry_id
    assert db.purge_saved_audio(1) == 1
    row = db.get_history(int(entry_id))
    assert row and row["audio_path"] == ""
    assert not audio.exists()


def test_uncommitted_audio_discard_is_confined_to_audio_directory(monkeypatch, tmp_path):
    from localvoice.core import database as database_module

    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path)
    secure = SecureStore(tmp_path / "security-discard.json")
    db = LocalDatabase(secure, tmp_path / "discard.db")
    audio_root = tmp_path / "audio"
    audio_root.mkdir(exist_ok=True)
    audio = audio_root / "recording-preview.lva"
    audio.write_bytes(b"encrypted")
    outside = tmp_path / "outside.lva"
    outside.write_bytes(b"do-not-delete")

    assert db.discard_saved_audio(audio.name)
    assert not audio.exists()
    assert not db.discard_saved_audio(str(outside))
    assert outside.exists()
