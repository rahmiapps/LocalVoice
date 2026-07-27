import unittest
from localvoice.core.postprocess import TextPostProcessor, count_words


class PostProcessTests(unittest.TestCase):
    def test_german_commands_and_vocabulary(self):
        processor = TextPostProcessor()
        text = processor.process(
            "hallo komma das ist dayter x punkt neue zeile danke",
            "de",
            vocabulary=[{"spoken_form": "dayter x", "written_form": "DateraX", "language": "de"}],
        )
        self.assertIn("Hallo,", text)
        self.assertIn("DateraX.", text)
        self.assertIn("\nDanke", text)

    def test_duplicate_words(self):
        self.assertEqual(TextPostProcessor().process("hello hello world", "en", spoken_commands=False), "Hello world.")

    def test_delete_last_sentence_command(self):
        text = TextPostProcessor().process(
            "erster satz punkt zweiter satz punkt lösche letzten satz neuer satz punkt",
            "de",
        )
        self.assertEqual(text, "Erster satz. Neuer satz.")

    def test_multilingual_word_count_handles_unspaced_cjk(self):
        self.assertEqual(count_words("Hello 世界 123"), 4)
        self.assertEqual(count_words("这是中文"), 4)
        self.assertEqual(count_words("こんにちは"), 5)

    def test_dictionary_replacement_is_literal_not_regex_template(self):
        text = TextPostProcessor().process(
            "alpha",
            "en",
            vocabulary=[{"spoken_form": "alpha", "written_form": r"\1-${unsafe}", "language": "en"}],
            spoken_commands=False,
            writing_style="code",
        )
        self.assertEqual(text, r"\1-${unsafe}")


if __name__ == "__main__":
    unittest.main()


def test_spoken_number_phrases_are_normalized_in_primary_languages():
    processor = TextPostProcessor()
    cases = [
        ("en", "one hundred and twenty three", "123"),
        ("de", "eintausendzweihundertvierunddreißig", "1234"),
        ("fr", "quatre-vingt-dix-neuf", "99"),
        ("it", "duecentotrentotto", "238"),
        ("es", "novecientos noventa y nueve", "999"),
        ("zh", "一千二百三十四", "1234"),
    ]
    for language, spoken, expected in cases:
        result = processor.process(
            spoken,
            language,
            spoken_commands=False,
            numbers_as_digits=True,
            automatic_punctuation=False,
        )
        assert result == expected


def test_french_article_un_is_not_changed_when_it_is_not_a_number_phrase():
    result = TextPostProcessor().process(
        "un message important",
        "fr",
        spoken_commands=False,
        numbers_as_digits=True,
        automatic_punctuation=False,
    )
    assert result == "un message important"


def test_automatic_punctuation_adds_terminal_mark_for_neutral_but_not_chat():
    processor = TextPostProcessor()
    assert processor.process("hello world", "en", spoken_commands=False) == "Hello world."
    assert processor.process("hello world", "en", spoken_commands=False, writing_style="chat") == "Hello world"
    assert processor.process("你好世界", "zh", spoken_commands=False) == "你好世界。"


def test_small_spoken_numbers_are_supported_in_additional_languages():
    processor = TextPostProcessor()
    cases = [
        ("tr", "üç dosya", "3 dosya"),
        ("pt", "dois arquivos", "2 arquivos"),
        ("nl", "vier bestanden", "4 bestanden"),
        ("pl", "pięć plików", "5 plików"),
        ("ru", "семь файлов", "7 файлов"),
        ("ar", "ثلاثة ملفات", "3 ملفات"),
        ("ja", "三 ファイル", "3 ファイル"),
        ("ko", "셋 파일", "3 파일"),
    ]
    for language, source, expected in cases:
        assert processor.process(
            source,
            language,
            spoken_commands=False,
            numbers_as_digits=True,
            automatic_punctuation=False,
        ) == expected
