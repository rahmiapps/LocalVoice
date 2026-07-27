from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import uuid
import wave
from pathlib import Path
from typing import Callable

from .paths import MODELS_DIR, ensure_directories
from .validation import normalize_language, safe_existing_directory


MODEL_ALIASES = {
    "tiny": "tiny",
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large": "large-v3",
    "turbo": "turbo",
}

LANGUAGE_PROMPTS = {
    "de": "Deutsche Diktataufnahme. Schreibe vollständige deutsche Sätze mit korrekter Groß- und Kleinschreibung und natürlicher Zeichensetzung.",
    "en": "English dictation. Write complete English sentences with natural punctuation.",
    "fr": "Dictée française. Écris des phrases françaises complètes avec une ponctuation naturelle.",
    "it": "Dettatura italiana. Scrivi frasi italiane complete con punteggiatura naturale.",
    "es": "Dictado en español. Escribe frases completas con puntuación natural.",
    "zh": "中文听写。请使用自然、完整的中文句子和正确标点。",
}

LANGUAGE_MARKERS = {
    "de": {"ich", "du", "wir", "das", "der", "die", "und", "nicht", "aber", "warum", "gerade", "schneller", "aufnehmen", "deutsch"},
    "en": {"i", "you", "we", "the", "this", "and", "not", "but", "why", "english", "test"},
    "fr": {"je", "tu", "nous", "le", "la", "et", "pas", "mais", "pourquoi", "français"},
    "it": {"io", "tu", "noi", "il", "la", "e", "non", "ma", "perché", "italiano"},
    "es": {"yo", "tú", "nosotros", "el", "la", "y", "no", "pero", "por qué", "español"},
}


class ModelMissingError(RuntimeError):
    pass


class ModelIntegrityError(RuntimeError):
    pass


class WhisperEngine:
    REQUIRED_FILES = ("config.json", "model.bin")
    MANIFEST_NAME = "localvoice-model-manifest.json"
    MAX_MODEL_FILES = 2_000
    MAX_MODEL_BYTES = 20 * 1024 * 1024 * 1024

    def __init__(self) -> None:
        ensure_directories()
        self._model = None
        self._signature: tuple[str, str, str] | None = None
        self._lock = threading.RLock()
        self._verified_manifests: dict[str, tuple[int, tuple[tuple[str, int, int, int], ...]]] = {}

    @staticmethod
    def _normalize_model_size(model_size: str) -> str:
        value = str(model_size or "").strip().lower()
        if value not in MODEL_ALIASES:
            raise ModelMissingError("MODEL_MISSING:INVALID")
        return value

    def model_cache_path(self, model_size: str) -> Path:
        normalized = self._normalize_model_size(model_size)
        alias = MODEL_ALIASES[normalized]
        path = (MODELS_DIR / alias).resolve()
        root = MODELS_DIR.resolve()
        if path.parent != root:
            raise ModelIntegrityError("The managed model path is invalid.")
        return path

    @classmethod
    def _basic_model_directory_valid(cls, folder: Path) -> bool:
        try:
            if not folder.is_dir() or folder.is_symlink():
                return False
            for filename in cls.REQUIRED_FILES:
                path = folder / filename
                if not path.is_file() or path.is_symlink():
                    return False
            return True
        except OSError:
            return False

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def _model_files(cls, folder: Path) -> list[Path]:
        files: list[Path] = []
        total = 0
        for path in sorted(folder.rglob("*")):
            if path.name == cls.MANIFEST_NAME:
                continue
            if path.is_symlink():
                raise ModelIntegrityError("Speech model directories may not contain symbolic links.")
            if not path.is_file():
                continue
            relative = path.relative_to(folder)
            if ".." in relative.parts:
                raise ModelIntegrityError("Speech model contains an invalid path.")
            size = path.stat().st_size
            if size < 0:
                raise ModelIntegrityError("Speech model contains an invalid file.")
            total += size
            files.append(path)
            if len(files) > cls.MAX_MODEL_FILES or total > cls.MAX_MODEL_BYTES:
                raise ModelIntegrityError("Speech model exceeds the safety limits.")
        return files

    def _write_manifest(self, folder: Path, model_size: str) -> None:
        if not self._basic_model_directory_valid(folder):
            raise ModelIntegrityError("The speech model is incomplete.")
        files = self._model_files(folder)
        record = {
            "version": 1,
            "model": self._normalize_model_size(model_size),
            "source": "faster-whisper-explicit-model-manager",
            "files": {
                str(path.relative_to(folder)).replace(os.sep, "/"): {
                    "size": path.stat().st_size,
                    "sha256": self._sha256(path),
                }
                for path in files
            },
        }
        manifest = folder / self.MANIFEST_NAME
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        temporary.replace(manifest)
        self._verified_manifests.pop(str(folder.resolve()), None)

    def _verify_managed_model(self, folder: Path, model_size: str, *, full: bool = True) -> bool:
        if not self._basic_model_directory_valid(folder):
            return False
        manifest = folder / self.MANIFEST_NAME
        if not manifest.is_file() or manifest.is_symlink() or manifest.stat().st_size > 2 * 1024 * 1024:
            return False
        try:
            record = json.loads(manifest.read_text(encoding="utf-8"))
            if record.get("version") != 1 or record.get("model") != self._normalize_model_size(model_size):
                return False
            expected = record.get("files")
            if not isinstance(expected, dict) or not expected or len(expected) > self.MAX_MODEL_FILES:
                return False
            files = self._model_files(folder)
            states = tuple(
                (
                    str(path.relative_to(folder)).replace(os.sep, "/"),
                    path.stat().st_size,
                    path.stat().st_mtime_ns,
                    path.stat().st_ctime_ns,
                )
                for path in files
            )
            cache_key = str(folder.resolve())
            manifest_mtime = manifest.stat().st_mtime_ns
            if full and self._verified_manifests.get(cache_key) == (manifest_mtime, states):
                return True
            actual_names = {state[0] for state in states}
            if actual_names != set(expected):
                return False
            for path in files:
                relative = str(path.relative_to(folder)).replace(os.sep, "/")
                metadata = expected.get(relative)
                if not isinstance(metadata, dict):
                    return False
                if int(metadata.get("size", -1)) != path.stat().st_size:
                    return False
                checksum = str(metadata.get("sha256", ""))
                if len(checksum) != 64 or not all(char in "0123456789abcdef" for char in checksum):
                    return False
                if full and self._sha256(path) != checksum:
                    return False
            if full:
                self._verified_manifests[cache_key] = (manifest_mtime, states)
            return True
        except (OSError, ValueError, TypeError, json.JSONDecodeError, ModelMissingError, ModelIntegrityError):
            return False

    def resolve_model_path(self, model_size: str, local_model_path: str = "") -> Path:
        normalized = self._normalize_model_size(model_size)
        if local_model_path:
            safe_path = safe_existing_directory(local_model_path)
            if not safe_path:
                raise ModelMissingError("MODEL_MISSING:CUSTOM")
            path = Path(safe_path).resolve()
            if not self._basic_model_directory_valid(path):
                raise ModelMissingError("MODEL_MISSING:CUSTOM")
            try:
                self._model_files(path)
            except ModelIntegrityError as exc:
                raise ModelMissingError("MODEL_MISSING:CUSTOM") from exc
            return path
        path = self.model_cache_path(normalized)
        if not self._verify_managed_model(path, normalized):
            raise ModelMissingError(f"MODEL_MISSING:{normalized}")
        return path

    def is_model_available(self, model_size: str, local_model_path: str = "") -> bool:
        try:
            normalized = self._normalize_model_size(model_size)
            if local_model_path:
                safe_path = safe_existing_directory(local_model_path)
                if not safe_path:
                    return False
                custom = Path(safe_path).resolve()
                if not self._basic_model_directory_valid(custom):
                    return False
                self._model_files(custom)
                return True
            return self._verify_managed_model(self.model_cache_path(normalized), normalized, full=False)
        except (ModelMissingError, ModelIntegrityError, OSError):
            return False

    def installed_models(self) -> list[str]:
        return [name for name in MODEL_ALIASES if self.is_model_available(name)]

    def _resolve_device(self, requested: str) -> str:
        if requested in {"cpu", "cuda"}:
            return requested
        if os.environ.get("LOCALVOICE_FORCE_CUDA") == "1":
            return "cuda"
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                return "cuda"
        except Exception:
            pass
        return "cpu"

    def resolved_device_for(self, requested: str) -> str:
        """Return the device LocalVoice would use without loading a model."""
        return self._resolve_device(requested)

    @staticmethod
    def _recommended_cpu_threads() -> int:
        logical = max(1, int(os.cpu_count() or 4))
        physical = 0
        try:
            import psutil
            physical = int(psutil.cpu_count(logical=False) or 0)
        except Exception:
            physical = 0
        # Medium and large models were previously capped at eight threads even on
        # modern desktop CPUs. Prefer physical cores, keep one core for the UI,
        # and cap at sixteen because CTranslate2 can regress with extreme counts.
        basis = physical or max(1, logical // 2)
        return max(2, min(16, basis - 1 if basis >= 6 else basis))

    def loaded_status(self) -> dict[str, object]:
        with self._lock:
            signature = self._signature
            return {
                "loaded": self._model is not None and signature is not None,
                "path": signature[0] if signature else "",
                "device": signature[1] if signature else "",
                "compute_type": signature[2] if signature else "",
                "cpu_threads": self._recommended_cpu_threads(),
            }

    def is_loaded_for(
        self,
        model_size: str,
        device: str = "auto",
        compute_type: str = "auto",
        local_model_path: str = "",
    ) -> bool:
        try:
            if local_model_path:
                safe_path = safe_existing_directory(local_model_path)
                if not safe_path:
                    return False
                path = Path(safe_path).resolve()
            else:
                path = self.model_cache_path(model_size)
            resolved_device = self._resolve_device(device)
            resolved_compute = compute_type
            if compute_type == "auto":
                resolved_compute = "float16" if resolved_device == "cuda" else "int8"
            with self._lock:
                if self._model is None or self._signature is None:
                    return False
                loaded_path, loaded_device, loaded_compute = self._signature
                if loaded_path != str(path.resolve()):
                    return False
                if device == "auto":
                    return loaded_device in {"cpu", "cuda"}
                return loaded_device == resolved_device and loaded_compute == resolved_compute
        except Exception:
            return False

    def _load_model(
        self,
        model_path: Path,
        device: str,
        compute_type: str,
        progress: Callable[[str], None] | None = None,
    ) -> None:
        from faster_whisper import WhisperModel

        resolved_device = self._resolve_device(device)
        resolved_compute = compute_type
        if compute_type == "auto":
            resolved_compute = "float16" if resolved_device == "cuda" else "int8"
        signature = (str(model_path.resolve()), resolved_device, resolved_compute)
        with self._lock:
            if self._model is not None and self._signature == signature:
                return
            if progress:
                progress("loading")
            try:
                model = WhisperModel(
                    str(model_path),
                    device=resolved_device,
                    compute_type=resolved_compute,
                    local_files_only=True,
                    cpu_threads=self._recommended_cpu_threads(),
                    num_workers=1,
                )
            except Exception:
                # Automatic mode may detect CUDA while the installed runtime is not usable.
                if device == "auto" and resolved_device == "cuda":
                    model = WhisperModel(
                        str(model_path),
                        device="cpu",
                        compute_type="int8" if compute_type == "auto" else compute_type,
                        local_files_only=True,
                        cpu_threads=self._recommended_cpu_threads(),
                        num_workers=1,
                    )
                    signature = (str(model_path.resolve()), "cpu", "int8" if compute_type == "auto" else compute_type)
                else:
                    raise
            self._model = model
            self._signature = signature


    def _discard_unverified_managed_model(self, target: Path) -> None:
        """Remove an untrusted managed model without ever blessing its contents.

        Managed directories are created only beneath LocalVoice's model cache. An
        existing directory without a valid LocalVoice manifest may have been copied
        there manually or altered by another process, so the model manager replaces
        it with a freshly downloaded and hashed directory.
        """
        if not target.exists() and not target.is_symlink():
            return
        root = MODELS_DIR.resolve()
        try:
            if target.resolve(strict=False).parent != root:
                raise ModelIntegrityError("The managed model path is outside the model cache.")
            if target.is_symlink():
                target.unlink()
                return
            quarantine = target.with_name(f".{target.name}.rejected-{uuid.uuid4().hex}")
            target.replace(quarantine)
            shutil.rmtree(quarantine, ignore_errors=True)
        except (OSError, RuntimeError) as exc:
            raise ModelIntegrityError("The unverified speech model could not be replaced safely.") from exc

    def ensure_model(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "auto",
        local_model_path: str = "",
        progress: Callable[[str], None] | None = None,
    ) -> None:
        """Explicitly download and validate a model from the model manager.

        Normal dictation never calls a network download. It only loads a verified
        local directory so offline/privacy guarantees cannot silently change.
        """
        if local_model_path:
            path = self.resolve_model_path(model_size, local_model_path)
            self._load_model(path, device, compute_type, progress)
            return
        normalized = self._normalize_model_size(model_size)
        alias = MODEL_ALIASES[normalized]
        target = self.model_cache_path(normalized)
        if self._verify_managed_model(target, normalized):
            self._load_model(target, device, compute_type, progress)
            return
        # Never create a trusted manifest for files that were already present.
        # Only a fresh explicit model-manager download is hashed and admitted.
        self._discard_unverified_managed_model(target)
        from faster_whisper.utils import download_model

        temp = MODELS_DIR / f".{alias}-{uuid.uuid4().hex}.download"
        temp.mkdir(parents=True, exist_ok=False)
        try:
            if progress:
                progress("download")
            download_model(alias, output_dir=str(temp), local_files_only=False)
            if not self._basic_model_directory_valid(temp):
                raise ModelIntegrityError("The downloaded model is incomplete.")
            self._write_manifest(temp, normalized)
            if not self._verify_managed_model(temp, normalized):
                raise ModelIntegrityError("The downloaded model failed its integrity check.")
            if target.exists():
                shutil.rmtree(target)
            temp.replace(target)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        self._load_model(target, device, compute_type, progress)

    def remove_model(self, model_size: str) -> None:
        normalized = self._normalize_model_size(model_size)
        path = self.model_cache_path(normalized)
        with self._lock:
            if self._signature and Path(self._signature[0]) == path.resolve():
                self._model = None
                self._signature = None
        if path.exists():
            shutil.rmtree(path)

    def preload(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "auto",
        local_model_path: str = "",
    ) -> None:
        """Load an already installed model without downloading anything."""
        path = self.resolve_model_path(model_size, local_model_path)
        self._load_model(path, device, compute_type)

    @staticmethod
    def _audio_duration(path: Path) -> float:
        try:
            with wave.open(str(path), "rb") as wav:
                rate = max(1, int(wav.getframerate()))
                return max(0.0, float(wav.getnframes()) / rate)
        except (OSError, wave.Error, ValueError):
            return 0.0

    @staticmethod
    def _language_text_bonus(text: str, language: str) -> float:
        if not text or language not in LANGUAGE_MARKERS:
            return 0.0
        words = {
            token.casefold().strip(".,!?;:()[]{}\"'„“”)")
            for token in text.split()
            if token.strip()
        }
        matches = len(words.intersection(LANGUAGE_MARKERS[language]))
        return min(0.16, matches * 0.035)

    @staticmethod
    def _hotword_text(values: list[str] | None) -> str | None:
        if not values:
            return None
        result: list[str] = []
        total = 0
        for value in values:
            clean = str(value or "").replace("\x00", " ").strip()
            if not clean or clean in result:
                continue
            clean = clean[:80]
            if total + len(clean) > 320:
                break
            result.append(clean)
            total += len(clean)
            if len(result) >= 30:
                break
        return ", ".join(result) or None

    def transcribe(
        self,
        audio_path: Path,
        model_size: str = "small",
        language: str = "auto",
        preferred_languages: list[str] | None = None,
        prefer_primary_language: bool = True,
        device: str = "auto",
        compute_type: str = "auto",
        recognition_mode: str = "balanced",
        beam_size: int = 2,
        language_detection_threshold: float = 0.35,
        hotwords: list[str] | None = None,
        local_model_path: str = "",
        progress: Callable[[str], None] | None = None,
        context_prompt: str = "",
        streaming: bool = False,
    ) -> tuple[str, str, float]:
        """Transcribe once in the normal path and retry only when justified.

        Earlier balanced builds could run the complete recording several times:
        auto detection, multiple preferred-language comparisons and a VAD rescue.
        That made a longer sentence take around ten seconds. Balanced mode now
        uses one main pass. A second pass is limited to very short ambiguous
        utterances or to an empty VAD result; Accurate mode may still compare
        additional candidates deliberately.
        """
        if not audio_path.is_file():
            raise RuntimeError("The recording file no longer exists.")
        model_path = self.resolve_model_path(model_size, local_model_path)
        self._load_model(model_path, device, compute_type, progress)
        selected = normalize_language(language, default="auto")
        mode = str(recognition_mode or "balanced").strip().lower()
        if mode not in {"fast", "balanced", "accurate"}:
            mode = "balanced"
        if streaming:
            mode = "fast"
        requested_beam = max(1, min(int(beam_size), 10))
        duration = self._audio_duration(audio_path)
        if mode == "fast":
            decode_beam = 1
            detection_segments = 1
        elif mode == "accurate":
            decode_beam = max(3, requested_beam)
            detection_segments = 5
        else:
            decode_beam = 1 if duration <= 30.0 else min(2, requested_beam)
            detection_segments = 2
        detection_threshold = max(0.25, min(float(language_detection_threshold), 0.95))
        hotword_text = self._hotword_text(hotwords)

        candidates: list[str] = []
        for code in preferred_languages or []:
            candidate = normalize_language(code, allow_auto=False, default="")
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        primary = candidates[0] if candidates and prefer_primary_language else ""

        # Push-to-talk recordings already have explicit start/stop boundaries.
        # Skipping Silero VAD for ordinary dictation both saves time and preserves
        # quiet/distant speech. Accurate mode and very long recordings still use
        # VAD to control long silences.
        main_use_vad = False if streaming else (mode == "accurate" or duration > 45.0)

        def run(
            selected_language: str | None,
            selected_beam: int,
            *,
            use_vad: bool,
            prompt_language: str = "",
        ):
            prompt = LANGUAGE_PROMPTS.get(prompt_language or selected_language or "", "")
            clean_context = str(context_prompt or "").replace("\x00", " ").strip()[-320:]
            if clean_context:
                prompt = f"{prompt}\nVorheriger Kontext / previous context: {clean_context}".strip()
            kwargs = dict(
                language=selected_language,
                task="transcribe",
                beam_size=max(1, min(int(selected_beam), 10)),
                best_of=1,
                patience=1.0,
                temperature=0.0,
                repetition_penalty=1.05,
                no_repeat_ngram_size=3,
                vad_filter=use_vad,
                condition_on_previous_text=(mode == "accurate" and duration > 20.0),
                initial_prompt=prompt,
                hotwords=hotword_text,
                without_timestamps=True,
                word_timestamps=False,
                language_detection_threshold=detection_threshold,
                language_detection_segments=detection_segments,
            )
            if use_vad:
                kwargs["vad_parameters"] = {
                    "threshold": 0.25,
                    "min_speech_duration_ms": 50,
                    "min_silence_duration_ms": 700,
                    "speech_pad_ms": 700,
                }
            segments_iter, information = self._model.transcribe(str(audio_path), **kwargs)
            segment_list = list(segments_iter)
            value = " ".join(segment.text.strip() for segment in segment_list if segment.text.strip()).strip()
            scores = [float(getattr(segment, "avg_logprob", -10.0)) for segment in segment_list]
            score = sum(scores) / len(scores) if scores else -10.0
            return value, information, score

        language_arg = None if selected == "auto" else selected
        prompt_language = primary if selected == "auto" else selected
        with self._lock:
            text, info, best_score = run(
                language_arg,
                decode_beam,
                use_vad=main_use_vad,
                prompt_language=prompt_language,
            )
            detected = normalize_language(
                getattr(info, "language", selected if selected != "auto" else ""),
                allow_auto=False,
                default=selected if selected != "auto" else "unknown",
            )
            probability = max(0.0, min(1.0, float(getattr(info, "language_probability", 0.0) or 0.0)))

            if not streaming and selected == "auto" and primary and detected != primary:
                # Short phrases contain little acoustic context and are the common
                # source of German/English confusion. Compare only the primary
                # language, and only for short or genuinely low-confidence input.
                short_ambiguous = duration <= 4.5
                low_confidence = probability < max(0.58, detection_threshold)
                primary_markers = self._language_text_bonus(text, primary) >= 0.035
                should_compare_primary = (
                    mode == "accurate"
                    or short_ambiguous
                    or (duration <= 12.0 and low_confidence)
                    or primary_markers
                )
                if should_compare_primary:
                    candidate_text, candidate_info, candidate_score = run(
                        primary,
                        1 if mode != "accurate" else decode_beam,
                        use_vad=False,
                        prompt_language=primary,
                    )
                    if candidate_text:
                        preference_bonus = 0.12 if short_ambiguous else 0.055
                        adjusted_candidate = candidate_score + preference_bonus + self._language_text_bonus(candidate_text, primary)
                        adjusted_current = best_score + self._language_text_bonus(text, detected)
                        if adjusted_candidate > adjusted_current + 0.01:
                            text = candidate_text
                            info = candidate_info
                            best_score = candidate_score
                            detected = primary
                            probability = max(probability, 0.74 if short_ambiguous else 0.66)

            if not streaming and selected == "auto" and mode == "accurate" and candidates:
                # Accurate mode explicitly trades speed for additional candidate
                # comparison. Balanced and Fast never enter this loop.
                for candidate in candidates[:3]:
                    if candidate == detected or candidate == primary:
                        continue
                    if detected in candidates and probability >= 0.82:
                        break
                    candidate_text, candidate_info, candidate_score = run(
                        candidate,
                        decode_beam,
                        use_vad=True,
                        prompt_language=candidate,
                    )
                    if not candidate_text:
                        continue
                    if candidate_score + self._language_text_bonus(candidate_text, candidate) > best_score + 0.07:
                        text = candidate_text
                        info = candidate_info
                        best_score = candidate_score
                        detected = candidate
                        probability = max(probability, 0.68)

            # A VAD retry is only useful if VAD returned no meaningful text. Do
            # not automatically double the processing time for every long sentence.
            word_count = len([item for item in text.split() if item.strip()])
            if main_use_vad and word_count <= 1 and duration >= 2.0:
                retry_language = detected if detected != "unknown" else language_arg
                retry_text, retry_info, retry_score = run(
                    retry_language,
                    1 if mode != "accurate" else decode_beam,
                    use_vad=False,
                    prompt_language=retry_language or primary,
                )
                if len(retry_text.split()) > word_count and retry_score >= best_score - 0.45:
                    text = retry_text
                    info = retry_info
                    best_score = retry_score
                    if retry_language:
                        detected = retry_language
                    probability = max(probability, 0.66)

        if selected != "auto" and probability <= 0.0:
            probability = 1.0
        return text, detected, probability
