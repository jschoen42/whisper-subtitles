# .venv\Scripts\activate
# python _test_load_spacy.py

import time
from typing import Any
from pathlib import Path
import spacy

from src.utils.prefs import Prefs
from src.utils.trace import Trace

model_doc: Any = None

def get_modelname_nlp(language: str) -> str:
    model_name = Prefs.get("spacy.model_name.de")

    if language.split("-")[0] == "en":
        model_name = Prefs.get("spacy.model_name.en")

    return model_name

def test_load_spacy(language) -> None:
    global model_doc

    Prefs.init("./_prefs")
    Prefs.read("base.yaml")

    model_path = Prefs.get("spacy.model_path")
    model_name = get_modelname_nlp(language)

    start_time = time.time()
    try:
        model_doc  = spacy.load( Path(model_path, model_name) )
        duration   = time.time() - start_time
        Trace.result(f"'{model_name}' loaded: {duration:.2f} sec")
    except OSError as error:
        Trace.fatal(f"'{model_name}' not loaded {error}")

def main():
    test_load_spacy("de-DE")
    #test_load_spacy("en-US")

if __name__ == "__main__":
    main()
