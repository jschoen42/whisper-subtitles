"""
    (c) Jürgen Schoenemeyer, 10.11.2024

    PUBLIC:
    check_quote(test_id: str, text: None | str, language: str) -> str
"""
from src.utils.trace import Trace

quote_info = {
    # unten99, oben66
    "de": [chr(8222), chr(8220)], # deutsch
    "cz": [chr(8222), chr(8220)], # tschechisch
    "bg": [chr(8222), chr(8220)], # bulgarisch
    "sk": [chr(8222), chr(8220)], # slowakisch
    "lv": [chr(8222), chr(8220)], # lettisch
    "li": [chr(8222), chr(8220)], # litauisch
    "dk": [chr(8222), chr(8220)], # dänisch

    # unten99, oben99
    "pl": [chr(8222), chr(8221)], # polnisch
    "hu": [chr(8222), chr(8221)], # ungarisch
    "et": [chr(8222), chr(8221)], # estnisch
    "hr": [chr(8222), chr(8221)], # kroatisch
    "ro": [chr(8222), chr(8221)], # rumänisch
    "sr": [chr(8222), chr(8220)], # serbisch

    # oben66, oben99
    "en": [chr(8220), chr(8221)], # englisch
    "tr": [chr(8220), chr(8221)], # türkisch
    "nl": [chr(8220), chr(8221)], # niederlänisch
    "zh": [chr(8220), chr(8221)], # chinesisch
    "ko": [chr(8220), chr(8221)], # koreanisch
    "it": [chr(8220), chr(8221)], # italienisch (ggf. auch « »)
    "es": [chr(8220), chr(8221)], # spanisch (ggf. auch « »)
    "ru": [chr(8220), chr(8221)], # russisch (ggf. auch « »)
    "el": [chr(8220), chr(8221)], # griechisch (ggf. auch « »)
    "pt": [chr(8220), chr(8221)], # portugiesisch (Portugal) (ggf. auch « »)
    "pt-BR": [chr(8220), chr(8221)], # brasilianisch

    # oben99, oben99
    "fi": [chr(8221), chr(8221)], # finnisch
    "sv": [chr(8221), chr(8221)], # schwedisch
    "id": [chr(8221), chr(8221)], # indonesisch

    # << >>
    "gr": [chr(171), chr(187)],   # griechisch
    "no": [chr(171), chr(187)],   # norwegisch

    # >> <<
    "sl": [chr(187), chr(171)],   # slovenisch

    # << >> inkl. nbsp
    "fr": [chr(171)+chr(160), chr(160)+chr(187)], # französisch

    # Ecke links oben, Ecke rechts unten
    "ja": [chr(12300), chr(12301)] # japanisch

    # keine typographischen Anführungszeichen
    # "ms": [chr(34), chr(34)], # malayisch
    # "vi": [chr(34), chr(34)]  # vietnamesisch
}

def check_quote(test_id: str, text: None | str, language: str) -> str:
    if text is None:
        return ""

    if language in ["vi", "ms"]: # keine typographischen Anführungszeichen
        return text

    text = text.strip()

    if text == "" or text.find('"')==-1:
        return text

    if language not in quote_info:
        Trace.error( f"check_quote - unknown language: {language}")
        language = "en"

    out_text = text
    i=0
    while True:
        pos = out_text.find('"')
        if pos==-1:
            break

        out_text = out_text[:pos] + quote_info[language][i] + out_text[pos+1:]
        i = (i+1)%2

    if i==1:
        Trace.error( f"check_quote: not even error ({language}) {test_id}: {text}")

    return out_text
