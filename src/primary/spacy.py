"""
    © Jürgen Schoenemeyer, 22.02.2025

    PUBLIC:
     - init_spacy(language: str) -> None
     - get_modelname_spacy(language: str) -> str
     - analyse_sentences_spacy(text: str, language: str = "de-DE") -> Tuple[List, List]:
"""
from __future__ import annotations

import re
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Any, Dict, List, Tuple

import spacy

from utils.decorator import duration
from utils.globals import BASE_PATH
from utils.prefs import Prefs
from utils.trace import Trace

# https://spacy.io/models/de

nlp: Any = None

spacy_version = "spacy_" + "".join(version("spacy").split(".")[:-1])
if spacy_version == "spacy_38":
    warnings.simplefilter("ignore", FutureWarning)

spacy_version = "spacy_37" # force to 3.7 models -> seems better than the 3.8 convert

if spacy_version == "spacy_37":
    warnings.simplefilter("ignore", UserWarning)

###########################################################################
#
# spaCy - init
#
###########################################################################

@duration("spacy - loading model")
def init_spacy(language: str) -> None:
    global nlp

    model_path = BASE_PATH / Prefs.get("spacy." + spacy_version + ".model_base")
    model_name = get_modelname_spacy(language)

    try:
        nlp = spacy.load(Path(model_path, model_name) )
    except OSError as error:
        Trace.fatal(f"spacy model '{model_name}' not loaded {error}")

    Trace.info(f"spaCy model '{model_name}'")

def get_modelname_spacy(language: str) -> str:
    model_name = Prefs.get("spacy." + spacy_version + ".model_name.de")

    if language.split("-")[0] == "en":
        model_name = Prefs.get("spacy." + spacy_version + ".model_name.en")

    return str(model_name)

###########################################################################
#
# spaCy - analyse text -> sentences
#
###########################################################################

def split_sentences(text: str) -> List[Tuple[str, str]]:
    doc = nlp(text)
    result: List[Tuple[str, str]] = []
    main_clause = ""

    for token in doc:
        Trace.info(f"{token.text =} {token.pos_ =} {token.dep_ =}")

        if token.pos_ == "SCONJ" or token.dep_ == "mark":
            if main_clause:
                result.append((main_clause.strip(), "main"))
                main_clause = ""
            result.append((token.head.text_with_ws + " ".join([t.text_with_ws for t in token.head.subtree]), "sub"))
        elif token.dep_ in ("cc", "punct") and token.head.dep_ == "ROOT":
            if main_clause:
                result.append((main_clause.strip(), "main"))
                main_clause = ""
            main_clause = token.head.text_with_ws + " ".join([t.text_with_ws for t in token.head.subtree])
        else:
            main_clause += token.text_with_ws

    if main_clause:
        result.append((main_clause.strip(), "main"))

    return result

@duration("spacy - analyse sentences")
def analyse_sentences_spacy(text: str, language: str = "de-DE") -> Tuple[List[int], List[int]]:
    # global nlp

    if text == "":
        Trace.error("text is empty")
        return [], []

    if not nlp:
        init_spacy(language)

    info_tokens    = []
    sentence_start = []
    sentence_end   = []

    tokens = nlp(re.sub('[″‟“”„»«"]', "'", text)) # normalize QUOTES

    # inconsistent behavior at the beginning of a text
    #
    # OSR_2409_KB_Kap_01_00:
    # 0 =>          => sent_start:  1, sent_end:  0
    # 1 => Guten    => sent_start:  0, sent_end:  0
    #
    # OSR_2409_KB_Kap_01_01:
    # 0 =>          => sent_start:  1, sent_end:  1
    # 1 => Beginnen => sent_start:  1, sent_end:  0

    min_idx = 0
    if text[0] == " ":
        min_idx = 1

    for _i, token in enumerate(tokens):
        token_info = {
            "idx":      token.idx,
            "text":     token.text,

            "lemma":    token.lemma_,  # Base form of the token
            "shape":    token.shape_,  # . , § d dd x xx xxx xxxx Xx Xxx Xxxx Xxxxx Xxxxx-Xxxxx => d = decimal, x = lowercase, X = uppercase

            "is_start": token.is_sent_start,
            "is_end":   token.is_sent_end,

            "type":     token.pos_,    # https://universaldependencies.org/u/pos/
            "tag":      token.tag_,    # https://gist.github.com/nlothian/9240750
        }

        info_tokens.append(token_info)

        if token.is_sent_start != token.is_sent_end:

            if token.is_sent_start:
                sentence_start.append(max(min_idx, token.idx)) # word starts with a visible char (not with a space)

            if token.is_sent_end:
                sentence_end.append(token.idx + len(token.text) )

        # shape_: {token.shape_:12} lemma_: {token.lemma_:25} pos_: {token.pos_:5}

        # Trace.debug(f"{token.idx:4} => {token.text:25} => sent_start: {token.is_sent_start: 1}, sent_end: {token.is_sent_end: 1}" )

    Trace.result(f"result: {len(sentence_end)} sentences")

    return sentence_start, sentence_end


###########################################################################
#
# only for testing spaCy
#
###########################################################################

# https://spacy.io/api/token#section-attributes

#                  de_dep_news_trf // de_core_news_sm
# pos_
# Holzfurnier:     PROPN //           ADJ
# zusammengefasst: VERB //            ADV
# um:              ADP //             SCONJ
# Soviel:          PRON //            DET
# die:             DET //             PRON
# nutzen:          VERB //            NOUN

# token.shape --> '.', ',', 'xx', 'xxx', 'xxxx', 'Xx', 'Xxx', 'Xxxx', 'Xxxxx', 'Xxxxx-Xxxxx', '§', 'd', 'dd'


def analyse_noun_nlp(text: str, language: str = "de-DE") -> Dict[str, Any]:
    # global nlp

    if not nlp:
        init_spacy(language)

    tokens = nlp(text)

    warn_list = {}
    warn_list_details = []

    for token in tokens:
        if token.pos_ == "NOUN":  # token.tag_ == "NN"
            if token.text[0].islower():
                warn_list_details.append({
                    "idx": token.idx,
                    "text": token.text,
                    "lemma": token.lemma_,
                    "tag": token.tag_,
                })

                if token.text not in warn_list:
                    warn_list[token.text] = {
                        "lemma": token.lemma_,
                        "count": 1,
                    }
                else:
                    warn_list[token.text]["count"] += 1

    if len(warn_list_details) > 0:
        Trace.warning(f"check spelling noun: {warn_list_details}")

    return warn_list


def analyse_nlp(_string_id: str, text: str, language: str = "de-DE") -> List[Dict[str, Any]]:
    # global nlp

    if not nlp:
        init_spacy(language)

    tokens = nlp(text)

    info_tokens = []
    warn_list = []
    for token in tokens:
        token_info = {
            "idx":      token.idx,
            "text":     token.text,
            "type":     token.pos_,
            "tag":      token.tag_,
            "lemma":    token.lemma_,
            "shape":    token.shape_,
            "is_start": token.is_sent_start,
            "is_end":   token.is_sent_end,
        }
        info_tokens.append(token_info)

        if token.pos_ == "NOUN":  # token.tag_ == "NN"
            if token.text[0].islower():
                warn_list.append({
                    "idx":   token.idx,
                    "text":  token.text,
                    "lemma": token.lemma_,
                    "tag":   token.tag_,
                })

    # print(info_tokens)

    # if len(warn_list)>0:
    #    Trace.error(f"{string_id} - check spelling noun: {warn_list}")

    for tokeninfo in info_tokens:
        Trace.info(f"{tokeninfo}")

    return info_tokens
