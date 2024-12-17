# .venv\Scripts\activate
# python _test_spelling.py

import sys

from src.utils.prefs import Prefs
from src.utils.trace import Trace

from src.helper.spelling import hunspell_dictionary_init, spellcheck

# https://manpages.ubuntu.com/manpages/focal/man5/hunspell.5.html

word_list = [
    "Schlüssel",
    "Gruppenschlüssel",
    "Beitragsgruppenschlüssel",
    "Personengruppenschlüssel",

    "Schlüsselung",
    "Gruppenschlüsselung",
    "Beitragsgruppenschlüsselung",
    "Personengruppenschlüsselung",

    "Gruppenschlüsselungen",
    "Beitragsgruppenschlüsselungen",
    "Personengruppenschlüsselungen",
]

# Regel "ung"
#
# Schlüssel/J
# Gruppenschlüssel/J
# Beitragsgruppenschlüssel/J
# Personengruppenschlüssel/J

word_list = [
    "erfasse",
    "erfassen",
    "erfassenden",
    "nacherfasse",
    "nacherfassen",
    "nacherfassenden",
    "nacherfassendes",
    "nacherfassendest",
    "nacherfasser",
]

word_list = [
    "mandantenbezog",
    "mandantenbezoge",
    "mandantenbezoger",
    "mandantenbezogem",
    "mandantenbezoges",
    "mandantenbezoger",

    "mandantenbezogen",
    "mandantenbezogenes"
]

word_list = [
    "15%ig",
    "15%ige",
    "15%iger",
    "15%iges",

    "35%igen"
]

word_list = [  # /ESTm
    "eAU-Abruf",
    "eAU-Abrufe",
    "ELStAM-Abruf",
    "ELStAM-Abrufe",
]

# Nummer/Nm
# Nummern/hij (deaktiviert !!!)
# KD-Nummer/Nm
# Kug-Nummer/Nm
# PLU-Nummer/Nm
# ZVK-Nummer/Nm
# kein RE-Nummer !!!!

# personalverantwortend/E falsch - > personalverantwortend/A

# Re -> deshalb "Re-Nummer" ok
# ä/n
# r/n

word_list = [
    "Nummer",
    "Nummern",    # auch ohne Eintrag "Nummer" gefunden -> Nummern/hij entfernt

    "XY-Nummer",  # korrekt fail
    "KD-Nummer",  # korrekt ok, weil Eintrag
    "Kd-Nummer",  # korrekt fail
    "KU-Nummer",  # korrekt fail

    "RE",
    "Re",
    "RE-Nummer",  # nicht korrekt ok  ################
    "Re-Nummer",  # nicht korrekt ok
    "re-Nummer",  # korrekt fail
    "rE-Nummer",  # korrekt fail

    "RG-Nummer",  # korrekt fail
]

_word_list = [
    "MT49",
]

# -> _hunspell/de-DE.aff
# -> _hunspell/InfoSyntax.xlsx

# Regel: 'p' Plural mit Umlauten

# [SFX / PFX] [rule] [a] [b] [c]
#
# if word ends with [c] then replace [a] with [b]
#
# SFX p   atz     ätze      atz # new 2024-11-03 (Satz -> Sätze)
# SFX p   atz     ätzen     atz # new 2024-11-03 (Satz -> Sätzen)
# SFX p   ab      äbe       ab  # new 2024-11-03 (Einstatzstab -> Einstatzstäbe)
# SFX p   ab      äben      ab  # new 2024-11-03 (Einstatzstab -> Einstatzstäben)
# SFX p   nal     näle      nal # new 2024-11-03 (Kanal -> Kanäle)
# SFX p   nal     nälen     nal # new 2024-11-03 (Kanal -> Kanälen)
# SFX p   lan     läne      lan # new 2024-11-03 (Ansparplan -> Ansparpläne)
# SFX p   lan     länen     lan # new 2024-11-03 (Ansparplan -> Ansparplänen)
# SFX p   aum     äume      aum # new 2024-11-03 (Raum -> Räume, Baum, Traum)
# SFX p   aum     äumen     aum # new 2024-11-03 (Raum -> Raumen)
# SFX p   und     ünde      und # new 2024-11-03 (Grund -> Gründe)
# SFX p   und     ünden     und # new 2024-11-03 (Grund -> Gründen)

# SFX p   arkt    ärkten    [mM]arkt | [mM] -> 'm' or 'M'
# SFX P   0       en         .       | 0    -> always
#

word_list = [

    # SFX p   ag      äge       ag
    # SFX p   ag      ägen      ag

    "Höchstbetrag",
    "Höchstbeträge",
    "Höchstbeträgen",

    # SFX p   atz     ätze      atz # new 2024-11-03 (Satz -> Sätze)
    # SFX p   atz     ätzen     atz # new 2024-11-03 (Satz -> Sätzen)

    "Nistplatz",
    "Nistplätze",
    "Umlagesatz",
    "Umlagesätze",
    "Blauhelmeinsatz",
    "Blauhelmeinsätze",
    "Kontoumsatz",
    "Kontoumsätze",

    # SFX p   ab      äbe       ab  # new 2024-11-03 (Einstatzstab -> Einstatzstäbe)
    # SFX p   ab      äben      ab  # new 2024-11-03 (Einstatzstab -> Einstatzstäben)

    "Äskulapstab",
    "Äskulapstäbe",
    "Einsatzstab",
    "Einsatzstäbe",

    # SFX p   nal     näle      nal # new 2024-11-03 (Kanal -> Kanäle)
    # SFX p   nal     nälen     nal # new 2024-11-03 (Kanal -> Kanälen)

    "Kanal",
    "Kanäle",
    "Fernsehkanal",
    "Fernsehkanäle",
    "Testkanal",
    "Testkanäle",

    # SFX p   lan     läne      lan # new 2024-11-03 (Ansparplan -> Ansparpläne)
    # SFX p   lan     länen     lan # new 2024-11-03 (Ansparplan -> Ansparplänen)

    "Plan",
    "Pläne",
    "Ansparplan",
    "Ansparpläne",
    "Fondssparplan",
    "Fondssparpläne",

    # SFX p   aum     äume      aum # new 2024-11-03 (Raum -> Räume, Baum, Traum)
    # SFX p   aum     äumen     aum # new 2024-11-03 (Raum -> Raumen)

    "Akazienbaum",
    "Akazienbäume",

    # SFX p   und     ünde      und # new 2024-11-03 (Grund -> Gründe)
    # SFX p   und     ünden     und # new 2024-11-03 (Grund -> Gründen)

    "Abgeltungsgrund",
    "Abgeltungsgründe",


    "Kontostand",
    "Kontostände",
]

# word_list = [
#     "Antarktisforscher",
#     "Antarktisforscherin",
#     "Schuldzinsenabzug",
#     "Schuldzinsenabzüge",
#     "Materialgemeinkostenzuschlag",
#     "Materialgemeinkostenzuschläge",
# ]

word_list = [
    "Beitragsgruppenschlüsselungen",
    "ZVK-Beitrag",
    "ZVK-Beitrags",
    "ZVK-Beiträge",
    "Werkstudierende",
    "Werkstudierenden",
    "Werkstudierender",
    "AOK", # wird vorher ausgefiltert !
    "AOKs",
    "SARS-CoV-2-Virus",
    "Altersvorsorgebeitrag",
    "Altersvorsorgebeiträge",
    "Geringverdienergrenze",
    "Empfänge",
]

def main():
    Prefs.init("./_prefs")
    Prefs.read("base.yaml")

    language   = Prefs.get("language")
    spelling   = Prefs.get("hunspell")

    hunspell_dictionary_init( spelling["path"], spelling["file"], language )

    spellcheck( word_list, debug=True )


if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")
    main()
