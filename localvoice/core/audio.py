from __future__ import annotations

import math
import os
import queue
import shutil
import threading
import time
import uuid
import wave
from pathlib import Path
from typing import Callable

import numpy as np

try:
    import sounddevice as sd
except ImportError:  # Allows non-audio validation tools to inspect the project.
    sd = None  # type: ignore[assignment]

from .paths import TEMP_DIR, ensure_directories


class AudioRecorder:
    """Record mono audio at a format supported by the selected microphone.

    The PortAudio callback only converts one block and puts it in a bounded
    queue. A dedicated writer thread streams blocks to a private temporary WAV
    file. If storage cannot keep up, recording stops with a clear error instead
    of allowing memory growth or silently producing a corrupted file.
    """

    SAMPLE_RATE = 16_000
    CHANNELS = 1
    BLOCK_SIZE = 1024
    MAX_QUEUED_BLOCKS = 512
    MIN_FREE_DISK_BYTES = 256 * 1024 * 1024
    DISK_CHECK_BLOCKS = 128

    def __init__(self) -> None:
        ensure_directories()
        self._stream: object | None = None
        self._lock = threading.RLock()
        self._started_at = 0.0
        self._last_voice_at = 0.0
        self._silence_fired = False
        self._max_fired = False
        self._cancelled = False
        self._stream_error = ""
        self._storage_stop_requested = False
        self._recording_path: Path | None = None
        self._writer_queue: queue.Queue[bytes | None] | None = None
        self._live_queue: queue.Queue[bytes | None] | None = None
        self._live_audio_dropped = False
        self._writer_thread: threading.Thread | None = None
        self._writer_error = ""
        self._frames_written = 0
        self._recording_sample_rate = self.SAMPLE_RATE
        self._latest_level = 0.0
        self.on_level: Callable[[float], None] | None = None
        self.on_silence: Callable[[], None] | None = None
        self.on_max_duration: Callable[[], None] | None = None
        self.silence_stop_enabled = False
        self.silence_seconds = 4.0
        self.silence_threshold = 0.018
        self.max_duration_seconds = 1800  # 0 means unlimited.

    @staticmethod
    def input_devices() -> list[dict[str, object]]:
        devices: list[dict[str, object]] = []
        if sd is None:
            return devices
        try:
            for index, device in enumerate(sd.query_devices()):
                if int(device.get("max_input_channels", 0)) > 0:
                    devices.append(
                        {
                            "index": index,
                            "name": str(device.get("name", f"Device {index}"))[:300],
                            "hostapi": int(device.get("hostapi", -1)),
                            "default_samplerate": float(
                                device.get("default_samplerate", AudioRecorder.SAMPLE_RATE)
                            ),
                        }
                    )
        except Exception:
            return []
        return devices

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    @property
    def elapsed(self) -> float:
        return max(0.0, time.monotonic() - self._started_at) if self._started_at else 0.0

    @property
    def stream_error(self) -> str:
        return self._stream_error or self._writer_error

    @property
    def recording_sample_rate(self) -> int:
        return int(self._recording_sample_rate)

    @property
    def live_audio_dropped(self) -> bool:
        with self._lock:
            return bool(self._live_audio_dropped)

    def take_live_block(self, timeout: float = 0.20) -> bytes | None:
        """Return a copied PCM block for live transcription.

        ``b""`` means no block arrived before the timeout; ``None`` is the
        end-of-recording sentinel. The queue is bounded and may drop preview
        blocks without ever affecting the full recording written to disk.
        """
        blocks = self._live_queue
        if blocks is None:
            return None
        try:
            return blocks.get(timeout=max(0.01, min(float(timeout), 2.0)))
        except queue.Empty:
            return b""

    @property
    def latest_level(self) -> float:
        """Latest normalized microphone level for GUI polling.

        Polling avoids keeping a bound Qt signal inside PortAudio's native CFFI
        callback. That race was the cause of the Windows error "Signal source has
        been deleted" when a microphone-test dialog closed.
        """
        with self._lock:
            return float(self._latest_level)

    def detach_callbacks(self) -> None:
        """Detach GUI callbacks before the owning QObject/dialog is destroyed.

        PortAudio can deliver one final callback while a stream is being stopped.
        Keeping a bound Qt signal here after its QObject has been deleted produces
        the Python-CFFI "Signal source has been deleted" error seen on Windows.
        """
        with self._lock:
            self.on_level = None
            self.on_silence = None
            self.on_max_duration = None

    def _invoke_callback(self, attribute: str, *args: object) -> None:
        callback = getattr(self, attribute, None)
        if callback is None:
            return
        try:
            callback(*args)
        except (RuntimeError, ReferenceError) as exc:
            # A deleted Qt signal source must be disconnected, not propagated out
            # through PortAudio's CFFI callback.
            message = str(exc).lower()
            if "deleted" in message or "signal source" in message or "wrapped c/c++" in message:
                with self._lock:
                    if getattr(self, attribute, None) is callback:
                        setattr(self, attribute, None)
                return
            self._stream_error = str(exc)[:500]
        except Exception as exc:
            # Never allow user/UI callbacks to unwind into PortAudio.
            self._stream_error = str(exc)[:500]

    def _invoke_callback_async(self, attribute: str, thread_name: str) -> None:
        callback = getattr(self, attribute, None)
        if callback is None:
            return
        threading.Thread(
            target=lambda: self._invoke_callback(attribute),
            daemon=True,
            name=thread_name,
        ).start()

    @classmethod
    def _candidate_sample_rates(cls, device: int | None) -> list[int]:
        candidates = [cls.SAMPLE_RATE]
        if sd is not None:
            try:
                info = sd.query_devices(device, "input") if device is not None else sd.query_devices(kind="input")
                default_rate = int(round(float(info.get("default_samplerate", cls.SAMPLE_RATE))))
                candidates.insert(0, default_rate)
            except Exception:
                pass
        candidates.extend([48_000, 44_100, 32_000, 22_050])
        result: list[int] = []
        for rate in candidates:
            if 8_000 <= int(rate) <= 192_000 and int(rate) not in result:
                result.append(int(rate))
        return result

    @classmethod
    def choose_input_sample_rate(cls, device: int | None) -> int:
        """Return a sample rate supported by the selected device.

        Many USB microphones reject 16 kHz even though Whisper accepts recordings
        at their native 44.1/48 kHz rate. Recording natively avoids false
        microphone failures; faster-whisper performs the final resampling.
        """
        if sd is None:
            return cls.SAMPLE_RATE
        last_error: Exception | None = None
        for rate in cls._candidate_sample_rates(device):
            try:
                checker = getattr(sd, "check_input_settings", None)
                if checker is not None:
                    checker(device=device, channels=cls.CHANNELS, dtype="float32", samplerate=rate)
                return rate
            except Exception as exc:
                last_error = exc
        if last_error is not None:
            raise RuntimeError(f"No supported mono input format was found: {last_error}") from last_error
        return cls.SAMPLE_RATE

    def start(self, device: int | None = None) -> None:
        if sd is None:
            raise RuntimeError("The sounddevice/PortAudio component is not installed.")
        with self._lock:
            if self._stream is not None:
                return
            if device is not None:
                available = {int(item["index"]) for item in self.input_devices()}
                if device not in available:
                    raise RuntimeError("The selected microphone is no longer available.")
            ensure_directories()
            self._recording_sample_rate = self.choose_input_sample_rate(device)
            path = TEMP_DIR / f"recording-{uuid.uuid4().hex}.wav"
            self._recording_path = path
            self._writer_queue = queue.Queue(maxsize=self.MAX_QUEUED_BLOCKS)
            self._live_queue = queue.Queue(maxsize=self.MAX_QUEUED_BLOCKS * 2)
            self._live_audio_dropped = False
            self._writer_error = ""
            self._frames_written = 0
            self._cancelled = False
            self._silence_fired = False
            self._max_fired = False
            self._stream_error = ""
            self._storage_stop_requested = False
            self._latest_level = 0.0
            self._started_at = time.monotonic()
            self._last_voice_at = self._started_at
            self._writer_thread = threading.Thread(
                target=self._writer_loop,
                args=(path, self._writer_queue, self._recording_sample_rate),
                daemon=True,
                name="LocalVoiceAudioWriter",
            )
            self._writer_thread.start()
            stream = sd.InputStream(
                samplerate=self._recording_sample_rate,
                channels=self.CHANNELS,
                dtype="float32",
                device=device,
                blocksize=self.BLOCK_SIZE,
                callback=self._callback,
            )
            try:
                stream.start()
            except Exception:
                try:
                    stream.close()
                finally:
                    self._signal_writer_stop()
                    self._join_writer()
                    self._delete_recording_path()
                    self._started_at = 0.0
                raise
            self._stream = stream

    def _writer_loop(self, path: Path, blocks: queue.Queue[bytes | None], sample_rate: int | None = None) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            blocks_since_disk_check = 0
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(self.CHANNELS)
                wav.setsampwidth(2)
                wav.setframerate(int(sample_rate or self._recording_sample_rate or self.SAMPLE_RATE))
                while True:
                    block = blocks.get()
                    try:
                        if block is None:
                            break
                        wav.writeframesraw(block)
                        self._frames_written += len(block) // 2
                        blocks_since_disk_check += 1
                        if blocks_since_disk_check >= self.DISK_CHECK_BLOCKS:
                            blocks_since_disk_check = 0
                            try:
                                free_bytes = shutil.disk_usage(path.parent).free
                            except OSError:
                                free_bytes = self.MIN_FREE_DISK_BYTES
                            if free_bytes < self.MIN_FREE_DISK_BYTES and not self._storage_stop_requested:
                                self._storage_stop_requested = True
                                self._stream_error = "Recording stopped before the disk became full."
                                if not self._max_fired:
                                    self._max_fired = True
                                    self._invoke_callback_async("on_max_duration", "LocalVoiceLowDiskStop")
                    finally:
                        blocks.task_done()
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        except Exception as exc:
            self._writer_error = str(exc)[:500]

    def _callback(self, indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        del frames, time_info
        if self._cancelled or self._storage_stop_requested:
            return
        if status:
            self._stream_error = str(status)[:500]
        block = np.asarray(indata[:, 0], dtype=np.float32)
        if not np.all(np.isfinite(block)):
            block = np.nan_to_num(block, nan=0.0, posinf=1.0, neginf=-1.0)
        clipped = np.clip(block, -1.0, 1.0)
        pcm = (clipped * 32767.0).astype("<i2", copy=False).tobytes()
        blocks = self._writer_queue
        if blocks is not None:
            try:
                blocks.put_nowait(pcm)
            except queue.Full:
                self._writer_error = "Audio storage could not keep up with the microphone stream."
                if not self._max_fired:
                    self._max_fired = True
                    self._invoke_callback_async("on_max_duration", "LocalVoiceStorageStop")
        live_blocks = self._live_queue
        if live_blocks is not None:
            try:
                live_blocks.put_nowait(pcm)
            except queue.Full:
                # Live preview may fall behind on slower CPUs. Never block the
                # PortAudio callback and never compromise the full recording.
                self._live_audio_dropped = True
        rms = float(np.sqrt(np.mean(np.square(block, dtype=np.float64)))) if block.size else 0.0
        level = min(1.0, max(0.0, math.sqrt(max(rms, 0.0)) * 3.5))
        with self._lock:
            self._latest_level = level
        self._invoke_callback("on_level", level)
        now = time.monotonic()
        if rms >= self.silence_threshold:
            self._last_voice_at = now
        elif (
            self.silence_stop_enabled
            and not self._silence_fired
            and now - self._started_at > 1.0
            and now - self._last_voice_at >= self.silence_seconds
        ):
            self._silence_fired = True
            self._invoke_callback_async("on_silence", "LocalVoiceSilenceStop")
        if (
            self.max_duration_seconds > 0
            and not self._max_fired
            and now - self._started_at >= self.max_duration_seconds
        ):
            self._max_fired = True
            self._invoke_callback_async("on_max_duration", "LocalVoiceMaxStop")

    def _signal_writer_stop(self) -> None:
        blocks = self._writer_queue
        if blocks is None:
            return
        try:
            blocks.put(None, timeout=2)
        except queue.Full:
            # Drop the oldest queued block only during shutdown so the writer can
            # terminate deterministically. The error is surfaced to the caller.
            self._writer_error = self._writer_error or "Audio writer queue did not drain cleanly."
            try:
                blocks.get_nowait()
                blocks.task_done()
            except queue.Empty:
                pass
            try:
                blocks.put_nowait(None)
            except queue.Full:
                pass

    def _join_writer(self) -> None:
        writer = self._writer_thread
        if writer is not None:
            writer.join(timeout=10)
            if writer.is_alive():
                self._writer_error = self._writer_error or "Audio writer did not stop in time."
        self._writer_thread = None
        self._writer_queue = None

    def _delete_recording_path(self) -> None:
        path = self._recording_path
        self._recording_path = None
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def _signal_live_stop(self) -> None:
        blocks = self._live_queue
        if blocks is None:
            return
        try:
            blocks.put(None, timeout=2)
        except queue.Full:
            self._live_audio_dropped = True
            try:
                blocks.get_nowait()
            except queue.Empty:
                pass
            try:
                blocks.put_nowait(None)
            except queue.Full:
                pass

    def stop(self) -> tuple[Path | None, float]:
        with self._lock:
            stream = self._stream
            self._stream = None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
        duration = self.elapsed
        self._started_at = 0.0
        self._signal_writer_stop()
        self._signal_live_stop()
        self._join_writer()
        path = self._recording_path
        self._recording_path = None
        if self._cancelled or path is None:
            if path:
                path.unlink(missing_ok=True)
            return None, duration
        if self._writer_error:
            path.unlink(missing_ok=True)
            raise RuntimeError(self._writer_error)
        if not path.is_file() or self._frames_written < int(self._recording_sample_rate * 0.15):
            path.unlink(missing_ok=True)
            return None, duration
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return path, duration

    def cancel(self) -> None:
        self._cancelled = True
        path, _ = self.stop()
        if path:
            path.unlink(missing_ok=True)

    @classmethod
    def _write_wav(cls, path: Path, audio: np.ndarray) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        audio = np.asarray(audio, dtype=np.float32)
        audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767.0).astype("<i2")
        temporary = path.with_suffix(path.suffix + ".tmp")
        with wave.open(str(temporary), "wb") as wav:
            wav.setnchannels(cls.CHANNELS)
            wav.setsampwidth(2)
            wav.setframerate(cls.SAMPLE_RATE)
            wav.writeframes(pcm.tobytes())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        temporary.replace(path)


class AudioProcessor:
    CHUNK_FRAMES = 65_536
    MAX_CHANNELS = 16
    MAX_SAMPLE_RATE = 384_000

    @staticmethod
    def _mono_float(raw: bytes, channels: int) -> np.ndarray:
        audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        if channels > 1:
            usable = audio.size - (audio.size % channels)
            audio = audio[:usable].reshape(-1, channels).mean(axis=1) if usable else np.empty(0, np.float32)
        return np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)

    @classmethod
    def _inspect(cls, path: Path) -> tuple[int, int, int, float, float]:
        sampled: list[np.ndarray] = []
        total_sum = 0.0
        total_samples = 0
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frame_count = wav.getnframes()
            if sample_width != 2:
                raise RuntimeError("Unsupported recording sample width.")
            if not 1 <= channels <= cls.MAX_CHANNELS or not 1 <= sample_rate <= cls.MAX_SAMPLE_RATE:
                raise RuntimeError("Invalid recording format.")
            while True:
                raw = wav.readframes(cls.CHUNK_FRAMES)
                if not raw:
                    break
                audio = cls._mono_float(raw, channels)
                total_sum += float(np.sum(audio, dtype=np.float64))
                total_samples += int(audio.size)
                # Keep a deterministic bounded sample for noise-floor estimation.
                if audio.size:
                    stride = max(1, audio.size // 4096)
                    sampled.append(audio[::stride][:4096])
                    if sum(item.size for item in sampled) > 262_144:
                        sampled = sampled[-48:]
        if frame_count <= 0 or total_samples <= 0:
            raise RuntimeError("The recording file is empty or missing.")
        dc_mean = total_sum / total_samples
        sample = np.concatenate(sampled) if sampled else np.zeros(1, dtype=np.float32)
        centered = np.abs(sample - dc_mean)
        noise_floor = float(np.percentile(centered, 20)) if centered.size else 0.0
        threshold = max(0.003, noise_floor * 2.0)
        return channels, sample_rate, frame_count, dc_mean, threshold

    @staticmethod
    def _transform(
        audio: np.ndarray,
        *,
        dc_mean: float,
        threshold: float,
        noise_reduction: bool,
        gain: float,
        previous: float,
    ) -> tuple[np.ndarray, float]:
        """Apply only conservative speech-safe conditioning.

        Earlier builds used a strong pre-emphasis filter and an aggressive gate.
        That could remove low-energy consonants and word beginnings, which is
        especially harmful for longer German dictation. Whisper already performs
        robust acoustic normalization, so LocalVoice now limits itself to DC
        removal, a gentle noise-floor attenuation and bounded microphone gain.
        """
        if not audio.size:
            return audio, previous
        result = audio.astype(np.float32, copy=True)
        result -= float(dc_mean)
        if noise_reduction:
            magnitude = np.abs(result)
            low = max(0.0015, float(threshold) * 0.55)
            high = max(low + 1e-6, float(threshold) * 2.4)
            speech_weight = np.clip((magnitude - low) / (high - low), 0.0, 1.0)
            # Never erase quiet phonemes. Only attenuate likely steady noise by
            # up to 28 percent and leave clear speech untouched.
            result *= 0.72 + 0.28 * speech_weight
        if gain != 1.0:
            result = np.clip(result * gain, -1.0, 1.0)
        previous = float(result[-1])
        return result, previous

    @classmethod
    def process(
        cls,
        path: Path,
        noise_reduction: bool = True,
        normalize: bool = True,
        gain: float = 1.0,
        auto_gain: bool = True,
    ) -> Path:
        """Create a speech-safe mono WAV with bounded automatic gain.

        Distant microphones often produce perfectly usable speech at a low level.
        Peak-only normalization did not lift that speech enough, forcing users to
        move close to the microphone. The first pass now estimates RMS only from
        likely speech samples and targets a conservative speech level while a
        hard peak limiter prevents clipping. Steady room noise is never used as
        the gain reference.
        """
        path = path.expanduser().resolve()
        if not path.is_file() or path.stat().st_size <= 44:
            raise RuntimeError("The recording file is empty or missing.")
        channels, sample_rate, _frames, dc_mean, threshold = cls._inspect(path)
        microphone_gain = max(0.1, min(float(gain), 8.0))

        peak = 0.0
        speech_square_sum = 0.0
        speech_samples = 0
        previous = 0.0
        speech_gate = max(0.0025, float(threshold) * 0.90)
        with wave.open(str(path), "rb") as wav:
            while True:
                raw = wav.readframes(cls.CHUNK_FRAMES)
                if not raw:
                    break
                transformed, previous = cls._transform(
                    cls._mono_float(raw, channels),
                    dc_mean=dc_mean,
                    threshold=threshold,
                    noise_reduction=noise_reduction,
                    gain=microphone_gain,
                    previous=previous,
                )
                if not transformed.size:
                    continue
                magnitude = np.abs(transformed)
                peak = max(peak, float(np.max(magnitude)))
                speech = transformed[magnitude >= speech_gate]
                if speech.size:
                    speech_square_sum += float(np.sum(np.square(speech, dtype=np.float64)))
                    speech_samples += int(speech.size)

        scale = 1.0
        if normalize and peak > 0.0005:
            peak_limit = max(0.1, 0.92 / peak)
            if auto_gain and speech_samples >= max(160, int(sample_rate * 0.03)):
                speech_rms = math.sqrt(max(0.0, speech_square_sum / speech_samples))
                # 0.115 RMS is clearly audible to Whisper without making normal
                # speech unnaturally loud. Allow more lift for distant microphones,
                # but never exceed the clipping-safe peak limit.
                desired = 0.115 / max(speech_rms, 0.004)
                scale = min(6.0, desired, peak_limit)
                scale = max(0.55, scale)
            else:
                scale = min(5.0 if auto_gain else 3.0, peak_limit)

        processed = path.with_name(path.stem + "-processed.wav")
        temporary = processed.with_suffix(processed.suffix + ".tmp")
        previous = 0.0
        try:
            with wave.open(str(path), "rb") as source, wave.open(str(temporary), "wb") as target:
                target.setnchannels(1)
                target.setsampwidth(2)
                target.setframerate(sample_rate)
                while True:
                    raw = source.readframes(cls.CHUNK_FRAMES)
                    if not raw:
                        break
                    transformed, previous = cls._transform(
                        cls._mono_float(raw, channels),
                        dc_mean=dc_mean,
                        threshold=threshold,
                        noise_reduction=noise_reduction,
                        gain=microphone_gain,
                        previous=previous,
                    )
                    pcm = (np.clip(transformed * scale, -1.0, 1.0) * 32767.0).astype("<i2")
                    target.writeframesraw(pcm.tobytes())
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            temporary.replace(processed)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return processed



def cleanup_stale_recordings(max_age_hours: int = 24) -> int:
    """Delete abandoned temporary audio files from interrupted prior sessions."""
    ensure_directories()
    cutoff = time.time() - max(1, max_age_hours) * 3600
    removed = 0
    for pattern in ("recording-*.wav", "recording-*.wav.tmp", "recording-*-processed.wav"):
        for path in TEMP_DIR.glob(pattern):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
    return removed
