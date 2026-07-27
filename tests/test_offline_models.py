import tempfile
import unittest
from pathlib import Path

from localvoice.core.transcription import ModelMissingError, WhisperEngine
from localvoice.core.translation import LocalTranslator


class _Target:
    def __init__(self, code):
        self.code = code


class _Translation:
    def __init__(self, source, target, marker):
        self.from_code = source
        self.to_lang = _Target(target)
        self.marker = marker

    def translate(self, text):
        return f"{text}|{self.marker}"


class _Language:
    def __init__(self, code, translations):
        self.code = code
        self.translations_from = translations


class OfflineModelTests(unittest.TestCase):
    def test_dictation_does_not_download_a_missing_model(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = WhisperEngine()
            engine.model_cache_path = lambda _size: Path(directory) / "missing"  # type: ignore[method-assign]
            audio = Path(directory) / "audio.wav"
            audio.write_bytes(b"not-used")
            with self.assertRaisesRegex(ModelMissingError, "MODEL_MISSING"):
                engine.transcribe(audio, model_size="small")

    def test_translation_uses_installed_bridge_offline(self):
        translator = LocalTranslator()
        en_de = _Translation("en", "de", "en-de")
        fr_en = _Translation("fr", "en", "fr-en")
        translator._installed_languages = lambda: [  # type: ignore[method-assign]
            _Language("fr", [fr_en]), _Language("en", [en_de]), _Language("de", [])
        ]
        self.assertEqual(translator.translate("bonjour", "fr", "de", "en"), "bonjour|fr-en|en-de")


if __name__ == "__main__":
    unittest.main()


def test_managed_model_manifest_detects_tampering():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory) / "small"
        folder.mkdir()
        (folder / "config.json").write_text("{}", encoding="utf-8")
        (folder / "model.bin").write_bytes(b"model-weights")
        engine = WhisperEngine()
        engine.model_cache_path = lambda _size: folder  # type: ignore[method-assign]
        engine._write_manifest(folder, "small")
        assert engine.resolve_model_path("small") == folder
        (folder / "model.bin").write_bytes(b"tampered-data")
        # Integrity is verified once per application process before loading. A
        # fresh engine represents the next launch and must reject tampering.
        fresh_engine = WhisperEngine()
        fresh_engine.model_cache_path = lambda _size: folder  # type: ignore[method-assign]
        with unittest.TestCase().assertRaisesRegex(ModelMissingError, "MODEL_MISSING"):
            fresh_engine.resolve_model_path("small")


def test_invalid_model_name_cannot_escape_model_directory():
    engine = WhisperEngine()
    with unittest.TestCase().assertRaises(ModelMissingError):
        engine.remove_model("../../outside")


def test_model_manager_replaces_unmanifested_managed_model_instead_of_self_signing(monkeypatch):
    import sys
    import types
    import localvoice.core.transcription as transcription_module

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = root / "small"
        target.mkdir()
        (target / "config.json").write_text("{}", encoding="utf-8")
        (target / "model.bin").write_bytes(b"planted-untrusted-model")

        def fake_download(_alias, output_dir, local_files_only=False):
            assert local_files_only is False
            output = Path(output_dir)
            (output / "config.json").write_text("{}", encoding="utf-8")
            (output / "model.bin").write_bytes(b"fresh-explicit-download")

        fake_utils = types.ModuleType("faster_whisper.utils")
        fake_utils.download_model = fake_download
        fake_package = types.ModuleType("faster_whisper")
        fake_package.utils = fake_utils
        monkeypatch.setitem(sys.modules, "faster_whisper", fake_package)
        monkeypatch.setitem(sys.modules, "faster_whisper.utils", fake_utils)
        monkeypatch.setattr(transcription_module, "MODELS_DIR", root)

        engine = WhisperEngine()
        engine.model_cache_path = lambda _size: target  # type: ignore[method-assign]
        monkeypatch.setattr(engine, "_load_model", lambda *args, **kwargs: None)
        engine.ensure_model("small")

        assert (target / "model.bin").read_bytes() == b"fresh-explicit-download"
        assert (target / engine.MANIFEST_NAME).is_file()
        assert not list(root.glob(".small.rejected-*"))
