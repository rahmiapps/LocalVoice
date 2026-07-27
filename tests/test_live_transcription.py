from __future__ import annotations

import queue
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from localvoice.core.models import AppSettings, Profile
from localvoice.core.streaming import LiveTranscriptionSession, merge_transcript_text
from localvoice.core.transcription import WhisperEngine


def test_overlapping_words_are_not_duplicated() -> None:
    assert merge_transcript_text(
        "Das ist ein längerer Test",
        "ein längerer Test und er funktioniert.",
    ) == "Das ist ein längerer Test und er funktioniert."


def test_character_overlap_supports_text_without_spaces() -> None:
    assert merge_transcript_text("这是一个测试", "一个测试并且成功") == "这是一个测试并且成功"


class _FakeRecorder:
    def __init__(self, blocks: list[bytes]) -> None:
        self.recording_sample_rate = 16_000
        self.live_audio_dropped = False
        self._blocks: queue.Queue[bytes | None] = queue.Queue()
        for block in blocks:
            self._blocks.put(block)
        self._blocks.put(None)

    def take_live_block(self, timeout: float = 0.2) -> bytes | None:
        del timeout
        return self._blocks.get_nowait()


class _FakeWhisper:
    def __init__(self) -> None:
        self.calls = 0

    def resolved_device_for(self, requested: str) -> str:
        del requested
        return "cpu"

    def transcribe(self, _path: Path, **kwargs):
        assert kwargs["streaming"] is True
        assert kwargs["beam_size"] == 1
        self.calls += 1
        if self.calls == 1:
            return "Hallo Welt", "de", 0.95
        return "Welt, heute funktioniert es.", "de", 0.96


def test_live_session_processes_during_recording_and_merges_tail() -> None:
    rate = 16_000
    # Four seconds split into PortAudio-sized blocks. A 3-second chunk plus the
    # final overlapping tail produces two incremental calls.
    audio = (np.sin(np.arange(rate * 4) * 0.03) * 2000).astype("<i2").tobytes()
    block_bytes = 1024 * 2
    blocks = [audio[index:index + block_bytes] for index in range(0, len(audio), block_bytes)]
    recorder = _FakeRecorder(blocks)
    whisper = _FakeWhisper()
    settings = AppSettings(
        model_size="small",
        input_language="de",
        live_chunk_seconds=3.0,
        live_overlap_seconds=0.8,
        normalize_audio=False,
        auto_microphone_gain=False,
    )
    partials: list[str] = []
    session = LiveTranscriptionSession(
        recorder,  # type: ignore[arg-type]
        whisper,  # type: ignore[arg-type]
        settings,
        on_partial=partials.append,
    )
    session.start()
    result = session.finish(5)
    assert result is not None and result.complete
    assert result.chunk_count == 2
    assert result.text == "Hallo Welt, heute funktioniert es."
    assert partials[-1] == result.text


def test_model_instance_is_reused_for_identical_signature(monkeypatch, tmp_path: Path) -> None:
    constructions: list[dict[str, object]] = []

    class FakeModel:
        def __init__(self, _path: str, **kwargs) -> None:
            constructions.append(kwargs)

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))
    engine = WhisperEngine()
    engine._load_model(tmp_path, "cpu", "int8")
    first = engine._model
    engine._load_model(tmp_path, "cpu", "int8")
    assert engine._model is first
    assert len(constructions) == 1
    assert constructions[0]["num_workers"] == 1
    assert int(constructions[0]["cpu_threads"]) >= 2


def test_live_settings_are_enabled_and_roundtrip_in_profiles() -> None:
    settings = AppSettings.from_dict({})
    assert settings.live_transcription_enabled
    assert settings.live_preview_enabled
    assert 3.0 <= settings.live_chunk_seconds <= 12.0

    profile = Profile.from_dict({
        "live_transcription_enabled": False,
        "live_preview_enabled": False,
        "live_chunk_seconds": 9.5,
        "live_overlap_seconds": 1.2,
    })
    assert not profile.live_transcription_enabled
    assert not profile.live_preview_enabled
    assert profile.live_chunk_seconds == 9.5
    assert profile.live_overlap_seconds == 1.2


def test_live_controls_and_partial_overlay_are_wired_in_source() -> None:
    root = Path(__file__).resolve().parents[1]
    dialogs = (root / "localvoice/ui/dialogs.py").read_text(encoding="utf-8")
    controller = (root / "localvoice/core/controller.py").read_text(encoding="utf-8")
    overlay = (root / "localvoice/ui/overlay.py").read_text(encoding="utf-8")
    assert "self.live_transcription" in dialogs
    assert "LiveTranscriptionSession" in controller
    assert "partial_text_changed" in controller
    assert "def set_partial_text" in overlay
