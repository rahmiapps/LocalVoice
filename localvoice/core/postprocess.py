from __future__ import annotations

import re
from typing import Iterable

from .number_normalization import normalize_spoken_numbers


COMMANDS: dict[str, dict[str, str]] = {
    "de": {
        "neuer absatz": "\n\n", "neue zeile": "\n", "punkt": ".", "komma": ",",
        "fragezeichen": "?", "ausrufezeichen": "!", "doppelpunkt": ":", "semikolon": ";",
        "anführungszeichen auf": "„", "anführungszeichen zu": "“", "klammer auf": "(", "klammer zu": ")",
    },
    "en": {
        "new paragraph": "\n\n", "new line": "\n", "period": ".", "full stop": ".", "comma": ",",
        "question mark": "?", "exclamation mark": "!", "colon": ":", "semicolon": ";",
        "open quote": "\"", "close quote": "\"", "open bracket": "(", "close bracket": ")",
    },
    "fr": {
        "nouveau paragraphe": "\n\n", "nouvelle ligne": "\n", "point": ".", "virgule": ",",
        "point d'interrogation": "?", "point d'exclamation": "!", "deux-points": ":", "point-virgule": ";",
        "ouvrir les guillemets": "«", "fermer les guillemets": "»", "ouvrir la parenthèse": "(", "fermer la parenthèse": ")",
    },
    "it": {
        "nuovo paragrafo": "\n\n", "nuova riga": "\n", "punto": ".", "virgola": ",",
        "punto interrogativo": "?", "punto esclamativo": "!", "due punti": ":", "punto e virgola": ";",
        "apri virgolette": "“", "chiudi virgolette": "”", "apri parentesi": "(", "chiudi parentesi": ")",
    },
    "es": {
        "nuevo párrafo": "\n\n", "nueva línea": "\n", "punto": ".", "coma": ",",
        "signo de interrogación": "?", "signo de exclamación": "!", "dos puntos": ":", "punto y coma": ";",
        "abrir comillas": "“", "cerrar comillas": "”", "abrir paréntesis": "(", "cerrar paréntesis": ")",
    },
    "zh": {
        "新段落": "\n\n", "换行": "\n", "句号": "。", "逗号": "，", "问号": "？", "感叹号": "！",
        "冒号": "：", "分号": "；", "左引号": "“", "右引号": "”", "左括号": "（", "右括号": "）",
    },
    "tr": {
        "yeni paragraf": "\n\n", "yeni satır": "\n", "nokta": ".", "virgül": ",",
        "soru işareti": "?", "ünlem işareti": "!", "iki nokta": ":", "noktalı virgül": ";",
        "tırnak aç": "“", "tırnak kapat": "”", "parantez aç": "(", "parantez kapat": ")",
    },
    "ar": {
        "فقرة جديدة": "\n\n", "سطر جديد": "\n", "نقطة": ".", "فاصلة": "،",
        "علامة استفهام": "؟", "علامة تعجب": "!", "نقطتان": ":", "فاصلة منقوطة": "؛",
        "افتح قوس": "(", "اغلق قوس": ")",
    },
    "pt": {
        "novo parágrafo": "\n\n", "nova linha": "\n", "ponto": ".", "vírgula": ",",
        "ponto de interrogação": "?", "ponto de exclamação": "!", "dois pontos": ":", "ponto e vírgula": ";",
        "abrir aspas": "“", "fechar aspas": "”", "abrir parênteses": "(", "fechar parênteses": ")",
    },
    "nl": {
        "nieuwe alinea": "\n\n", "nieuwe regel": "\n", "punt": ".", "komma": ",",
        "vraagteken": "?", "uitroepteken": "!", "dubbele punt": ":", "puntkomma": ";",
    },
    "pl": {
        "nowy akapit": "\n\n", "nowa linia": "\n", "kropka": ".", "przecinek": ",",
        "znak zapytania": "?", "wykrzyknik": "!", "dwukropek": ":", "średnik": ";",
    },
    "ru": {
        "новый абзац": "\n\n", "новая строка": "\n", "точка": ".", "запятая": ",",
        "вопросительный знак": "?", "восклицательный знак": "!", "двоеточие": ":", "точка с запятой": ";",
    },
    "ja": {
        "新しい段落": "\n\n", "改行": "\n", "句点": "。", "読点": "、", "疑問符": "？", "感嘆符": "！",
    },
    "ko": {
        "새 문단": "\n\n", "새 줄": "\n", "마침표": ".", "쉼표": ",", "물음표": "?", "느낌표": "!",
    },
}

DELETE_LAST_SENTENCE = {
    "de": ["lösche letzten satz", "letzten satz löschen"],
    "en": ["delete last sentence", "remove last sentence"],
    "fr": ["supprimer la dernière phrase", "efface la dernière phrase"],
    "it": ["elimina l'ultima frase", "cancella l'ultima frase"],
    "es": ["elimina la última frase", "borra la última frase"],
    "zh": ["删除上一句", "删掉上一句"],
    "tr": ["son cümleyi sil"],
    "ar": ["احذف الجملة الأخيرة"],
    "pt": ["apagar última frase", "excluir última frase"],
    "nl": ["verwijder laatste zin"],
    "pl": ["usuń ostatnie zdanie"],
    "ru": ["удали последнее предложение"],
    "ja": ["最後の文を削除"],
    "ko": ["마지막 문장 삭제"],
}

FILLERS = {
    "de": ["äh", "ähm", "hm"],
    "en": ["um", "uh", "erm"],
    "fr": ["euh"],
    "it": ["ehm"],
    "es": ["eh", "em"],
    "tr": ["eee", "ııı"],
    "pt": ["hum", "ahn"],
    "nl": ["eh", "uh"],
    "pl": ["yyy"],
    "ru": ["эм"],
    "ja": ["えーと"],
    "ko": ["음"],
}



class TextPostProcessor:
    MAX_TEXT_LENGTH = 2_000_000

    def process(
        self,
        text: str,
        language: str,
        vocabulary: Iterable[dict[str, object]] = (),
        spoken_commands: bool = True,
        remove_filler_words: bool = False,
        numbers_as_digits: bool = False,
        automatic_punctuation: bool = True,
        writing_style: str = "neutral",
    ) -> str:
        result = str(text).replace("\x00", "")[: self.MAX_TEXT_LENGTH].strip()
        if not result:
            return result
        if spoken_commands:
            result = self._replace_commands(result, language)
            result = self._apply_edit_commands(result, language)
        if remove_filler_words:
            for filler in FILLERS.get(language, []):
                result = re.sub(rf"(?<!\w){re.escape(filler)}(?!\w)[, ]*", "", result, flags=re.IGNORECASE)
        if numbers_as_digits:
            result = normalize_spoken_numbers(result, language)
        result = self.apply_vocabulary(result, language, vocabulary)
        result = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", result, flags=re.IGNORECASE)
        result = re.sub(r"[ \t]+([,.;:!?。！？；：،؛؟])", r"\1", result)
        result = re.sub(r"([,.;:!?。！？；：،؛؟])(?=[^\s\n])", r"\1 ", result)
        result = re.sub(r"[ \t]{2,}", " ", result)
        result = re.sub(r" *\n *", "\n", result)
        if writing_style == "code":
            return result.strip()
        if automatic_punctuation:
            result = self._capitalize_sentences(result, language)
            if writing_style in {"neutral", "email"} and result and result[-1] not in ".!?。！？؟":
                result += "。" if language in {"zh", "ja"} else "."
        return result.strip()

    @staticmethod
    def _apply_edit_commands(text: str, language: str) -> str:
        result = text
        for command in DELETE_LAST_SENTENCE.get(language, DELETE_LAST_SENTENCE["en"]):
            pattern = re.compile(rf"(?<!\w){re.escape(command)}(?!\w)", re.IGNORECASE)
            while True:
                match = pattern.search(result)
                if not match:
                    break
                before = result[:match.start()].rstrip()
                after = result[match.end():].lstrip()
                sentence_endings = ".!?。！？؟\n"
                trimmed = before.rstrip()
                if trimmed and trimmed[-1] in sentence_endings:
                    trimmed = trimmed[:-1].rstrip()
                previous_end = max((trimmed.rfind(char) for char in sentence_endings), default=-1)
                before = trimmed[: previous_end + 1].rstrip() if previous_end >= 0 else ""
                result = (before + (" " if before and after else "") + after).strip()
        return result

    @staticmethod
    def _replace_commands(text: str, language: str) -> str:
        commands = COMMANDS.get(language, COMMANDS.get("en", {}))
        result = text
        for spoken, written in sorted(commands.items(), key=lambda item: len(item[0]), reverse=True):
            result = re.sub(
                rf"(?<!\w){re.escape(spoken)}(?!\w)",
                lambda _m, value=written: value,
                result,
                flags=re.IGNORECASE,
            )
        return result

    @staticmethod
    def apply_vocabulary(text: str, language: str, vocabulary: Iterable[dict[str, object]]) -> str:
        result = text
        for entry in vocabulary:
            entry_language = str(entry.get("language", "all"))
            if entry_language not in {"all", language}:
                continue
            spoken = str(entry.get("spoken_form", "")).replace("\x00", "").strip()[:500]
            written = str(entry.get("written_form", "")).replace("\x00", "").strip()[:500]
            if not spoken or not written:
                continue
            flags = 0 if bool(entry.get("case_sensitive", False)) else re.IGNORECASE
            result = re.sub(
                rf"(?<!\w){re.escape(spoken)}(?!\w)",
                lambda _m, value=written: value,
                result,
                flags=flags,
            )
        return result

    @staticmethod
    def _capitalize_sentences(text: str, language: str) -> str:
        if language in {"zh", "ja", "ko"}:
            return text
        chars = list(text)
        should_capitalize = True
        for index, char in enumerate(chars):
            if should_capitalize and char.isalpha():
                chars[index] = char.upper()
                should_capitalize = False
            elif char in ".!?\n؟":
                should_capitalize = True
        return "".join(chars)


def count_words(text: str) -> int:
    """Count written words across whitespace-delimited and CJK scripts.

    Whisper output in Chinese/Japanese/Korean often contains few or no spaces.
    Counting each CJK/Hiragana/Katakana/Hangul character as a written unit while
    keeping Latin/number sequences as words gives stable multilingual statistics.
    """
    clean = str(text or "").replace("\x00", "")[: TextPostProcessor.MAX_TEXT_LENGTH]
    tokens = re.findall(
        r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž0-9_]+(?:['’\-][A-Za-zÀ-ÖØ-öø-ÿĀ-ž0-9_]+)*"
        r"|[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]",
        clean,
    )
    return len(tokens)
