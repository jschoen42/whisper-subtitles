# .venv\Scripts\activate
# python _test_stanza.py

import sys
# import re
import warnings

# https://github.com/stanfordnlp/stanza/issues
# https://stanfordnlp.github.io/stanza/tokenize.html#tokenization-and-sentence-segmentation

import stanza

# from src.utils.prefs import Prefs
from src.utils.trace     import Trace
from src.utils.decorator import duration


text = " Beginnen wir mit einer Entscheidung des Bundesarbeitsgerichts vom 23. Mai 2024. Ist ein Unternehmen gezwungen, innerhalb eines kurzen Zeitraums mehrere Mitarbeiter zu kündigen, dann ist er verpflichtet, ab einer bestimmten Anzahl von zu kündigenden Mitarbeitern bei der Agentur für Arbeit eine sogenannte Massenentlassungsanzeige nach § 17 Kündigungsschutzgesetz zu erstatten."

text = " Beginnen wir mit einer Entscheidung des Bundesarbeitsgerichts vom 23.\xa0Mai 2024. Das ist ein weitere Satz am 20.20.2024." # \xa0 hilft nicht

warnings.simplefilter("ignore", FutureWarning)

MODEL_PATH = "../models/stanza"

@duration("Stanza: loading")
def init_stanza(language: str):
    Trace.info(f"loading stanza '{language}'")
    return stanza.Pipeline(lang=language, verbose=False, dir=MODEL_PATH, download_method=None, use_gpu=False)

@duration("Stanza: analyse")
def analyse( nlp, text ):
    return nlp(text)

def main():
    # Prefs.init("./_prefs")
    # Prefs.read("base.yaml")

    # stanza.download("en")
    # nlp = init_stanza("en")
    # doc = analyse( nlp, "Barack Obama was in Hawaii.  He was elected president in 2008.")

    # stanza.download("de")
    nlp = init_stanza("de")
    doc = analyse( nlp, text )

    for i, sentence in enumerate(doc.sentences):
        print(f"====== Sentence {i+1} tokens =======")
        print(*[f"id: {token.id}\ttext: {token.text}" for token in sentence.tokens], sep="\n")


    # doc.sentences[2].print_dependencies()


if __name__ == "__main__":
    # Trace.set( debug_mode=True, show_timestamp=False )
    Trace.action(f"Python version {sys.version}")

    main()