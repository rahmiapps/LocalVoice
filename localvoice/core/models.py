from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .validation import (
    COMPUTE_DEVICES,
    COMPUTE_TYPES,
    RECOGNITION_MODES,
    MODEL_SIZES,
    OUTPUT_MODES,
    OVERLAY_POSITIONS,
    RECORDING_MODES,
    SUPPORTED_UI_LANGUAGES,
    THEMES,
    WRITING_STYLES,
    clamp_int,
    clamp_number,
    normalize_app_list,
    normalize_hotkey,
    normalize_language,
    normalize_language_list,
    normalize_language_target_rules,
    normalize_max_recording_seconds,
    normalize_optional_hotkey,
    safe_choice,
    safe_existing_directory,
    safe_text,
)


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


@dataclass(slots=True)
class AppSettings:
    settings_schema_version: int = 8
    ui_language: str = "de"
    ui_language_confirmed: bool = False
    theme: str = "dark"
    ui_size: str = "medium"  # small | medium | large
    first_run_complete: bool = False
    microphone_device: int | None = None
    recording_mode: str = "hold"  # hold | toggle
    hotkey: str = "f8"
    secondary_hotkey: str = ""
    hotkey_enabled: bool = True
    suppress_hotkey_keystroke: bool = True
    hotkey_include_apps: list[str] = field(default_factory=list)
    hotkey_exclude_apps: list[str] = field(default_factory=list)
    input_language: str = "auto"
    preferred_languages: list[str] = field(default_factory=lambda: ["de", "en", "fr"])
    prefer_primary_language: bool = True
    target_language: str = "same"
    show_original_and_translation: bool = False
    output_mode: str = "insert"  # insert | clipboard | preview | app
    auto_press_enter: bool = False
    restore_clipboard_after_insert: bool = True
    model_size: str = "small"
    compute_device: str = "auto"
    compute_type: str = "auto"
    recognition_mode: str = "balanced"
    beam_size: int = 2
    preload_model: bool = True
    live_transcription_enabled: bool = True
    live_preview_enabled: bool = True
    live_chunk_seconds: float = 3.0
    live_overlap_seconds: float = 0.8
    noise_reduction: bool = False
    normalize_audio: bool = True
    microphone_gain: float = 1.0
    auto_microphone_gain: bool = True
    silence_stop_enabled: bool = False
    silence_seconds: float = 4.0
    silence_threshold: float = 0.018
    max_recording_seconds: int = 1800  # 0 = unlimited
    remove_filler_words: bool = False
    spoken_commands: bool = True
    numbers_as_digits: bool = False
    automatic_punctuation: bool = True
    save_history: bool = True
    save_audio: bool = False
    private_mode: bool = False
    history_retention_days: int = 0
    audio_retention_days: int = 0
    max_history_items: int = 10_000
    clipboard_clear_seconds: int = 0
    overlay_screen: str = "active"  # active | primary | index:0
    overlay_position: str = "bottom_right"
    overlay_opacity: float = 0.96
    overlay_scale: float = 1.0
    overlay_custom_x: int = 20
    overlay_custom_y: int = 20
    overlay_show_processing: bool = True
    start_stop_sound: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    autostart: bool = False
    close_to_tray: bool = True
    auto_profile_switching: bool = True
    writing_style: str = "neutral"
    language_detection_threshold: float = 0.35
    local_model_path: str = ""
    translation_enabled: bool = True
    translation_intermediate_language: str = "en"
    language_target_rules: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        defaults = cls()
        if not isinstance(data, dict):
            return defaults
        microphone: int | None
        try:
            microphone = int(data.get("microphone_device")) if data.get("microphone_device") is not None else None
        except (TypeError, ValueError):
            microphone = None
        overlay_screen = safe_text(data.get("overlay_screen", defaults.overlay_screen), maximum=32)
        if overlay_screen not in {"active", "primary"} and not overlay_screen.startswith("index:"):
            overlay_screen = defaults.overlay_screen
        private_mode = _as_bool(data.get("private_mode"), defaults.private_mode)
        save_history = _as_bool(data.get("save_history"), defaults.save_history) and not private_mode
        save_audio = _as_bool(data.get("save_audio"), defaults.save_audio) and save_history
        return cls(
            settings_schema_version=clamp_int(data.get("settings_schema_version"), 1, 10_000, defaults.settings_schema_version),
            ui_language=safe_choice(data.get("ui_language"), SUPPORTED_UI_LANGUAGES, defaults.ui_language),
            ui_language_confirmed=_as_bool(data.get("ui_language_confirmed"), defaults.ui_language_confirmed),
            theme=safe_choice(data.get("theme"), THEMES, defaults.theme),
            ui_size=safe_choice(data.get("ui_size"), {"small", "medium", "large"}, defaults.ui_size),
            first_run_complete=_as_bool(data.get("first_run_complete"), defaults.first_run_complete),
            microphone_device=microphone,
            recording_mode=safe_choice(data.get("recording_mode"), RECORDING_MODES, defaults.recording_mode),
            hotkey=normalize_hotkey(data.get("hotkey"), defaults.hotkey),
            secondary_hotkey=normalize_optional_hotkey(data.get("secondary_hotkey")),
            hotkey_enabled=_as_bool(data.get("hotkey_enabled"), defaults.hotkey_enabled),
            suppress_hotkey_keystroke=_as_bool(data.get("suppress_hotkey_keystroke"), defaults.suppress_hotkey_keystroke),
            hotkey_include_apps=normalize_app_list(data.get("hotkey_include_apps", [])),
            hotkey_exclude_apps=normalize_app_list(data.get("hotkey_exclude_apps", [])),
            input_language=normalize_language(data.get("input_language"), default=defaults.input_language),
            preferred_languages=normalize_language_list(data.get("preferred_languages", defaults.preferred_languages)) or defaults.preferred_languages,
            prefer_primary_language=_as_bool(data.get("prefer_primary_language"), defaults.prefer_primary_language),
            target_language=normalize_language(data.get("target_language"), allow_auto=False, allow_same=True, default=defaults.target_language),
            show_original_and_translation=_as_bool(data.get("show_original_and_translation"), defaults.show_original_and_translation),
            output_mode=safe_choice(data.get("output_mode"), OUTPUT_MODES, defaults.output_mode),
            auto_press_enter=_as_bool(data.get("auto_press_enter"), defaults.auto_press_enter),
            restore_clipboard_after_insert=_as_bool(data.get("restore_clipboard_after_insert"), defaults.restore_clipboard_after_insert),
            model_size=safe_choice(data.get("model_size"), MODEL_SIZES, defaults.model_size),
            compute_device=safe_choice(data.get("compute_device"), COMPUTE_DEVICES, defaults.compute_device),
            compute_type=safe_choice(data.get("compute_type"), COMPUTE_TYPES, defaults.compute_type),
            recognition_mode=safe_choice(data.get("recognition_mode"), RECOGNITION_MODES, defaults.recognition_mode),
            beam_size=clamp_int(data.get("beam_size"), 1, 10, defaults.beam_size),
            preload_model=_as_bool(data.get("preload_model"), defaults.preload_model),
            live_transcription_enabled=_as_bool(data.get("live_transcription_enabled"), defaults.live_transcription_enabled),
            live_preview_enabled=_as_bool(data.get("live_preview_enabled"), defaults.live_preview_enabled),
            live_chunk_seconds=clamp_number(data.get("live_chunk_seconds"), 3.0, 12.0, defaults.live_chunk_seconds),
            live_overlap_seconds=clamp_number(data.get("live_overlap_seconds"), 0.35, 2.5, defaults.live_overlap_seconds),
            noise_reduction=_as_bool(data.get("noise_reduction"), defaults.noise_reduction),
            normalize_audio=_as_bool(data.get("normalize_audio"), defaults.normalize_audio),
            microphone_gain=clamp_number(data.get("microphone_gain"), 0.25, 8.0, defaults.microphone_gain),
            auto_microphone_gain=_as_bool(data.get("auto_microphone_gain"), defaults.auto_microphone_gain),
            silence_stop_enabled=_as_bool(data.get("silence_stop_enabled"), defaults.silence_stop_enabled),
            silence_seconds=clamp_number(data.get("silence_seconds"), 1.0, 30.0, defaults.silence_seconds),
            silence_threshold=clamp_number(data.get("silence_threshold"), 0.001, 0.25, defaults.silence_threshold),
            max_recording_seconds=normalize_max_recording_seconds(data.get("max_recording_seconds"), defaults.max_recording_seconds),
            remove_filler_words=_as_bool(data.get("remove_filler_words"), defaults.remove_filler_words),
            spoken_commands=_as_bool(data.get("spoken_commands"), defaults.spoken_commands),
            numbers_as_digits=_as_bool(data.get("numbers_as_digits"), defaults.numbers_as_digits),
            automatic_punctuation=_as_bool(data.get("automatic_punctuation"), defaults.automatic_punctuation),
            save_history=save_history,
            save_audio=save_audio,
            private_mode=private_mode,
            history_retention_days=clamp_int(data.get("history_retention_days"), 0, 3650, defaults.history_retention_days),
            audio_retention_days=clamp_int(data.get("audio_retention_days"), 0, 3650, defaults.audio_retention_days),
            max_history_items=clamp_int(data.get("max_history_items"), 100, 1_000_000, defaults.max_history_items),
            clipboard_clear_seconds=clamp_int(data.get("clipboard_clear_seconds"), 0, 3600, defaults.clipboard_clear_seconds),
            overlay_screen=overlay_screen,
            overlay_position=safe_choice(data.get("overlay_position"), OVERLAY_POSITIONS, defaults.overlay_position),
            overlay_opacity=clamp_number(data.get("overlay_opacity"), 0.35, 1.0, defaults.overlay_opacity),
            overlay_scale=clamp_number(data.get("overlay_scale"), 0.7, 1.6, defaults.overlay_scale),
            overlay_custom_x=clamp_int(data.get("overlay_custom_x"), 0, 20_000, defaults.overlay_custom_x),
            overlay_custom_y=clamp_int(data.get("overlay_custom_y"), 0, 20_000, defaults.overlay_custom_y),
            overlay_show_processing=_as_bool(data.get("overlay_show_processing"), defaults.overlay_show_processing),
            start_stop_sound=_as_bool(data.get("start_stop_sound"), defaults.start_stop_sound),
            start_minimized=_as_bool(data.get("start_minimized"), defaults.start_minimized),
            minimize_to_tray=_as_bool(data.get("minimize_to_tray"), defaults.minimize_to_tray),
            autostart=_as_bool(data.get("autostart"), defaults.autostart),
            close_to_tray=_as_bool(data.get("close_to_tray"), defaults.close_to_tray),
            auto_profile_switching=_as_bool(data.get("auto_profile_switching"), defaults.auto_profile_switching),
            writing_style=safe_choice(data.get("writing_style"), WRITING_STYLES, defaults.writing_style),
            language_detection_threshold=clamp_number(data.get("language_detection_threshold"), 0.0, 1.0, defaults.language_detection_threshold),
            local_model_path=safe_existing_directory(data.get("local_model_path")),
            translation_enabled=_as_bool(data.get("translation_enabled"), defaults.translation_enabled),
            translation_intermediate_language=normalize_language(data.get("translation_intermediate_language"), allow_auto=False, default=defaults.translation_intermediate_language),
            language_target_rules=normalize_language_target_rules(data.get("language_target_rules", defaults.language_target_rules)),
        )


@dataclass(slots=True)
class Profile:
    id: int | None = None
    name: str = "Default"
    applications: list[str] = field(default_factory=list)
    hotkey: str = "f8"
    secondary_hotkey: str = ""
    recording_mode: str = "hold"
    microphone_device: int | None = None
    input_language: str = "auto"
    preferred_languages: list[str] = field(default_factory=lambda: ["de", "en", "fr"])
    prefer_primary_language: bool = True
    target_language: str = "same"
    language_target_rules: dict[str, str] = field(default_factory=dict)
    translation_enabled: bool = True
    translation_intermediate_language: str = "en"
    language_detection_threshold: float = 0.35
    show_original_and_translation: bool = False
    output_mode: str = "insert"
    auto_press_enter: bool = False
    spoken_commands: bool = True
    remove_filler_words: bool = False
    numbers_as_digits: bool = False
    automatic_punctuation: bool = True
    restore_clipboard_after_insert: bool = True
    clipboard_clear_seconds: int = 0
    model_size: str = "small"
    local_model_path: str = ""
    compute_device: str = "auto"
    compute_type: str = "auto"
    recognition_mode: str = "balanced"
    beam_size: int = 2
    live_transcription_enabled: bool = True
    live_preview_enabled: bool = True
    live_chunk_seconds: float = 3.0
    live_overlap_seconds: float = 0.8
    noise_reduction: bool = False
    normalize_audio: bool = True
    microphone_gain: float = 1.0
    auto_microphone_gain: bool = True
    silence_stop_enabled: bool = False
    silence_seconds: float = 4.0
    silence_threshold: float = 0.018
    max_recording_seconds: int = 1800
    start_stop_sound: bool = True
    save_history: bool = True
    save_audio: bool = False
    private_mode: bool = False
    writing_style: str = "neutral"
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        defaults = cls()
        if not isinstance(data, dict):
            return defaults
        profile_id = data.get("id")
        try:
            profile_id = int(profile_id) if profile_id is not None else None
        except (TypeError, ValueError):
            profile_id = None
        microphone: int | None
        try:
            microphone = int(data.get("microphone_device")) if data.get("microphone_device") is not None else None
        except (TypeError, ValueError):
            microphone = None
        private_mode = _as_bool(data.get("private_mode"), defaults.private_mode)
        save_history = _as_bool(data.get("save_history"), defaults.save_history) and not private_mode
        save_audio = _as_bool(data.get("save_audio"), defaults.save_audio) and save_history
        return cls(
            id=profile_id,
            name=safe_text(data.get("name", defaults.name), maximum=120) or defaults.name,
            applications=normalize_app_list(data.get("applications", [])),
            hotkey=normalize_hotkey(data.get("hotkey"), defaults.hotkey),
            secondary_hotkey=normalize_optional_hotkey(data.get("secondary_hotkey")),
            recording_mode=safe_choice(data.get("recording_mode"), RECORDING_MODES, defaults.recording_mode),
            microphone_device=microphone,
            input_language=normalize_language(data.get("input_language"), default=defaults.input_language),
            preferred_languages=normalize_language_list(data.get("preferred_languages", defaults.preferred_languages)) or defaults.preferred_languages,
            prefer_primary_language=_as_bool(data.get("prefer_primary_language"), defaults.prefer_primary_language),
            target_language=normalize_language(data.get("target_language"), allow_auto=False, allow_same=True, default=defaults.target_language),
            language_target_rules=normalize_language_target_rules(data.get("language_target_rules", defaults.language_target_rules)),
            translation_enabled=_as_bool(data.get("translation_enabled"), defaults.translation_enabled),
            translation_intermediate_language=normalize_language(data.get("translation_intermediate_language"), allow_auto=False, default=defaults.translation_intermediate_language),
            language_detection_threshold=clamp_number(data.get("language_detection_threshold"), 0.0, 1.0, defaults.language_detection_threshold),
            show_original_and_translation=_as_bool(data.get("show_original_and_translation"), defaults.show_original_and_translation),
            output_mode=safe_choice(data.get("output_mode"), OUTPUT_MODES, defaults.output_mode),
            auto_press_enter=_as_bool(data.get("auto_press_enter"), defaults.auto_press_enter),
            spoken_commands=_as_bool(data.get("spoken_commands"), defaults.spoken_commands),
            remove_filler_words=_as_bool(data.get("remove_filler_words"), defaults.remove_filler_words),
            numbers_as_digits=_as_bool(data.get("numbers_as_digits"), defaults.numbers_as_digits),
            automatic_punctuation=_as_bool(data.get("automatic_punctuation"), defaults.automatic_punctuation),
            restore_clipboard_after_insert=_as_bool(data.get("restore_clipboard_after_insert"), defaults.restore_clipboard_after_insert),
            clipboard_clear_seconds=clamp_int(data.get("clipboard_clear_seconds"), 0, 3600, defaults.clipboard_clear_seconds),
            model_size=safe_choice(data.get("model_size"), MODEL_SIZES, defaults.model_size),
            local_model_path=safe_existing_directory(data.get("local_model_path")),
            compute_device=safe_choice(data.get("compute_device"), COMPUTE_DEVICES, defaults.compute_device),
            compute_type=safe_choice(data.get("compute_type"), COMPUTE_TYPES, defaults.compute_type),
            recognition_mode=safe_choice(data.get("recognition_mode"), RECOGNITION_MODES, defaults.recognition_mode),
            beam_size=clamp_int(data.get("beam_size"), 1, 10, defaults.beam_size),
            live_transcription_enabled=_as_bool(data.get("live_transcription_enabled"), defaults.live_transcription_enabled),
            live_preview_enabled=_as_bool(data.get("live_preview_enabled"), defaults.live_preview_enabled),
            live_chunk_seconds=clamp_number(data.get("live_chunk_seconds"), 3.0, 12.0, defaults.live_chunk_seconds),
            live_overlap_seconds=clamp_number(data.get("live_overlap_seconds"), 0.35, 2.5, defaults.live_overlap_seconds),
            noise_reduction=_as_bool(data.get("noise_reduction"), defaults.noise_reduction),
            normalize_audio=_as_bool(data.get("normalize_audio"), defaults.normalize_audio),
            microphone_gain=clamp_number(data.get("microphone_gain"), 0.25, 8.0, defaults.microphone_gain),
            auto_microphone_gain=_as_bool(data.get("auto_microphone_gain"), defaults.auto_microphone_gain),
            silence_stop_enabled=_as_bool(data.get("silence_stop_enabled"), defaults.silence_stop_enabled),
            silence_seconds=clamp_number(data.get("silence_seconds"), 1.0, 30.0, defaults.silence_seconds),
            silence_threshold=clamp_number(data.get("silence_threshold"), 0.001, 0.25, defaults.silence_threshold),
            max_recording_seconds=normalize_max_recording_seconds(data.get("max_recording_seconds"), defaults.max_recording_seconds),
            start_stop_sound=_as_bool(data.get("start_stop_sound"), defaults.start_stop_sound),
            save_history=save_history,
            save_audio=save_audio,
            private_mode=private_mode,
            writing_style=safe_choice(data.get("writing_style"), WRITING_STYLES, defaults.writing_style),
            enabled=_as_bool(data.get("enabled"), defaults.enabled),
        )


@dataclass(slots=True)
class TranscriptionResult:
    original_text: str
    final_text: str
    detected_language: str
    language_probability: float
    translated: bool
    duration_seconds: float
    word_count: int
    target_application: str = ""
    audio_path: str = ""
    processing_seconds: float = 0.0
    streaming_used: bool = False
    realtime_factor: float = 0.0
    model_device: str = ""
    model_compute_type: str = ""
    phase_timings: dict[str, float] = field(default_factory=dict)
