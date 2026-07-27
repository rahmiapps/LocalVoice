import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from localvoice.core.audio import AudioProcessor, AudioRecorder


class AudioTests(unittest.TestCase):
    def test_noise_reduction_and_gain_do_not_shadow_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.wav"
            t = np.arange(AudioRecorder.SAMPLE_RATE, dtype=np.float32) / AudioRecorder.SAMPLE_RATE
            signal = 0.15 * np.sin(2 * np.pi * 440 * t)
            AudioRecorder._write_wav(path, signal)
            processed = AudioProcessor.process(path, noise_reduction=True, normalize=True, gain=1.75)
            self.assertTrue(processed.is_file())
            with wave.open(str(processed), "rb") as wav:
                self.assertEqual(wav.getframerate(), AudioRecorder.SAMPLE_RATE)
                self.assertGreater(wav.getnframes(), 0)


if __name__ == "__main__":
    unittest.main()


def test_audio_recorder_reserves_disk_space_for_unlimited_recording(monkeypatch, tmp_path) -> None:
    import queue
    import threading
    from types import SimpleNamespace

    recorder = AudioRecorder()
    recorder.DISK_CHECK_BLOCKS = 1
    recorder._recording_path = tmp_path / "recording-low-disk.wav"
    recorder._writer_queue = queue.Queue(maxsize=8)
    stop_requested = threading.Event()
    recorder.on_max_duration = stop_requested.set
    monkeypatch.setattr("localvoice.core.audio.shutil.disk_usage", lambda _path: SimpleNamespace(free=1))

    writer = threading.Thread(
        target=recorder._writer_loop,
        args=(recorder._recording_path, recorder._writer_queue),
        daemon=True,
    )
    recorder._writer_thread = writer
    writer.start()
    recorder._writer_queue.put(b"\x00\x00" * recorder.BLOCK_SIZE)
    recorder._writer_queue.put(None)
    writer.join(timeout=2)

    assert recorder._storage_stop_requested
    assert stop_requested.wait(1)
    assert "disk became full" in recorder.stream_error


def test_deleted_qt_callback_is_detached_and_never_escapes_portaudio() -> None:
    recorder = AudioRecorder()

    def deleted_signal(_value: float) -> None:
        raise RuntimeError("Signal source has been deleted")

    recorder.on_level = deleted_signal
    recorder._writer_queue = __import__("queue").Queue(maxsize=4)
    recorder._started_at = __import__("time").monotonic()
    block = np.zeros((recorder.BLOCK_SIZE, 1), dtype=np.float32)
    recorder._callback(block, recorder.BLOCK_SIZE, object(), None)
    assert recorder.on_level is None
    assert recorder.latest_level == 0.0


def test_recorder_tracks_latest_level_without_a_gui_callback() -> None:
    recorder = AudioRecorder()
    recorder._writer_queue = __import__("queue").Queue(maxsize=4)
    recorder._started_at = __import__("time").monotonic()
    block = np.full((recorder.BLOCK_SIZE, 1), 0.20, dtype=np.float32)
    recorder._callback(block, recorder.BLOCK_SIZE, object(), None)
    assert recorder.latest_level > 0.0


def test_microphone_test_polls_plain_level_instead_of_storing_qt_signal() -> None:
    source = Path("localvoice/ui/dialogs.py").read_text(encoding="utf-8")
    section = source[source.index("class MicrophoneTestDialog"):source.index("class OnboardingDialog")]
    assert "self.recorder.latest_level" in section
    assert "self.recorder.on_level = self.level_signal.emit" not in section


def test_microphone_sample_rate_uses_supported_device_format(monkeypatch) -> None:
    class FakeSoundDevice:
        @staticmethod
        def query_devices(device=None, kind=None):
            return {"default_samplerate": 48_000.0}

        @staticmethod
        def check_input_settings(*, device, channels, dtype, samplerate):
            assert channels == 1
            assert dtype == "float32"
            if samplerate != 48_000:
                raise ValueError("unsupported")

    monkeypatch.setattr("localvoice.core.audio.sd", FakeSoundDevice())
    assert AudioRecorder.choose_input_sample_rate(None) == 48_000


def test_automatic_gain_lifts_quiet_speech_without_clipping(tmp_path: Path) -> None:
    path = tmp_path / "quiet.wav"
    rate = AudioRecorder.SAMPLE_RATE
    t = np.arange(rate * 2, dtype=np.float32) / rate
    signal = 0.012 * np.sin(2 * np.pi * 210 * t)
    AudioRecorder._write_wav(path, signal)
    processed = AudioProcessor.process(
        path, noise_reduction=False, normalize=True, gain=1.0, auto_gain=True
    )
    with wave.open(str(processed), "rb") as wav:
        output = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    assert float(np.sqrt(np.mean(output ** 2))) > float(np.sqrt(np.mean(signal ** 2))) * 2.0
    assert float(np.max(np.abs(output))) <= 0.93


def test_recorder_copies_blocks_to_bounded_live_queue_and_signals_stop() -> None:
    import queue
    import time

    recorder = AudioRecorder()
    recorder._writer_queue = queue.Queue(maxsize=4)
    recorder._live_queue = queue.Queue(maxsize=4)
    recorder._started_at = time.monotonic()
    block = np.full((recorder.BLOCK_SIZE, 1), 0.05, dtype=np.float32)
    recorder._callback(block, recorder.BLOCK_SIZE, object(), None)
    live = recorder.take_live_block(0.1)
    assert isinstance(live, bytes) and len(live) == recorder.BLOCK_SIZE * 2
    recorder._signal_live_stop()
    assert recorder.take_live_block(0.1) is None
