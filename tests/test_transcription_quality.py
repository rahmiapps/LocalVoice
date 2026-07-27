from __future__ import annotations

import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from localvoice.core.audio import AudioProcessor, AudioRecorder
from localvoice.core.transcription import WhisperEngine


def _wav(path: Path, seconds: float = 3.0) -> None:
    samples = np.zeros(int(AudioRecorder.SAMPLE_RATE * seconds), dtype=np.float32)
    AudioRecorder._write_wav(path, samples)


class _Segment:
    def __init__(self, text: str, score: float) -> None:
        self.text = text
        self.avg_logprob = score


class _LanguageModel:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def transcribe(self, _path: str, **kwargs):
        self.calls.append(kwargs)
        language = kwargs.get("language")
        if language == "de":
            return iter([_Segment("Wir testen das.", -0.23)]), SimpleNamespace(language="de", language_probability=1.0)
        return iter([_Segment("We'll test this.", -0.20)]), SimpleNamespace(language="en", language_probability=0.80)


def test_short_auto_dictation_compares_first_preferred_language(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "short.wav"
        _wav(path, 3.0)
        engine = WhisperEngine()
        fake = _LanguageModel()
        engine._model = fake
        monkeypatch.setattr(engine, "resolve_model_path", lambda *_args, **_kwargs: Path(directory))
        monkeypatch.setattr(engine, "_load_model", lambda *_args, **_kwargs: None)

        text, detected, _probability = engine.transcribe(
            path,
            language="auto",
            preferred_languages=["de", "en", "fr"],
            recognition_mode="balanced",
            beam_size=5,
        )

        assert text == "Wir testen das."
        assert detected == "de"
        assert fake.calls[0]["beam_size"] == 1
        assert fake.calls[0]["temperature"] == 0.0
        assert fake.calls[0]["language_detection_segments"] == 2
        assert fake.calls[0]["without_timestamps"] is True
        assert fake.calls[0]["vad_filter"] is False
        assert "Deutsche Diktataufnahme" in fake.calls[0]["initial_prompt"]


class _VadRecoveryModel:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def transcribe(self, _path: str, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("vad_filter"):
            return iter([_Segment("Stücke.", -0.20)]), SimpleNamespace(language="de", language_probability=1.0)
        return iter([_Segment("Eigentlich nimmt er das schneller auf und erkennt den ganzen Satz.", -0.30)]), SimpleNamespace(language="de", language_probability=1.0)


def test_balanced_long_recording_uses_one_non_vad_pass_for_speed(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "long.wav"
        _wav(path, 18.0)
        engine = WhisperEngine()
        fake = _VadRecoveryModel()
        engine._model = fake
        monkeypatch.setattr(engine, "resolve_model_path", lambda *_args, **_kwargs: Path(directory))
        monkeypatch.setattr(engine, "_load_model", lambda *_args, **_kwargs: None)

        text, detected, _probability = engine.transcribe(
            path,
            language="de",
            preferred_languages=["de", "en"],
            recognition_mode="balanced",
        )

        assert detected == "de"
        assert text.startswith("Eigentlich nimmt er")
        assert [call["vad_filter"] for call in fake.calls] == [False]


def test_accurate_mode_recovers_empty_or_fragmented_vad_result(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "accurate-long.wav"
        _wav(path, 18.0)
        engine = WhisperEngine()
        fake = _VadRecoveryModel()
        engine._model = fake
        monkeypatch.setattr(engine, "resolve_model_path", lambda *_args, **_kwargs: Path(directory))
        monkeypatch.setattr(engine, "_load_model", lambda *_args, **_kwargs: None)
        text, detected, _probability = engine.transcribe(
            path, language="de", preferred_languages=["de", "en"], recognition_mode="accurate"
        )
        assert detected == "de"
        assert text.startswith("Eigentlich nimmt er")
        assert [call["vad_filter"] for call in fake.calls] == [True, False]


def test_speech_safe_noise_reduction_keeps_quiet_consonant_energy(tmp_path: Path) -> None:
    path = tmp_path / "speech.wav"
    rate = AudioRecorder.SAMPLE_RATE
    t = np.arange(rate * 2, dtype=np.float32) / rate
    signal = 0.025 * np.sin(2 * np.pi * 180 * t) + 0.006 * np.sin(2 * np.pi * 3200 * t)
    AudioRecorder._write_wav(path, signal)
    processed = AudioProcessor.process(path, noise_reduction=True, normalize=False, gain=1.0)
    with wave.open(str(processed), "rb") as wav:
        output = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    assert output.size == signal.size
    # The new conditioner must not erase quiet speech components.
    assert float(np.sqrt(np.mean(output ** 2))) >= float(np.sqrt(np.mean(signal ** 2))) * 0.60
