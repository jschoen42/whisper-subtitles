# .venv/Scripts/activate
# python src/_test_prefs.py

import sys

from utils.prefs import Prefs
from utils.trace import Trace

def main() -> None:
    Prefs.init("settings")
    Prefs.load("base.yaml")
    Prefs.load("projects.yaml")

    spacy = Prefs.get("spacy")
    Trace.info( f"spacy: {spacy}" )

    model_path = Prefs.get("spacy.model_path")
    Trace.info( f"spacy model path: {model_path}" )

    spacy = Prefs.get("spacy.model_name.de")
    Trace.info( f"spacy model: {spacy}" )

    # projects = Prefs.get("projects")
    # Trace.info( f"projects: {projects}" )

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    main()
