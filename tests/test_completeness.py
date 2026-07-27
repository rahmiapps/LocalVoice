from __future__ import annotations

import os
import queue
import tempfile
import threading
import time
import wave
import zipfile
from pathlib import Path

import numpy as np
import pytest

from localvoice.core.audio import AudioProcessor, AudioRecorder
from localvoice.core.models import AppSettings, Profile
from localvoice.core.postprocess import TextPostProcessor
from localvoice.core.security import SecureStore
from localvoice.core.transcription import ModelMissingError, WhisperEngine
from localvoice.core.translation import LocalTranslator
from localvoice.core.validation import normalize_hotkey, normalize_max_recording_seconds


class _FakeStream:
    def stop(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_unlimited_recording_is_preserved_but_negative_input_is_not() -> None:
    assert normalize_max_recording_seconds(0, 1800) == 0
    assert AppSettings.from_dict({"max_recording_seconds": 0}).max_recording_seconds == 0
    assert AppSettings.from_dict({"max_recording_seconds": -1}).max_recording_seconds == 1800


def test_full_profile_roundtrip_and_sanitization() -> None:
    with tempfile.TemporaryDirectory() as directory:
        model_dir = Path(directory) / "model"
        model_dir.mkdir()
        original = Profile(
            id=7,
            name="Français → Deutsch",
            applications=["chrome*.exe"],
            hotkey="ctrl+space",
            secondary_hotkey="mouse4",
            recording_mode="toggle",
            microphone_device=4,
            input_language="fr",
            preferred_languages=["fr", "en"],
            target_language="de",
            language_target_rules={"en": "de", "fr": "de"},
            translation_enabled=True,
            translation_intermediate_language="en",
            language_detection_threshold=0.7,
            show_original_and_translation=True,
            output_mode="preview",
            auto_press_enter=True,
            spoken_commands=False,
            remove_filler_words=True,
            numbers_as_digits=True,
            automatic_punctuation=False,
            restore_clipboard_after_insert=False,
            clipboard_clear_seconds=15,
            model_size="medium",
            local_model_path=str(model_dir),
            compute_device="cpu",
            compute_type="int8",
            beam_size=7,
            noise_reduction=False,
            normalize_audio=False,
            microphone_gain=2.0,
            silence_stop_enabled=True,
            silence_seconds=9,
            silence_threshold=0.04,
            max_recording_seconds=0,
            start_stop_sound=False,
            save_history=False,
            save_audio=False,
            private_mode=True,
            writing_style="email",
            enabled=True,
        )
        loaded = Profile.from_dict(original.to_dict())
        assert loaded.to_dict() == original.to_dict()


def test_audio_recorder_streams_blocks_to_disk_without_unbounded_chunk_list() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = AudioRecorder()
        path = Path(directory) / "recording-streamed.wav"
        blocks: queue.Queue[bytes | None] = queue.Queue(maxsize=recorder.MAX_QUEUED_BLOCKS)
        recorder._recording_path = path
        recorder._writer_queue = blocks
        recorder._writer_thread = threading.Thread(target=recorder._writer_loop, args=(path, blocks), daemon=True)
        recorder._started_at = time.monotonic() - 1
        recorder._last_voice_at = recorder._started_at
        recorder._stream = _FakeStream()
        recorder._writer_thread.start()
        signal = np.full((recorder.BLOCK_SIZE, 1), 0.05, dtype=np.float32)
        for _ in range(8):
            recorder._callback(signal, recorder.BLOCK_SIZE, object(), None)
        result, duration = recorder.stop()
        assert result == path
        assert duration > 0
        assert not hasattr(recorder, "_chunks")
        with wave.open(str(path), "rb") as wav:
            assert wav.getnframes() == recorder.BLOCK_SIZE * 8


def test_audio_processor_handles_a_longer_file_in_chunks() -> None:
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "long.wav"
        # Several processing chunks, without requiring excessive test memory.
        samples = np.linspace(-0.25, 0.25, AudioProcessor.CHUNK_FRAMES * 3 + 123, dtype=np.float32)
        AudioRecorder._write_wav(source, samples)
        processed = AudioProcessor.process(source, noise_reduction=True, normalize=True, gain=1.25)
        with wave.open(str(processed), "rb") as wav:
            assert wav.getnchannels() == 1
            assert wav.getnframes() == samples.size


def test_pin_lockout_state_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "security.json"
        store = SecureStore(path)
        store.enable_pin("1234")
        store.lock()
        for _ in range(store.MAX_FAILED_ATTEMPTS):
            assert not store.unlock("9999")
        assert store.lockout_seconds_remaining > 0
        reopened = SecureStore(path)
        assert reopened.is_locked
        assert reopened.lockout_seconds_remaining > 0
        assert not reopened.unlock("1234")


def _write_argos_archive(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)


def test_translation_package_validation_accepts_safe_archive() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "de_en.argosmodel"
        _write_argos_archive(path, {"metadata.json": b"{}", "model/model.bin": b"safe"})
        assert LocalTranslator._validate_download(path) == path.resolve()


def test_translation_package_validation_rejects_path_traversal() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bad.argosmodel"
        _write_argos_archive(path, {"../outside": b"bad"})
        with pytest.raises(RuntimeError, match="unsafe path"):
            LocalTranslator._validate_download(path)


def test_translation_package_validation_rejects_symlinks() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "link.argosmodel"
        with zipfile.ZipFile(path, "w") as archive:
            info = zipfile.ZipInfo("model/link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, "target")
        with pytest.raises(RuntimeError, match="symbolic links"):
            LocalTranslator._validate_download(path)


def test_custom_model_directory_rejects_symlink() -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symbolic links unsupported")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        model = root / "model"
        model.mkdir()
        (model / "config.json").write_text("{}", encoding="utf-8")
        outside = root / "outside.bin"
        outside.write_bytes(b"weights")
        try:
            (model / "model.bin").symlink_to(outside)
        except OSError:
            pytest.skip("symbolic links unavailable in this environment")
        engine = WhisperEngine()
        with pytest.raises(ModelMissingError, match="MODEL_MISSING"):
            engine.resolve_model_path("small", str(model))


def test_automatic_punctuation_can_be_disabled() -> None:
    processor = TextPostProcessor()
    result = processor.process(
        "hello world",
        language="en",
        automatic_punctuation=False,
        spoken_commands=False,
    )
    assert result == "hello world"



def test_hotkey_validation_matches_cross_platform_function_key_limits() -> None:
    assert normalize_hotkey("Ctrl + NumPad5") == "ctrl+num5"
    assert normalize_hotkey("mouse4") == "mouse4"
    assert normalize_hotkey("f24") == "f24"
    assert normalize_hotkey("f25", default="") == ""
    assert normalize_hotkey("ctrl+alt+../../bad", default="") == ""


def test_active_window_center_uses_real_geometry() -> None:
    pytest.importorskip("PySide6")
    from localvoice.core.system import ActiveWindowContext

    context = ActiveWindowContext("editor", "42", x=100, y=200, width=800, height=600)
    assert context.center == (500, 500)


def test_linux_keyring_retirement_overwrites_old_master_key(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types
    import base64

    previous = b"x" * 32
    values = {("LocalVoice", SecureStore._keyring_account()): base64.b64encode(previous).decode("ascii")}

    class Backend:
        priority = 1

    fake = types.SimpleNamespace(
        get_keyring=lambda: Backend(),
        set_password=lambda service, account, value: values.__setitem__((service, account), value),
        get_password=lambda service, account: values.get((service, account)),
        delete_password=lambda service, account: values.pop((service, account), None),
    )
    monkeypatch.setitem(sys.modules, "keyring", fake)
    assert SecureStore._retire_keyring_secret(previous)
    assert values.get(("LocalVoice", SecureStore._keyring_account())) != base64.b64encode(previous).decode("ascii")


def test_preview_and_output_failure_discard_uncommitted_encrypted_audio() -> None:
    root = Path(__file__).resolve().parents[1]
    controller = (root / "localvoice/core/controller.py").read_text(encoding="utf-8")
    window = (root / "localvoice/ui/main_window.py").read_text(encoding="utf-8")
    assert "not self.settings.save_history" in controller
    assert "def discard_result" in controller
    assert "not history_persisted" in controller
    assert "self.controller.discard_result(result)" in window


def test_windows_activation_does_not_restore_a_maximized_window() -> None:
    from localvoice.core.window_activation import activate_windows_window

    class FakeUser32:
        def __init__(self, iconic: bool) -> None:
            self.iconic = iconic
            self.show_calls: list[tuple[int, int]] = []

        def IsIconic(self, _hwnd: int) -> int:
            return int(self.iconic)

        def ShowWindow(self, hwnd: int, command: int) -> int:
            self.show_calls.append((hwnd, command))
            return 1

        def BringWindowToTop(self, _hwnd: int) -> int:
            return 1

        def SetForegroundWindow(self, _hwnd: int) -> int:
            return 1

    maximized = FakeUser32(iconic=False)
    assert activate_windows_window(maximized, 123) is True
    assert maximized.show_calls == []

    minimized = FakeUser32(iconic=True)
    assert activate_windows_window(minimized, 456) is True
    assert minimized.show_calls == [(456, 9)]
