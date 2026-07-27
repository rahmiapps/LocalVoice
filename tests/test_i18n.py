import unittest
from localvoice.core.i18n import LANGUAGES, validate_translations


class TranslationTests(unittest.TestCase):
    def test_all_interface_languages_contain_all_keys(self):
        missing = validate_translations()
        self.assertEqual(set(missing), set(LANGUAGES))
        self.assertTrue(all(not values for values in missing.values()), missing)


if __name__ == "__main__":
    unittest.main()


def test_current_whisper_language_catalogue_is_centralized_and_complete():
    from localvoice.core.i18n import SPEECH_LANGUAGES, speech_language_name
    from localvoice.core.languages import SUPPORTED_SPEECH_LANGUAGE_CODES
    from localvoice.core.validation import SUPPORTED_SPEECH_LANGUAGES, normalize_language

    assert len(SUPPORTED_SPEECH_LANGUAGE_CODES) == 100
    assert set(SPEECH_LANGUAGES) == {"auto", *SUPPORTED_SPEECH_LANGUAGE_CODES}
    assert SUPPORTED_SPEECH_LANGUAGES == {"auto", *SUPPORTED_SPEECH_LANGUAGE_CODES}
    for code in ("ca", "ta", "ur", "yue", "haw", "su"):
        assert normalize_language(code, allow_auto=False, default="") == code
        assert speech_language_name("de", code)
