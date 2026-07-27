from __future__ import annotations

import os
import threading
import time
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from .audio import AudioRecorder
from .models import AppSettings
from .paths import TEMP_DIR, ensure_directories
from .transcription import WhisperEngine


@dataclass(slots=True)
class StreamingTranscript:
    text: str = ""
    detected_language: str = "unknown"
    language_probability: float = 0.0
    audio_seconds: float = 0.0
    processing_seconds: float = 0.0
    chunk_count: int = 0
    complete: bool = False
    dropped_audio: bool = False

    @property
    def realtime_factor(self) -> float:
        return self.processing_seconds / max(0.001, self.audio_seconds)


def _normalized_token(value: str) -> str:
    return value.casefold().strip(".,!?;:()[]{}\"'„“”«»…-–—")


def merge_transcript_text(previous: str, current: str, *, max_overlap_words: int = 18) -> str:
    """Merge overlapping chunk transcripts without repeating boundary words.

    Streaming chunks deliberately overlap so words cut at a chunk boundary are
    heard twice. The longest normalized word overlap is removed. Languages that
    commonly omit spaces (for example Chinese) additionally use a bounded
    character overlap.
    """
    left = str(previous or "").strip()
    right = str(current or "").strip()
    if not left:
        return right
    if not right:
        return left

    left_words = left.split()
    right_words = right.split()
    limit = min(max_overlap_words, len(left_words), len(right_words))
    for count in range(limit, 0, -1):
        left_tail = [_normalized_token(item) for item in left_words[-count:]]
        right_head = [_normalized_token(item) for item in right_words[:count]]
        if left_tail == right_head and any(left_tail):
            # Preserve punctuation/casing from the newer chunk at the overlap;
            # it has more right-hand acoustic context for the boundary word.
            merged_words = [*left_words[:-count], *right_words[:count], *right_words[count:]]
            return " ".join(merged_words).strip()

    # Character overlap is useful for CJK text and for punctuation-only spacing
    # differences. Keep the search small so unrelated phrases cannot collapse.
    compact_left = left.rstrip()
    compact_right = right.lstrip()
    for count in range(min(48, len(compact_left), len(compact_right)), 2, -1):
        if compact_left[-count:].casefold() == compact_right[:count].casefold():
            return compact_left + compact_right[count:]
    return f"{left} {right}".strip()


def _condition_pcm_chunk(
    pcm: bytes,
    *,
    sample_rate: int,
    gain: float,
    normalize: bool,
    auto_gain: bool,
    noise_reduction: bool,
) -> bytes:
    """Fast, bounded one-pass conditioning for live chunks.

    The full recording processor intentionally performs a deeper two-pass scan.
    Live transcription instead needs low latency. This routine removes DC,
    gently attenuates the estimated noise floor and applies a clipping-safe
    speech RMS gain without loading more than one small chunk into memory.
    """
    del sample_rate  # Reserved for future frequency-aware filters.
    if not pcm:
        return b""
    audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    if not audio.size:
        return b""
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    audio -= float(np.mean(audio, dtype=np.float64))
    magnitude = np.abs(audio)
    noise_floor = float(np.percentile(magnitude, 18)) if magnitude.size else 0.0
    if noise_reduction and noise_floor > 0.0:
        low = max(0.0012, noise_floor * 0.8)
        high = max(low + 1e-6, noise_floor * 3.0)
        weight = np.clip((magnitude - low) / (high - low), 0.0, 1.0)
        audio *= 0.78 + 0.22 * weight

    manual_gain = max(0.25, min(float(gain), 8.0))
    audio *= manual_gain
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    scale = 1.0
    if normalize and peak > 0.0004:
        speech_gate = max(0.0025, noise_floor * 1.8)
        speech = audio[np.abs(audio) >= speech_gate]
        if auto_gain and speech.size >= 160:
            speech_rms = float(np.sqrt(np.mean(np.square(speech, dtype=np.float64))))
            scale = min(6.0, 0.115 / max(speech_rms, 0.004))
        scale = min(scale, 0.92 / max(peak, 1e-6))
        scale = max(0.55, scale)
    audio = np.clip(audio * scale, -1.0, 1.0)
    return (audio * 32767.0).astype("<i2", copy=False).tobytes()


class LiveTranscriptionSession:
    """Incrementally transcribe bounded overlapping chunks while recording.

    The final stop path reuses the already decoded text and only waits for the
    last tail chunk. This does not claim that Medium can run in real time on
    every CPU; it spreads the work across the speaking time and reports whether
    the local hardware kept up. The original full recording remains the source
    of truth and is used as a fallback if live audio was dropped or a chunk
    failed.
    """

    MIN_TAIL_SECONDS = 0.20

    def __init__(
        self,
        recorder: AudioRecorder,
        whisper: WhisperEngine,
        settings: AppSettings,
        *,
        hotwords: list[str] | None = None,
        on_partial: Callable[[str], None] | None = None,
        on_state: Callable[[str], None] | None = None,
    ) -> None:
        self.recorder = recorder
        self.whisper = whisper
        self.settings = settings
        self.hotwords = list(hotwords or [])[:60]
        self.on_partial = on_partial
        self.on_state = on_state
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._done = threading.Event()
        self._result = StreamingTranscript()
        self._error = ""
        self._lock = threading.RLock()

    @property
    def error(self) -> str:
        return self._error

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="LocalVoiceLiveTranscription")
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()

    def finish(self, timeout: float = 180.0) -> StreamingTranscript | None:
        thread = self._thread
        if thread is None:
            return None
        thread.join(max(0.1, min(float(timeout), 300.0)))
        if thread.is_alive():
            self._error = self._error or "Live transcription did not finish in time."
            return None
        with self._lock:
            return self._result

    @staticmethod
    def _write_chunk(path: Path, pcm: bytes, sample_rate: int) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with wave.open(str(temporary), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(int(sample_rate))
            wav.writeframes(pcm)
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        temporary.replace(path)

    def _transcribe_chunk(
        self,
        pcm: bytes,
        sample_rate: int,
        accumulated: str,
        detected_language: str,
    ) -> tuple[str, str, float, float]:
        conditioned = _condition_pcm_chunk(
            pcm,
            sample_rate=sample_rate,
            gain=self.settings.microphone_gain,
            normalize=self.settings.normalize_audio,
            auto_gain=self.settings.auto_microphone_gain,
            noise_reduction=self.settings.noise_reduction,
        )
        if not conditioned:
            return "", detected_language, 0.0, 0.0
        ensure_directories()
        path = TEMP_DIR / f"live-{uuid.uuid4().hex}.wav"
        self._write_chunk(path, conditioned, sample_rate)
        try:
            # Once a language was confidently detected, fixing it for later
            # chunks removes repeated language detection and improves continuity.
            selected_language = self.settings.input_language
            if selected_language == "auto" and detected_language not in {"", "unknown", "auto"}:
                selected_language = detected_language
            started = time.perf_counter()
            text, detected, probability = self.whisper.transcribe(
                path,
                model_size=self.settings.model_size,
                language=selected_language,
                preferred_languages=self.settings.preferred_languages,
                prefer_primary_language=self.settings.prefer_primary_language,
                device=self.settings.compute_device,
                compute_type=self.settings.compute_type,
                recognition_mode="fast",
                beam_size=1,
                language_detection_threshold=self.settings.language_detection_threshold,
                hotwords=self.hotwords,
                local_model_path=self.settings.local_model_path,
                context_prompt=accumulated[-320:],
                streaming=True,
            )
            return text, detected, probability, time.perf_counter() - started
        finally:
            path.unlink(missing_ok=True)

    def _run(self) -> None:
        sample_rate = max(8_000, int(self.recorder.recording_sample_rate))
        requested_chunk = max(3.0, min(float(self.settings.live_chunk_seconds), 12.0))
        # Start the first live decode quickly even for Medium. Slower CPUs may
        # show the "catching up" state, but waiting for a long chunk would provide
        # no benefit for the short dictations users make most often.
        overlap_seconds = max(0.35, min(float(self.settings.live_overlap_seconds), requested_chunk / 3.0))
        chunk_frames = max(1, int(sample_rate * requested_chunk))
        overlap_frames = max(1, int(sample_rate * overlap_seconds))
        advance_frames = max(1, chunk_frames - overlap_frames)
        buffer = bytearray()
        accumulated = ""
        detected = "unknown"
        probability = 0.0
        processed_audio = 0.0
        total_input_frames = 0
        processing_seconds = 0.0
        chunk_count = 0
        ended = False

        try:
            while not self._cancel.is_set():
                block = self.recorder.take_live_block(timeout=0.20)
                if block is None:
                    ended = True
                elif block:
                    buffer.extend(block)
                    total_input_frames += len(block) // 2

                while len(buffer) // 2 >= chunk_frames and not self._cancel.is_set():
                    chunk = bytes(buffer[: chunk_frames * 2])
                    text, new_language, new_probability, elapsed = self._transcribe_chunk(
                        chunk, sample_rate, accumulated, detected
                    )
                    processing_seconds += elapsed
                    chunk_count += 1
                    if text:
                        accumulated = merge_transcript_text(accumulated, text)
                        detected = new_language or detected
                        probability = max(probability, new_probability)
                        if self.on_partial:
                            self.on_partial(accumulated)
                    del buffer[: advance_frames * 2]
                    processed_audio += advance_frames / sample_rate
                    if self.on_state:
                        ratio = processing_seconds / max(processed_audio, 0.001)
                        self.on_state("live_behind" if ratio > 1.25 else "live_listening")

                if ended:
                    break

            if not self._cancel.is_set():
                frames = len(buffer) // 2
                # The remaining buffer includes the prior overlap. Only process it
                # when it also contains a meaningful new tail, or when no chunk ran.
                new_tail_frames = frames if chunk_count == 0 else max(0, frames - overlap_frames)
                if frames > 0 and (
                    chunk_count == 0
                    or new_tail_frames >= int(sample_rate * self.MIN_TAIL_SECONDS)
                ):
                    text, new_language, new_probability, elapsed = self._transcribe_chunk(
                        bytes(buffer), sample_rate, accumulated, detected
                    )
                    processing_seconds += elapsed
                    chunk_count += 1
                    if text:
                        accumulated = merge_transcript_text(accumulated, text)
                        detected = new_language or detected
                        probability = max(probability, new_probability)
                        if self.on_partial:
                            self.on_partial(accumulated)
                processed_audio = max(processed_audio, total_input_frames / sample_rate)

            with self._lock:
                self._result = StreamingTranscript(
                    text=accumulated.strip(),
                    detected_language=detected,
                    language_probability=probability,
                    audio_seconds=max(processed_audio, total_input_frames / sample_rate),
                    processing_seconds=processing_seconds,
                    chunk_count=chunk_count,
                    complete=(ended and not self._cancel.is_set() and not self.recorder.live_audio_dropped and not self._error),
                    dropped_audio=self.recorder.live_audio_dropped,
                )
        except Exception as exc:
            self._error = str(exc)[:1000]
            with self._lock:
                self._result = StreamingTranscript(
                    text=accumulated.strip(),
                    detected_language=detected,
                    language_probability=probability,
                    audio_seconds=processed_audio,
                    processing_seconds=processing_seconds,
                    chunk_count=chunk_count,
                    complete=False,
                    dropped_audio=self.recorder.live_audio_dropped,
                )
        finally:
            self._done.set()
