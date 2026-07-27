from __future__ import annotations

import re
from functools import lru_cache

# Local, deterministic spoken-number normalization for the six primary UI
# languages.  The generated phrase tables cover the range 0..9999 and do not
# execute user-supplied patterns.

_EN_SMALL = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
]
_EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _en(n: int, *, use_and: bool = False) -> str:
    if n < 20:
        return _EN_SMALL[n]
    if n < 100:
        return _EN_TENS[n // 10] + (" " + _EN_SMALL[n % 10] if n % 10 else "")
    if n < 1000:
        rest = n % 100
        return _EN_SMALL[n // 100] + " hundred" + ((" and " if use_and else " ") + _en(rest, use_and=use_and) if rest else "")
    rest = n % 1000
    return _en(n // 1000, use_and=use_and) + " thousand" + (" " + _en(rest, use_and=use_and) if rest else "")


_DE_SMALL = [
    "null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun",
    "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn",
]
_DE_TENS = ["", "", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig", "siebzig", "achtzig", "neunzig"]


def _de_under_100(n: int) -> str:
    if n < 20:
        return _DE_SMALL[n]
    if n % 10 == 0:
        return _DE_TENS[n // 10]
    unit = "ein" if n % 10 == 1 else _DE_SMALL[n % 10]
    return unit + "und" + _DE_TENS[n // 10]


def _de(n: int) -> str:
    if n < 100:
        return _de_under_100(n)
    if n < 1000:
        prefix = "ein" if n // 100 == 1 else _DE_SMALL[n // 100]
        return prefix + "hundert" + (_de_under_100(n % 100) if n % 100 else "")
    prefix = "ein" if n // 1000 == 1 else _de(n // 1000)
    return prefix + "tausend" + (_de(n % 1000) if n % 1000 else "")


def _de_spaced(n: int) -> str:
    if n < 20:
        return _DE_SMALL[n]
    if n < 100:
        if n % 10 == 0:
            return _DE_TENS[n // 10]
        unit = "ein" if n % 10 == 1 else _DE_SMALL[n % 10]
        return f"{unit} und {_DE_TENS[n // 10]}"
    if n < 1000:
        prefix = "ein" if n // 100 == 1 else _DE_SMALL[n // 100]
        return f"{prefix} hundert" + (" " + _de_spaced(n % 100) if n % 100 else "")
    prefix = "ein" if n // 1000 == 1 else _de_spaced(n // 1000)
    return f"{prefix} tausend" + (" " + _de_spaced(n % 1000) if n % 1000 else "")


_FR_SMALL = [
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
]
_FR_TENS = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}


def _fr_under_100(n: int) -> str:
    if n <= 16:
        return _FR_SMALL[n]
    if n < 20:
        return "dix-" + _FR_SMALL[n - 10]
    if n < 70:
        ten = (n // 10) * 10
        rest = n % 10
        return _FR_TENS[ten] + (" et un" if rest == 1 else "-" + _FR_SMALL[rest] if rest else "")
    if n < 80:
        rest = n - 60
        return "soixante et onze" if rest == 11 else "soixante-" + _fr_under_100(rest)
    rest = n - 80
    if rest == 0:
        return "quatre-vingts"
    return "quatre-vingt-" + _fr_under_100(rest)


def _fr(n: int) -> str:
    if n < 100:
        return _fr_under_100(n)
    if n < 1000:
        hundreds = n // 100
        rest = n % 100
        prefix = "cent" if hundreds == 1 else _FR_SMALL[hundreds] + " cent"
        if not rest and hundreds > 1:
            prefix += "s"
        return prefix + (" " + _fr_under_100(rest) if rest else "")
    thousands = n // 1000
    rest = n % 1000
    prefix = "mille" if thousands == 1 else _fr(thousands) + " mille"
    return prefix + (" " + _fr(rest) if rest else "")


_IT_SMALL = [
    "zero", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove",
    "dieci", "undici", "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove",
]
_IT_TENS = ["", "", "venti", "trenta", "quaranta", "cinquanta", "sessanta", "settanta", "ottanta", "novanta"]


def _it_under_100(n: int) -> str:
    if n < 20:
        return _IT_SMALL[n]
    base = _IT_TENS[n // 10]
    rest = n % 10
    if rest in {1, 8}:
        base = base[:-1]
    return base + (_IT_SMALL[rest] if rest else "")


def _it(n: int) -> str:
    if n < 100:
        return _it_under_100(n)
    if n < 1000:
        hundreds = n // 100
        rest = n % 100
        prefix = "cento" if hundreds == 1 else _IT_SMALL[hundreds] + "cento"
        if 80 <= rest < 90:
            prefix = prefix[:-1]
        return prefix + (_it_under_100(rest) if rest else "")
    thousands = n // 1000
    rest = n % 1000
    prefix = "mille" if thousands == 1 else _it(thousands) + "mila"
    return prefix + (_it(rest) if rest else "")


_ES_SMALL = [
    "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
    "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve",
]
_ES_TENS = ["", "", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
_ES_HUNDREDS = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _es_under_100(n: int) -> str:
    if n < 30:
        return _ES_SMALL[n]
    return _ES_TENS[n // 10] + (" y " + _ES_SMALL[n % 10] if n % 10 else "")


def _es(n: int) -> str:
    if n < 100:
        return _es_under_100(n)
    if n < 1000:
        if n == 100:
            return "cien"
        return _ES_HUNDREDS[n // 100] + (" " + _es_under_100(n % 100) if n % 100 else "")
    thousands = n // 1000
    rest = n % 1000
    prefix = "mil" if thousands == 1 else _es(thousands) + " mil"
    return prefix + (" " + _es(rest) if rest else "")


def _normal_tokens(phrase: str) -> tuple[str, ...]:
    return tuple(part for part in re.split(r"[\s\-]+", phrase.casefold().strip()) if part)


@lru_cache(maxsize=None)
def _phrase_map(language: str) -> dict[tuple[str, ...], int]:
    generator = {"en": _en, "de": _de, "fr": _fr, "it": _it, "es": _es}.get(language)
    if generator is None:
        return {}
    result: dict[tuple[str, ...], int] = {}
    for number in range(10_000):
        phrases = [generator(number)]
        if language == "en" and number >= 100:
            phrases.append(_en(number, use_and=True))
        if language == "de":
            phrases.append(_de_spaced(number))
        for phrase in phrases:
            result[_normal_tokens(phrase)] = number
    # Common ASR variants.
    if language == "de":
        result[("ein",)] = 1
    return result


_SIMPLE_WORDS: dict[str, dict[str, int]] = {
    "tr": {"sıfır":0,"bir":1,"iki":2,"üç":3,"dört":4,"beş":5,"altı":6,"yedi":7,"sekiz":8,"dokuz":9,"on":10},
    "pt": {"zero":0,"um":1,"dois":2,"três":3,"quatro":4,"cinco":5,"seis":6,"sete":7,"oito":8,"nove":9,"dez":10},
    "nl": {"nul":0,"een":1,"twee":2,"drie":3,"vier":4,"vijf":5,"zes":6,"zeven":7,"acht":8,"negen":9,"tien":10},
    "pl": {"zero":0,"jeden":1,"dwa":2,"trzy":3,"cztery":4,"pięć":5,"sześć":6,"siedem":7,"osiem":8,"dziewięć":9,"dziesięć":10},
    "ru": {"ноль":0,"один":1,"два":2,"три":3,"четыре":4,"пять":5,"шесть":6,"семь":7,"восемь":8,"девять":9,"десять":10},
    "ar": {"صفر":0,"واحد":1,"اثنان":2,"اثنين":2,"ثلاثة":3,"أربعة":4,"خمسة":5,"ستة":6,"سبعة":7,"ثمانية":8,"تسعة":9,"عشرة":10},
    "ja": {"ゼロ":0,"零":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10},
    "ko": {"영":0,"공":0,"하나":1,"둘":2,"셋":3,"넷":4,"다섯":5,"여섯":6,"일곱":7,"여덟":8,"아홉":9,"열":10},
}


def _normalize_simple_words(text: str, language: str) -> str:
    words = _SIMPLE_WORDS.get(language, {})
    result = text
    for spoken, value in sorted(words.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(
            rf"(?<!\w){re.escape(spoken)}(?!\w)",
            str(value),
            result,
            flags=re.IGNORECASE,
        )
    return result

_WORD_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
_CHINESE_NUMERAL = re.compile(r"[零〇一二两三四五六七八九十百千万亿]+")


def _parse_chinese(value: str) -> int | None:
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    small_units = {"十": 10, "百": 100, "千": 1000}
    large_units = {"万": 10_000, "亿": 100_000_000}
    if value and all(char in digits for char in value):
        return int("".join(str(digits[char]) for char in value))
    total = section = number = 0
    seen = False
    for char in value:
        if char in digits:
            number = digits[char]
            seen = True
        elif char in small_units:
            unit = small_units[char]
            section += (number or 1) * unit
            number = 0
            seen = True
        elif char in large_units:
            section += number
            total += (section or 1) * large_units[char]
            section = number = 0
            seen = True
        else:
            return None
    return total + section + number if seen else None


def normalize_spoken_numbers(text: str, language: str) -> str:
    """Replace safely recognized spoken integer phrases with decimal digits.

    The primary UI languages support 0..9999. Chinese unit expressions also
    support 万 and 亿. Ambiguous French article ``un`` is not converted when it
    appears alone.
    """
    source = str(text)
    if language == "zh":
        return _CHINESE_NUMERAL.sub(lambda match: str(_parse_chinese(match.group(0))) if _parse_chinese(match.group(0)) is not None else match.group(0), source)
    phrases = _phrase_map(language)
    if not phrases:
        return _normalize_simple_words(source, language)

    virtual: list[tuple[str, int, int]] = []
    for match in _WORD_TOKEN.finditer(source):
        parts = _normal_tokens(match.group(0))
        for part in parts:
            virtual.append((part, match.start(), match.end()))
    if not virtual:
        return source

    max_parts = max((len(key) for key in phrases), default=1)
    replacements: list[tuple[int, int, str]] = []
    index = 0
    while index < len(virtual):
        found: tuple[int, int] | None = None
        upper = min(max_parts, len(virtual) - index)
        for length in range(upper, 0, -1):
            key = tuple(item[0] for item in virtual[index:index + length])
            value = phrases.get(key)
            if value is None:
                continue
            # Avoid changing the common French indefinite article in isolation.
            if language == "fr" and key == ("un",):
                continue
            start = virtual[index][1]
            end = virtual[index + length - 1][2]
            found = (length, value)
            replacements.append((start, end, str(value)))
            break
        index += found[0] if found else 1

    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source
