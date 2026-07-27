from __future__ import annotations

import copy
import os
import re
import time
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .audio import AudioProcessor, AudioRecorder
from .database import LocalDatabase
from .i18n import tr
from .models import AppSettings, Profile, TranscriptionResult
from .paths import DATA_DIR
from .postprocess import TextPostProcessor, count_words
from .settings import SettingsStore
from .streaming import LiveTranscriptionSession, StreamingTranscript
from .system import ActiveWindowContext, TextInjector, active_window_context, application_matches
from .transcription import ModelMissingError, WhisperEngine
from .translation import LocalTranslator, TranslationMissingError


class JobSignals(QObject):
    state = Signal(str)
    result = Signal(object)
    error = Signal(str)
    finished = Signal(object)


class ProcessingJob(QRunnable):
    def __init__(
        self,
        audio_path: Path,
        duration: float,
        target_application: str,
        settings: AppSettings,
        database: LocalDatabase,
        whisper: WhisperEngine,
        translator: LocalTranslator,
        live_session: LiveTranscriptionSession | None = None,
    ) -> None:
        super().__init__()
        self.audio_path = audio_path
        self.duration = duration
        self.target_application = target_application
        self.settings = settings
        self.database = database
        self.whisper = whisper
        self.translator = translator
        self.live_session = live_session
        self.signals = JobSignals()

    @staticmethod
    def _protect_terms(text: str, vocabulary: list[dict[str, object]]) -> tuple[str, dict[str, str]]:
        protected: dict[str, str] = {}
        result = text
        counter = 0
        for entry in vocabulary:
            if not bool(entry.get("never_translate", False)):
                continue
            written = str(entry.get("written_form", "")).strip()[:500]
            if not written:
                continue
            flags = 0 if bool(entry.get("case_sensitive", False)) else re.IGNORECASE
            pattern = re.compile(re.escape(written), flags)
            while pattern.search(result):
                token = f"⟦LV{counter:04d}⟧"
                protected[token] = written
                result = pattern.sub(lambda _m, value=token: value, result, count=1)
                counter += 1
                if counter >= 1000:
                    return result, protected
        return result, protected

    @staticmethod
    def _restore_terms(text: str, protected: dict[str, str]) -> str:
        result = text
        for token, written in protected.items():
            # Some translation tokenizers insert spaces inside brackets; accept this
            # limited variation without using a broad or unsafe regular expression.
            flexible = re.escape(token).replace(r"\⟦", r"⟦\s*").replace(r"\⟧", r"\s*⟧")
            result = re.sub(flexible, lambda _m, value=written: value, result)
        return result

    def _store_audio_if_requested(self) -> str:
        if not self.settings.save_audio or not self.settings.save_history or self.settings.private_mode:
            return ""
        audio_dir = DATA_DIR / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        destination = audio_dir / f"{self.audio_path.stem}.lva"
        self.database.secure_store.encrypt_file(self.audio_path, destination)
        self.audio_path.unlink(missing_ok=True)
        return str(destination)

    @Slot()
    def run(self) -> None:
        processed_path: Path | None = None
        audio_saved_path = ""
        total_started = time.perf_counter()
        transcription_seconds = 0.0
        phase_timings: dict[str, float] = {}
        streaming_used = False
        realtime_factor = 0.0
        try:
            self.signals.state.emit("processing")
            vocabulary = self.database.list_vocabulary()
            hotwords: list[str] = []
            for entry in vocabulary:
                for key in ("written_form", "spoken_form"):
                    value = str(entry.get(key, "")).strip()
                    if value and value not in hotwords:
                        hotwords.append(value)
                if len(hotwords) >= 60:
                    break

            stream_result: StreamingTranscript | None = None
            if self.live_session is not None:
                stream_wait_started = time.perf_counter()
                stream_result = self.live_session.finish()
                phase_timings["stream_wait"] = time.perf_counter() - stream_wait_started
            if (
                stream_result is not None
                and stream_result.complete
                and stream_result.text.strip()
                and not stream_result.dropped_audio
            ):
                text = stream_result.text.strip()
                detected = stream_result.detected_language
                probability = stream_result.language_probability
                transcription_seconds = stream_result.processing_seconds
                realtime_factor = stream_result.realtime_factor
                streaming_used = True
            else:
                # Safe fallback: the complete original recording remains on disk.
                # This path is used when live preview was disabled, fell behind so
                # far that audio was dropped, or a streaming chunk failed.
                audio_started = time.perf_counter()
                processed_path = AudioProcessor.process(
                    self.audio_path,
                    noise_reduction=self.settings.noise_reduction,
                    normalize=self.settings.normalize_audio,
                    gain=self.settings.microphone_gain,
                    auto_gain=self.settings.auto_microphone_gain,
                )
                phase_timings["audio"] = time.perf_counter() - audio_started
                transcription_started = time.perf_counter()
                text, detected, probability = self.whisper.transcribe(
                    processed_path,
                    model_size=self.settings.model_size,
                    language=self.settings.input_language,
                    preferred_languages=self.settings.preferred_languages,
                    prefer_primary_language=self.settings.prefer_primary_language,
                    device=self.settings.compute_device,
                    compute_type=self.settings.compute_type,
                    recognition_mode=self.settings.recognition_mode,
                    beam_size=self.settings.beam_size,
                    language_detection_threshold=self.settings.language_detection_threshold,
                    hotwords=hotwords,
                    local_model_path=self.settings.local_model_path,
                    progress=lambda _stage: self.signals.state.emit("loading_model"),
                )
                transcription_seconds = time.perf_counter() - transcription_started
                realtime_factor = transcription_seconds / max(self.duration, 0.001)
            phase_timings["transcription"] = transcription_seconds

            if not text.strip():
                raise RuntimeError("NO_SPEECH")
            self.signals.state.emit(f"language:{detected}")

            post_started = time.perf_counter()
            processor = TextPostProcessor()
            original = processor.process(
                text,
                detected,
                vocabulary=vocabulary,
                spoken_commands=self.settings.spoken_commands,
                remove_filler_words=self.settings.remove_filler_words,
                numbers_as_digits=self.settings.numbers_as_digits,
                automatic_punctuation=self.settings.automatic_punctuation,
                writing_style=self.settings.writing_style,
            )
            phase_timings["postprocess"] = time.perf_counter() - post_started
            final = original
            translated = False
            target = self.settings.language_target_rules.get(detected, self.settings.target_language)
            if self.settings.translation_enabled and target not in {"", "same", detected}:
                translation_started = time.perf_counter()
                self.signals.state.emit("translating")
                protected_text, protected = self._protect_terms(original, vocabulary)
                translated_text = self.translator.translate(
                    protected_text,
                    detected,
                    target,
                    self.settings.translation_intermediate_language,
                )
                translated_text = self._restore_terms(translated_text, protected)
                final = processor.process(
                    translated_text,
                    target,
                    vocabulary=vocabulary,
                    spoken_commands=False,
                    remove_filler_words=False,
                    numbers_as_digits=self.settings.numbers_as_digits,
                    automatic_punctuation=self.settings.automatic_punctuation,
                    writing_style=self.settings.writing_style,
                )
                translated = True
                phase_timings["translation"] = time.perf_counter() - translation_started
                if self.settings.show_original_and_translation:
                    final = (
                        f"{tr(self.settings.ui_language, 'original')}:\n{original}\n\n"
                        f"{tr(self.settings.ui_language, 'translation')}:\n{final}"
                    )

            audio_saved_path = self._store_audio_if_requested()
            model_status = self.whisper.loaded_status()
            total_elapsed = time.perf_counter() - total_started
            phase_timings["total"] = total_elapsed
            result = TranscriptionResult(
                original_text=original,
                final_text=final,
                detected_language=detected,
                language_probability=probability,
                translated=translated,
                duration_seconds=self.duration,
                word_count=count_words(final),
                target_application=self.target_application,
                audio_path=audio_saved_path,
                processing_seconds=total_elapsed,
                streaming_used=streaming_used,
                realtime_factor=realtime_factor,
                model_device=str(model_status.get("device", "")),
                model_compute_type=str(model_status.get("compute_type", "")),
                phase_timings=phase_timings,
            )
            self.signals.result.emit((result, self.settings))
        except ModelMissingError as exc:
            self.signals.error.emit(str(exc))
        except TranslationMissingError as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:
            self.signals.error.emit(str(exc)[:2000])
        finally:
            try:
                if self.audio_path.exists() and not audio_saved_path:
                    self.audio_path.unlink()
                if processed_path and processed_path.exists():
                    processed_path.unlink()
            except OSError:
                pass
            self.signals.finished.emit(self)


class AppController(QObject):
    recording_started = Signal()
    recording_stopped = Signal()
    level_changed = Signal(float)
    state_changed = Signal(str)
    result_ready = Signal(object)
    preview_requested = Signal(object)
    error_occurred = Signal(str)
    request_start = Signal()
    request_stop = Signal()
    request_toggle = Signal()
    request_cancel = Signal()
    request_start_hotkey = Signal(str)
    request_stop_hotkey = Signal(str)
    request_toggle_hotkey = Signal(str)
    history_changed = Signal()
    partial_text_changed = Signal(str)
    model_status_changed = Signal(object)

    def __init__(
        self,
        settings_store: SettingsStore,
        database: LocalDatabase,
        injector: TextInjector,
    ) -> None:
        super().__init__()
        self.settings_store = settings_store
        self.database = database
        self.injector = injector
        self.recorder = AudioRecorder()
        self.whisper = WhisperEngine()
        self.translator = LocalTranslator()
        self.thread_pool = QThreadPool.globalInstance()
        self._active_jobs: set[ProcessingJob] = set()
        self._processing = False
        self._live_session: LiveTranscriptionSession | None = None
        self._target_application = ""
        self._target_context = ActiveWindowContext()
        self._recording_profile: Profile | None = None
        self._active_settings = copy.deepcopy(self.settings_store.current)
        self._configure_recorder(self._active_settings)
        self.request_start.connect(self.start_recording)
        self.request_stop.connect(self.stop_recording)
        self.request_toggle.connect(self.toggle_recording)
        self.request_cancel.connect(self.cancel_recording)
        self.request_start_hotkey.connect(self.start_recording_for_hotkey)
        self.request_stop_hotkey.connect(lambda _hotkey: self.stop_recording())
        self.request_toggle_hotkey.connect(self.toggle_recording_for_hotkey)

    @property
    def is_recording(self) -> bool:
        return self.recorder.is_recording

    @property
    def is_processing(self) -> bool:
        return self._processing

    @property
    def active_settings(self) -> AppSettings:
        return self._active_settings

    @property
    def active_profile(self) -> Profile | None:
        return self._recording_profile

    @property
    def target_context(self) -> ActiveWindowContext:
        return self._target_context

    def _configure_recorder(self, settings: AppSettings) -> None:
        self.recorder.silence_stop_enabled = settings.silence_stop_enabled
        self.recorder.silence_seconds = settings.silence_seconds
        self.recorder.silence_threshold = settings.silence_threshold
        self.recorder.max_duration_seconds = settings.max_recording_seconds
        self.recorder.on_level = self.level_changed.emit
        self.recorder.on_silence = self.request_stop.emit
        self.recorder.on_max_duration = self.request_stop.emit

    def refresh_settings(self) -> None:
        self._active_settings = copy.deepcopy(self.settings_store.current)
        self._configure_recorder(self._active_settings)

    def _settings_for_active_app(self, explicit_profile: Profile | None = None) -> AppSettings:
        settings = copy.deepcopy(self.settings_store.current)
        self._recording_profile = None
        profiles = [explicit_profile] if explicit_profile is not None else self.database.list_profiles()
        if explicit_profile is None and not settings.auto_profile_switching:
            return settings
        for profile in profiles:
            if profile is None or not profile.enabled:
                continue
            if profile.applications and not application_matches(self._target_application, profile.applications):
                continue
            settings.hotkey = profile.hotkey
            settings.secondary_hotkey = profile.secondary_hotkey
            settings.recording_mode = profile.recording_mode
            settings.microphone_device = profile.microphone_device
            settings.input_language = profile.input_language
            settings.preferred_languages = list(profile.preferred_languages)
            settings.prefer_primary_language = profile.prefer_primary_language
            settings.target_language = profile.target_language
            settings.language_target_rules = dict(profile.language_target_rules)
            settings.translation_enabled = profile.translation_enabled
            settings.translation_intermediate_language = profile.translation_intermediate_language
            settings.language_detection_threshold = profile.language_detection_threshold
            settings.show_original_and_translation = profile.show_original_and_translation
            settings.output_mode = profile.output_mode
            settings.auto_press_enter = profile.auto_press_enter
            settings.spoken_commands = profile.spoken_commands
            settings.remove_filler_words = profile.remove_filler_words
            settings.numbers_as_digits = profile.numbers_as_digits
            settings.automatic_punctuation = profile.automatic_punctuation
            settings.restore_clipboard_after_insert = profile.restore_clipboard_after_insert
            settings.clipboard_clear_seconds = profile.clipboard_clear_seconds
            settings.model_size = profile.model_size
            settings.local_model_path = profile.local_model_path
            settings.compute_device = profile.compute_device
            settings.compute_type = profile.compute_type
            settings.recognition_mode = profile.recognition_mode
            settings.beam_size = profile.beam_size
            settings.live_transcription_enabled = profile.live_transcription_enabled
            settings.live_preview_enabled = profile.live_preview_enabled
            settings.live_chunk_seconds = profile.live_chunk_seconds
            settings.live_overlap_seconds = profile.live_overlap_seconds
            settings.noise_reduction = profile.noise_reduction
            settings.normalize_audio = profile.normalize_audio
            settings.microphone_gain = profile.microphone_gain
            settings.auto_microphone_gain = profile.auto_microphone_gain
            settings.silence_stop_enabled = profile.silence_stop_enabled
            settings.silence_seconds = profile.silence_seconds
            settings.silence_threshold = profile.silence_threshold
            settings.max_recording_seconds = profile.max_recording_seconds
            settings.start_stop_sound = profile.start_stop_sound
            settings.save_history = profile.save_history
            settings.save_audio = profile.save_audio
            settings.private_mode = profile.private_mode
            settings.writing_style = profile.writing_style
            self._recording_profile = profile
            break
        return settings

    def _hotkey_allowed_for_app(self, settings: AppSettings) -> bool:
        if settings.hotkey_exclude_apps and application_matches(self._target_application, settings.hotkey_exclude_apps):
            return False
        if settings.hotkey_include_apps and not application_matches(self._target_application, settings.hotkey_include_apps):
            return False
        return True

    def _profile_for_hotkey(self, hotkey: str) -> Profile | None:
        normalized = hotkey.strip().lower()
        for profile in self.database.list_profiles():
            if not profile.enabled:
                continue
            if normalized in {profile.hotkey.lower(), profile.secondary_hotkey.lower()}:
                return profile
        return None

    def _vocabulary_hotwords(self) -> list[str]:
        values: list[str] = []
        try:
            vocabulary = self.database.list_vocabulary()
        except Exception:
            return values
        for entry in vocabulary:
            for key in ("written_form", "spoken_form"):
                value = str(entry.get(key, "")).strip()
                if value and value not in values:
                    values.append(value)
                if len(values) >= 60:
                    return values
        return values

    def _start_recording(self, explicit_profile: Profile | None = None) -> None:
        if self.recorder.is_recording or self._processing:
            return
        self._target_context = active_window_context()
        self._target_application = self._target_context.process_name
        base_settings = self.settings_store.current
        if not self._hotkey_allowed_for_app(base_settings):
            return
        if explicit_profile is not None and explicit_profile.applications and not application_matches(
            self._target_application, explicit_profile.applications
        ):
            return
        self._active_settings = self._settings_for_active_app(explicit_profile)
        self._configure_recorder(self._active_settings)
        # Dictation is intentionally offline. Make a missing model visible before
        # opening the microphone instead of recording and failing only afterwards.
        if not self.whisper.is_model_available(
            self._active_settings.model_size,
            self._active_settings.local_model_path,
        ):
            self.state_changed.emit("model_missing")
            self.error_occurred.emit(f"MODEL_MISSING:{self._active_settings.model_size}")
            return
        try:
            self.recorder.start(self._active_settings.microphone_device)
            self._live_session = None
            if self._active_settings.live_transcription_enabled:
                self._live_session = LiveTranscriptionSession(
                    self.recorder,
                    self.whisper,
                    copy.deepcopy(self._active_settings),
                    hotwords=self._vocabulary_hotwords(),
                    on_partial=(
                        self.partial_text_changed.emit
                        if self._active_settings.live_preview_enabled
                        else None
                    ),
                    on_state=self.state_changed.emit,
                )
                self._live_session.start()
            self.state_changed.emit("recording")
            self.recording_started.emit()
        except Exception as exc:
            # If starting the live worker fails after PortAudio has already
            # opened, close both paths immediately. Otherwise the microphone
            # could remain active although the UI reports an error.
            live_session = self._live_session
            self._live_session = None
            if live_session is not None:
                live_session.cancel()
            if self.recorder.is_recording:
                try:
                    self.recorder.cancel()
                except Exception:
                    pass
            self.state_changed.emit("error")
            self.error_occurred.emit(f"MICROPHONE:{str(exc)[:1000]}")

    @Slot()
    def start_recording(self) -> None:
        self._start_recording()

    @Slot(str)
    def start_recording_for_hotkey(self, hotkey: str) -> None:
        global_hotkeys = {
            self.settings_store.current.hotkey.lower(),
            self.settings_store.current.secondary_hotkey.lower(),
        }
        profile = None if hotkey.lower() in global_hotkeys else self._profile_for_hotkey(hotkey)
        self._start_recording(profile)

    @Slot()
    def stop_recording(self) -> None:
        if not self.recorder.is_recording:
            return
        try:
            path, duration = self.recorder.stop()
        except Exception as exc:
            live_session = self._live_session
            self._live_session = None
            if live_session is not None:
                live_session.cancel()
            self.recording_stopped.emit()
            self.state_changed.emit("error")
            self.error_occurred.emit(f"AUDIO_WRITE:{str(exc)[:1000]}")
            return
        self.recording_stopped.emit()
        live_session = self._live_session
        self._live_session = None
        if path is None:
            if live_session is not None:
                live_session.cancel()
            self.state_changed.emit("ready")
            self.error_occurred.emit("TOO_SHORT")
            return
        self._processing = True
        settings = copy.deepcopy(self._active_settings)
        job = ProcessingJob(
            path,
            duration,
            self._target_application,
            settings,
            self.database,
            self.whisper,
            self.translator,
            live_session,
        )
        job.signals.state.connect(self.state_changed.emit)
        job.signals.result.connect(self._processing_complete_payload)
        job.signals.error.connect(self._processing_error)
        job.signals.finished.connect(self._processing_job_finished)
        self._active_jobs.add(job)
        self.thread_pool.start(job)

    @Slot()
    def toggle_recording(self) -> None:
        if self.recorder.is_recording:
            self.stop_recording()
        elif not self._processing:
            self.start_recording()

    @Slot(str)
    def toggle_recording_for_hotkey(self, hotkey: str) -> None:
        if self.recorder.is_recording:
            self.stop_recording()
            return
        if self._processing:
            return
        global_hotkeys = {
            self.settings_store.current.hotkey.lower(),
            self.settings_store.current.secondary_hotkey.lower(),
        }
        profile = None if hotkey.lower() in global_hotkeys else self._profile_for_hotkey(hotkey)
        self._start_recording(profile)

    @Slot()
    def cancel_recording(self) -> None:
        if self.recorder.is_recording:
            if self._live_session is not None:
                self._live_session.cancel()
                self._live_session = None
            self.recorder.cancel()
            self.recording_stopped.emit()
            self.state_changed.emit("cancelled")

    @Slot(object)
    def _processing_complete_payload(self, payload: object) -> None:
        try:
            result, settings = payload  # type: ignore[misc]
        except (TypeError, ValueError):
            self._processing_error("Invalid processing result.")
            return
        if not isinstance(result, TranscriptionResult) or not isinstance(settings, AppSettings):
            self._processing_error("Invalid processing result.")
            return
        self._processing_complete(result, settings)

    @Slot(object)
    def _processing_job_finished(self, job: object) -> None:
        self._active_jobs.discard(job)  # type: ignore[arg-type]

    def _processing_complete(self, result: TranscriptionResult, settings: AppSettings) -> None:
        self._processing = False
        low_confidence = settings.input_language == "auto" and result.language_probability < settings.language_detection_threshold
        if settings.output_mode == "preview" or low_confidence:
            self.preview_requested.emit(result)
            return
        self.commit_result(result, settings)

    def discard_result(self, result: TranscriptionResult) -> None:
        """Discard result-owned audio when a preview is cancelled or output fails."""
        if result.audio_path:
            self.database.discard_saved_audio(result.audio_path)
            result.audio_path = ""

    @Slot(object)
    def commit_result(self, result: TranscriptionResult, settings: AppSettings | None = None) -> None:
        settings = settings or self._active_settings
        history_persisted = False
        try:
            if settings.output_mode not in {"app", "preview"}:
                outcome = self.injector.output(
                    result.final_text,
                    "insert" if settings.output_mode == "insert" else "clipboard",
                    auto_enter=settings.auto_press_enter,
                    clear_after=settings.clipboard_clear_seconds,
                    context=self._target_context,
                    restore_clipboard=settings.restore_clipboard_after_insert,
                )
                self.state_changed.emit(outcome)
            else:
                self.state_changed.emit("ready")
            if settings.save_history and not settings.private_mode:
                self.database.add_history(result)
                history_persisted = True
                if settings.history_retention_days > 0:
                    self.database.purge_history(settings.history_retention_days)
                self.database.prune_history(settings.max_history_items)
                self.database.purge_saved_audio(settings.audio_retention_days)
                self.history_changed.emit()
            self.result_ready.emit(result)
        except Exception as exc:
            if result.audio_path and not history_persisted:
                self.discard_result(result)
            self._processing_error(str(exc))

    def _processing_error(self, message: str) -> None:
        self._processing = False
        self.state_changed.emit("error")
        self.error_occurred.emit(message)

    @Slot()
    def preload_current_model(self) -> None:
        """Warm the installed local model in a background thread.

        This removes the model-loading delay from the first dictation while
        preserving the offline guarantee. Missing models are ignored here and
        remain visible through the normal model-manager status.
        """
        settings = copy.deepcopy(self.settings_store.current)
        if not settings.preload_model or not self.whisper.is_model_available(
            settings.model_size, settings.local_model_path
        ):
            return

        def worker() -> None:
            try:
                self.whisper.preload(
                    settings.model_size,
                    settings.compute_device,
                    settings.compute_type,
                    settings.local_model_path,
                )
                self.model_status_changed.emit(self.whisper.loaded_status())
            except Exception:
                # Preloading is only a latency optimization. Dictation still
                # reports the real error through its normal processing path.
                return

        import threading
        threading.Thread(target=worker, daemon=True, name="LocalVoiceModelPreload").start()

    def shutdown(self, timeout_ms: int = 10_000) -> None:
        """Stop capture and let active local jobs finish before process exit."""
        if self.recorder.is_recording:
            if self._live_session is not None:
                self._live_session.cancel()
                self._live_session = None
            self.recorder.cancel()
            self.recording_stopped.emit()
        self.recorder.detach_callbacks()
        try:
            self.thread_pool.waitForDone(max(0, min(int(timeout_ms), 30_000)))
        except (RuntimeError, TypeError, ValueError):
            pass
