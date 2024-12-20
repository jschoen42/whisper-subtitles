# .venv\Scripts\activate
# python _test_prefs.py

import sys

from src.utils.prefs import Prefs
from src.utils.trace import Trace

def main():
    Prefs.init("_prefs")
    Prefs.read("base.yaml")
    Prefs.read("projects.yaml")

    spacy = Prefs.get("spacy")
    Trace.info( f"spacy: {spacy}" )

    model_path = Prefs.get("spacy.model_path")
    Trace.info( f"spacy model path: {model_path}" )

    spacy = Prefs.get("spacy.model_name.de")
    Trace.info( f"spacy model: {spacy}" )

    # projects = Prefs.get("projects")
    # Trace.info( f"projects: {projects}" )

if __name__ == "__main__":
    Trace.action(f"Python version {sys.version}")

    main()
