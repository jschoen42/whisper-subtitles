"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - prepare_words(data: dict, is_faster_whisper: bool, is_intro: bool, model_name: str, language: str, cache_md5: dict, media_filename: str) -> Tuple[list, int, float, float, str, list, list]:
     - split_to_lines(words: list, dictionary: list) -> Tuple[dict, str, str, dict, dict, list]:
     - split_to_sentences(words: dict, dictionary: dict) -> list:

     - get_filename_parameter(params: dict) -> str:
     - are_prompts_allowed(model_name) -> bool:
     - are_inner_prompts_possible(model_name) -> bool:
     - prompt_main_normalize(text: str) -> str:
     - prompt_normalize(text: str) -> str:
     - format_euro(text: str, thousand_separator: str = ".", float_separator: str = ",", euro: str = "€") -> str:

"""

import re
import hashlib

import numpy
from typing import Tuple

from main.spacy import analyse_sentences_spacy

from utils.trace import Trace
from utils.prefs import Prefs
from utils.util  import format_timestamp, CacheJSON
from helper.spelling import spellcheck

#################################################################################################################
#
#   def allow_inner_prompts(model_name) -> bool: # -> condition_on_previous_text
#   def are_inner_prompts_allowed(model_name) -> bool: # -> check repetitions
#
#   prompt_main_normalize(text: str) -> str:
#   prompt_normalize(text: str) -> str:
#
#   format_euro(text: str, thousand_separator: str = ".", float_separator: str = ",", euro: str = "€") -> str:
#
#   def get_filename_parameter(params: dict) -> str:
#
#   PASS 1
#   def prepare_words(data: dict[dict], is_faster_whisper: bool, is_intro: bool, type_v3: bool, language: str,
#                      cache_md5: dict, media_filename: str) -> Tuple[list[dict], int, float, float, str, list[dict]]:
#   PASS 2
#   def split_to_lines(words: list[dict], dictionary: list[list]) -> Tuple[dict, str, str, dict, dict, list]:
#
#   export in sentences -> TextToSpeech
#   def split_to_sentences(words: dict, dictionary: dict) -> list:
#
#################################################################################################################

def are_inner_prompts_possible(model_name) -> bool: # -> check repetitions
    return model_name not in Prefs.get("whisper.faster_whisper.models.no_condition_on_previous_text")

def are_prompts_allowed(model_name) -> bool: # ->
    return model_name != "large-v3-de"

SPLIT_DEBUG: bool = False

prompt_replace: dict = {
    '"': "'",
    "„": "»",
    "“": "«",

    "..": ".",
}

#
# Excel: line 2, row 'Prompt' (singlelLine text)
#

def prompt_main_normalize(text: str) -> str:
    lines = text.split("<br>")
    prompt = ""
    for i, line in enumerate(lines):
        if i == 0:
            prompt = line.strip()
        else:
            prompt += "; " + line.strip()

    for source, dest in prompt_replace.items():
        prompt = prompt.replace(source, dest)

    return prompt.replace("  ", " ")

#
# Excel: line 3 ... n, row 'prompt' (multiLine text)
#

def prompt_normalize(text: str) -> str:
    lines = text.split("<br>")

    prompt = ""
    for i, line in enumerate(lines):
        if i == 0:
            prompt = line.strip()
        else:
            prompt += re.sub(r"^[\d\.]+\s", "", line.strip())

        if prompt[-1] not in ".:,;!?…":
            prompt += ";"  # ; "," / "." macht Probleme beim ersten Satz im Video

        prompt += " "

    for source, dest in prompt_replace.items():
        prompt = prompt.replace(source, dest)

    return prompt.replace("{", '"').replace("}", '"').strip()

# https://pynative.com/python-find-position-of-regex-match-using-span-start-end/
#
# res = re.search(r'[\d,\.]+\s(Euro|€)', target_string)
# print(res.start())
# print(res.end())
#
# for match in re.finditer(r'[\d,\.]+\s(Euro|€)', target_string):
#
#  "12 Euro"    => "12 €"
#  "12,12 Euro" => "12,12 €"
#  "1234 €"     => "1.234 €"
#  "1234,56 €"  => "1.234,56 €"
#  "1234€"      => "1.234 €"
#  "520€"       => "520 €"

def format_euro(text: str, thousand_separator: str = ".", float_separator: str = ",", euro: str = "€") -> str:
    results = []

    text = text.replace("€", " €")

    for match in re.finditer(r"[\d,\.]+\s*(Euro|€)", text):
        number_str = match.group().split(" ")[0]

        if thousand_separator in number_str:
            result = number_str + " " + euro
        else:
            if "," in number_str:
                tmp = number_str.split(float_separator)
                n = tmp[0]
                m = tmp[1]
            else:
                n = number_str
                m = ""

            pre = ""
            for i, c in enumerate(reversed(n)):
                if i > 0 and i % 3 == 0:
                    pre = thousand_separator + pre
                pre = c + pre

            if m:
                result = pre + float_separator + m + " " + euro
            else:
                result = pre + " " + euro

        results.append({"start": match.start(), "end": match.end(), "result": result})

    if len(results) == 0:
        ret = text
    else:
        ret = ""
        pos = 0
        for entry in results:
            ret += text[pos:entry["start"]] + entry["result"]
            pos =  entry["end"]

        ret += text[pos:]

    # if text != ret:
    #    Trace.warning(f"[{text}] => [{ret}]")

    return ret

split_words: list = [
    " und",
    " oder",
    " sowie",
]

dont_split: list = [
    "-",         # xxx- und xxxyyy

    # und

    " Arbeitnehmer" # Arbeitnehmer und ANgestellten
    " Beratung",    # Beratung und Schulung
    " Lohn",        # Lohn und Gehalt
    " Löhne",       # Löhne und Gehälter
    " Löhnen",      # den Löhnen und Gehältern
    " Inlohn",      # In Lohn und Gehalt
    " Lohn-",       # Lohn- und Gehaltszahlung
    " hin",         # hin und wieder
    " Stein",       # Stein und Bein
    " schlicht",    # schlicht und ergreifend
    " einzig",      # einzig und alleine
    " Sinn",        # Sinn und Zweck"
    " Damen",       # Damen und Herren
    " Lieferungen", # Lieferungen und Leistungen
    " Soll",        # Soll und Haben
    " steuer-",     # steuer- und sozialversicherungsfrei
    " Steuer-",     # Steuer- und Beitragsfrei
    " G",           # G und V
    " SKR03",       # SKR03 und SKR04

    # oder

    " mehr",       # mehr oder weniger
    " einen",      # einen oder anderen Stelle
    " eine",       # eine oder andere # ???? 78960_V1_Kap_00
    " ein",        # ein oder anderen Blick
    " so",         # so oder so
]

dont_split_two: list = [
    " heißt,", # das heißt
    " heißt",
]

#
# https://github.com/openai/whisper/discussions/928
#
# Stille am Ende wird als Copyrighttext erkannt
#
# not used anymore -> last segment: no_speech_prob>0.9

silence_text: list = [
    " Mehr Informationen auf www.sas-medien.de",
    " Mehr Informationen auf www.bundestag.de",

    " Untertitel von Stephanie Geiges",

    " Untertitel der Amara.org-Community",
    " Untertitelung aufgrund der Amara.org-Community"

    " Untertitel im Auftrag des ZDF für funk, 2017",

    " Untertitel im Auftrag des ZDF, 2017",
    " Untertitel im Auftrag des ZDF, 2020",
    " Untertitel im Auftrag des ZDF, 2018",
    " Untertitel im Auftrag des ZDF, 2021",
    " Untertitelung im Auftrag des ZDF, 2021",

    " Untertitelung des ZDF, 2020",
    " Untertitelung. BR 2018",

    " Copyright WDR 2021",
    " Copyright WDR 2020",
    " Copyright WDR 2019",
    " SWR 2021",
    " SWR 2020",

    " Das ist das Problem.",

    " Vielen Dank für die Aufmerksamkeit, meine Damen und Herren, ich bedanke mich für die Aufmerksamkeit.",

    " Vielen Dank fürs Zuhören.",
    " Vielen Dank für's Zuschauen.",
    " Vielen Dank für's Zuschauen!",
    " Vielen Dank für die Aufmerksamkeit.",
    " Vielen Dank.",
    " ENDE",

    " Bis zum nächsten Mal.",
    " Danke schön.",
    " Gut.",
    " Amen.",
]

def get_filename_parameter(params: dict) -> str:
    engine      = params["whisper"]
    model_id    = params["modelNumber"]
    model_name  = params["modelName"]
    beam_size   = params["beam"]
    vad_used    = params["VAD"]
    no_prompt   = params["noPrompt"]

    condition_on_previous_text = params["innerPrompt"]


    model = model_id + " " + model_name

    # parameter

    # VAD on/off

    params = ""
    if engine == "faster-whisper":
        if vad_used:
            vad = "VAD on"
        else:
            vad = "VAD off"
        params = f"{vad}, "

    # condition_on_previous on/off

    if condition_on_previous_text:
        inner_prompt = "inner-prompt on"
    else:
        inner_prompt = "inner-prompt off"
    params += f"{inner_prompt}, "

    if no_prompt:
        params += "no-prompt, "

    params += f"beam-{beam_size}"

    return f"[{engine}] [{model}] ({params})"

######################
#   Pass 1
######################

def prepare_words(data: dict, is_faster_whisper: bool, is_intro: bool, model_name: str, language: str, cache_md5: CacheJSON, media_filename: str) -> Tuple[list, int, float, float, str, list, list]:
    words: list = []
    probability: list = []

    words_new: list = []

    segments = data["segments"]

    text = data["text"]
    text = text.replace(" – ", " , ")
    text = text.replace(" - ", " , ")

    if text == "":
        Trace.fatal( f"text empty {media_filename}" )

    curr_md5 = hashlib.md5(text.encode("utf-8")).hexdigest()

    cache = cache_md5.get(curr_md5)
    if cache and "start" in cache:
        sentence_start = cache["start"] # cache[0]
        sentence_end   = cache["end"]   # cache[1]
    else:
        sentence_start, sentence_end = analyse_sentences_spacy(text, language)

        cache_md5.add(curr_md5, {
            "media": media_filename,
            "start": sentence_start,
            "end"  : sentence_end,
        })

    last_segment_seek = 0
    last_segment_end  = 0
    last_segment_text = ""

    corrected = set()
    repetition_error = []
    pause_error: dict = {
        "introStart":  [],
        "normalStart": [],
        "innerPause":  [],
    }

    position = 0

    for s, segment in enumerate(segments):
        segment_text      = segment["text"]
        compression_ratio = segment["compression_ratio"]
        speech_prop       = segment["no_speech_prob"]
        duration          = segment["end"] - segment["start"]
        curr_words        = segment_text.split(" ")


        if speech_prop>0.9 and duration<2:
            Trace.error(f"*** suspicious text *** segment {s}/{len(segments)-1} - last: {s == len(segments)-1}, no_speech_prob: {speech_prop:.3f}, duration: {duration:.2f}, compressionRatio: {compression_ratio:.2f} '{segment_text}'")

        # types of hallucination in the last segment
        #  - errors in the model -> " Untertitel im Auftrag des ZDF für funk, 2017"
        #  - internal promt -> "Das Recht des Heimatstaates."

        # toDo: vorletztes Segment

        # OSR_2311_LuG_LODAS
        # OSR_2311_Lohn_Kap_02_00:     *** suspicious text *** segment 9/10  - last: False, no_speech_prob: 0.981, duration: 0.56, compressionRatio: 0.87 ' Vielen Dank.'
        # OSR_2311_Lohn_Kap_02_00:     last segment with 'silence text' removed ' Bis zum nächsten Mal.' (no_speech_prob: 0.9806162118911743, duration: 1.08)
        # OSR_2311_Lohn_Kap_02_02_neu: *** suspicious text *** segment 95/96 - last: False, no_speech_prob: 0.995, duration: 0.64, compressionRatio: 0.91 ' Vielen Dank für's Zuschauen.
        # OSR_2311_Lohn_Kap_02_02_neu: *** suspicious text *** segment 96/96 - last: True,  no_speech_prob: 0.995, duration: 0.14, compressionRatio: 0.91 ' Bis zum nächsten Mal.'

        silence_text_found = False

        # if len(segments) > 1 and s == len(segments)-2:
        #    if len(curr_words) > 1 and duration < 0.2:
        #        silence_text_found = True
        #        last_segment_text = "\n" + segment_text + f" [0] (duration: {duration:.2f} < 0.2, speechProp: {speech_prop:.3f}, compressionRatio: {compression_ratio:.2f})"

        if s == len(segments) - 1: # last segment
            if len(curr_words) > 1 and duration < 0.2:
                silence_text_found = True
                last_segment_text = segment_text + f" [1] (duration: {duration:.2f} < 0.2, speechProp: {speech_prop:.3f}, compressionRatio: {compression_ratio:.2f})"

            elif speech_prop > 0.98:
                silence_text_found = True
                last_segment_text = segment_text + f" [2] (duration: {duration:.2f}, speechProp: {speech_prop:.3f} > 0.98, compressionRatio: {compression_ratio:.2f})"

            elif speech_prop > 0.9:
                if segment_text in silence_text:
                    silence_text_found = True
                    last_segment_text = segment_text  + f" [3] (duration: {duration:.2f}, speechProp: {speech_prop:.3f} > 0.9, compressionRatio: {compression_ratio:.2f}, silentText)"
                else:
                    Trace.warning(f"suspicious text in last segment: '{segment_text}', (duration: {duration:.2f}, no_speech_prob: {speech_prop} > 0.9, compressionRatio: {compression_ratio})")
                    last_segment_text = segment_text + f" (speech_prop: {speech_prop} - not removed)"


        if silence_text_found:
            Trace.warning(f"last segment with 'silence text' removed '{segment_text}' (no_speech_prob: {speech_prop}, duration: {duration:.2f})")
            continue

        segment_words  = segment["words"]
        # segment_length = len(segment_words)
        segment_id     = segment["id"]
        segment_seek   = segment["seek"]
        segment_start  = segment["start"]
        segment_pause  = round(segment_start - last_segment_end, 2)

        if segment_seek != last_segment_seek:
            if last_segment_end == 0:
                if is_intro:
                    if segment_start > last_segment_end + 13:
                        pause_error["introStart"].append([ 13, format_timestamp(last_segment_end), segment_pause])
                        Trace.warning(f"pause at intro slide start (>13 sec): {segment_start}")
                else:
                    if segment_start > last_segment_end + 2:
                        pause_error["normalStart"].append([ 2, format_timestamp(last_segment_end), segment_pause])
                        Trace.warning(f"pause at normal slide start (>2 sec): {segment_start}")
            else:
                if segment_start > last_segment_end + 5:
                    pause_error["innerPause"].append([ 5, format_timestamp(last_segment_end) + " -> " + format_timestamp(segment_start), segment_pause ])
                    Trace.warning(f"pause inside slide (>5 sec): {segment_start}, Pause: {segment_pause}")

            last_segment_seek = segment_seek

        last_segment_end = segment["end"]

        if is_faster_whisper:
            segment_id -= 1

        for i, word_info_original in enumerate(segment_words):

            word_info = {
                "word":           "",

                #"position-12:    0,
                #"position-2":    0,

                "sentence_start": 0,
                "sentence_end":   0,

                "segment_start":  (i==0),
                "segment_end":    (i==len(segment_words)-1),

                "start":          0,
                "end":            0,
                "duration":       0,
                "pause":          0,

                "probability":    0,
            }

            curr_word = ""
            if is_faster_whisper:
                curr_word                   = word_info_original[2]
                word_info["start"]         = round(word_info_original[0], 2)
                word_info["end"]           = round(word_info_original[1], 2)
                word_info["duration"]      = round(word_info_original[1] - word_info_original[0], 2)
                word_info["pause"]         = -1
                word_info["probability"]   = round(word_info_original[3], 3)
            else:
                word_info["start"]         = round(word_info_original["start"], 2)
                word_info["end"]           = round(word_info_original["end"], 2)
                word_info["duration"]      = round(word_info_original["end"] - word_info_original["start"], 2)
                word_info["pause"]         = -1
                if "word" in word_info_original:
                    # whisper

                    curr_word                = word_info_original["word"]
                    word_info["probability"] = round(word_info_original["probability"], 3)
                elif "text" in word_info_original:
                    # whisper timestamped

                    if word_info_original["text"] == "[*]":
                        continue
                    else:
                        curr_word                = " " + word_info_original["text"]
                        word_info["probability"] = round(word_info_original["confidence"], 3)

            word_info["word"] = re.sub('[″‟“”„»«"]', "'", curr_word)

            if curr_word[0] == " ":
                word_info["sentence_start"] = position+1 in sentence_start
            else:
                word_info["sentence_start"] = position in sentence_start

            position += len(curr_word)
            word_info["sentence_end"] = position in sentence_end

            words.append(word_info)
            probability.append(word_info["probability"])

            if len(words_new)>1 and word_info["word"].lower() == words_new[-1]["word"].lower(): # [1:] [1:]
                error_segment = f"{segment_id} / {(i + 1)}"
                error_text    = f"'{words_new[-1]['word']}' / '{word_info['word']}'"

                repetition_error.append({
                    "model":   model_name,
                    "type":    "single",
                    "segment": error_segment,
                    "text":    error_text,
                })

                if are_inner_prompts_possible(model_name):
                    Trace.warning(f"{model_name}: possible single word repetition {error_text} (segment {error_segment})")
                else:
                    # toDo "sehr sehr schnell" (Eigenorganisation compact & classic 4.1)
                    #words_new[-1]["end"]  = word_info["end"]
                    #words_new[-1]["duration"] = round(words_new[-1]["end"] - words_new[-1]["start"], 2)
                    Trace.error(f"{model_name}: single word repetition {error_text} (segment {error_segment}) not removed")
                    #continue

            # dual word repetition
            # LODAS Modul 3 Bauhauptgewerbe: 78945_V3_Kap_03_03: an dieser An dieser

            if len(words_new)>2 and word_info["word"].lower() == words_new[-2]["word"].lower() and words_new[-1]["word"].lower() == words_new[-3]["word"].lower():
                error_segment = f"{segment_id} / {i}-{i+1}"
                error_text    = f"'{words_new[-3]['word']}{words_new[-2]['word']}' / '{words_new[-1]['word']}{word_info['word']}'"

                repetition_error.append({
                    "model":   model_name,
                    "type":    "dual",
                    "segment": error_segment,
                    "text":    error_text,
                })

                if are_inner_prompts_possible(model_name):
                    Trace.warning(f"{model_name}: possible dual word repetition {error_text} (segment {error_segment})")
                else:
                    words_new[-2]["end"]  = word_info["end"]
                    words_new[-2]["duration"] = round(words_new[-2]["end"] - words_new[-2]["start"], 2)
                    Trace.error(f"{model_name}: dual word repetition {error_text} (segment {error_segment}) removed")
                    words_new.pop(-1)
                    continue

            words_new.append(word_info)

    for i, word in enumerate(words_new):
        curr_word = word["word"]
        curr_end  = word["end"]

        if i+1 < len(words_new):
            next_start = words_new[i+1]["start"]
            pause = next_start - curr_end
        else:
            pause = 1.0

        word["pause"] = round(pause, 2)

    average_probability = float(numpy.mean(probability))
    standard_deviation  = float(numpy.std(probability))

    if corrected:
        Trace.warning(f"corrected: {corrected}")

    return (
        words_new,
        len(sentence_start),
        average_probability,
        standard_deviation,
        last_segment_text,
        repetition_error,
        pause_error,
   )

####################################################
#
#   ...
#   {
#     "segmentID": 16,
#     "segmentLength": 16,
#     "count": 15,
#     "word": " erfolgt.",
#     "start": 152.17,
#     "end": 152.71,
#     "pause": 0.5,
#     "probability": 0.9331034819285074,
#     "position": "end",
#     "segment_start": false,
#     "segment_end": true
#   },
#   ...
#
#   "pause": 0.5 (sec behind the word - last word always 1.0 sec)
#   "position": "start" / "middle" / "end"
#   "pause": 0.0 / >0
#
#   special cases (last char of the word: '.')
#    - " bzw." => no break
#
#    - " 29.", " Februar", " 2024" => no break
#    - " ab", " 3.", " 2023" => no break
#    - " 01", ".12", ".2024" => no break
#
#    - und/oder => optional wrap if line is too long
#
#   special format "Euro" (only german format !!!)
#    - " 15" / ",10" / " Euro" => " 15,10 €"
#    - " 12345,67 Euro" -> "12.345,67 €"
#
####################################################

def split_to_lines(words: list, dictionary: list) -> Tuple[list, str, str, list, dict]:
    line  = ""
    lines = ""

    start = 0
    end   = 0
    count = 0

    corrected_details = {}

    captions = []
    section = 0

    def check_any_runctuation(word: str) -> bool:
        return word[-1] in ".:,;?!"

    def check_comma(word):
        return word[-1] in ","

    def predict(words: list, index: int, limit: int) -> bool:
        split = False
        for j in range(index + 1, len(words)):
            # print(j, words[j]["word"], "sentence_end", words[j]["sentence_end"])

            if words[j]["sentence_end"]:
                if j - index >= limit:
                    split = True
                else:
                    split = False
                break

        return split

    text = ""
    pre_word = ""
    for i, word_info in enumerate(words):
        segment_end = False                        # wg. Amazon
        if "segment_end" in word_info:
            segment_end = word_info["segment_end"]  # <- whisper
        sentence_end = word_info["sentence_end"]   # <- spaCy
        curr_word    = word_info["word"]
        curr_start   = word_info["start"]
        curr_end     = word_info["end"]
        next_pause   = word_info["pause"]

        if start == 0:
            start = curr_start

        split      = False # direct after this word ("hallo." / "hallo," )
        post_split = False # split before the word ("xyz und abc ..." => "xyz …" / "und abc ...")

        is_any_punctuation = check_any_runctuation(curr_word) # ".:,;?!"
        is_comma = check_comma(curr_word)                     # ","

        split_type = 0

        # Prio 1: spaCy Satzende

        if sentence_end:
            if next_pause > 0:
                split_type = 1
                split = True

            elif segment_end:
                split_type = 2
                split = True

        # Prio 2: whisper segment_ende

        if not split:
            if segment_end and curr_word not in dont_split_two:
                if is_any_punctuation and next_pause > 0.5:  # bisher 0.25
                    split_type = 3
                    split = True

                elif next_pause > 1.5:
                    split_type = 4
                    split = True

        # Prio 3: Kommata

        if not split:
            if is_comma:
                if count > 1:
                    split = predict(words, i, 3)
                    if split:
                        split_type = 5
                    elif next_pause > 0.5:
                        split = predict(words, i, 3)
                        if split:
                            split_type = 6


        # Prio 4 und/oder

        if not split:
            if count > 2:
                if curr_word in split_words and pre_word not in dont_split:
                    if next_pause > 1:
                        post_split = True
                        split_type = 7
                    else:
                        post_split = predict(words, i, 4) # ggf. split -> after "und", post_split -> before "und"
                        split_type = 8

        ###############

        if split or post_split:
            if split:
                count += 1
                line  += curr_word
                if SPLIT_DEBUG:
                    line += f" ({split_type})"
                end = curr_end

            if post_split:
                if SPLIT_DEBUG:
                    line += f" ({split_type})"

            line = format_euro(line)

            for w in dictionary:
                if w in line:
                    count = line.count(w)

                    line = line.replace(w, dictionary[w][0])
                    corr_text = f"[{w}] => [{dictionary[w][0]}]"

                    if corr_text in corrected_details:
                        corrected_details[corr_text]["count"] += count
                    else:
                        corrected_details[corr_text] = {
                            "count":     count,
                            "worksheet": dictionary[w][1],
                            "row":       dictionary[w][2]
                        }

            line = line.replace(" …", "").replace("  ", " ").replace("...", "…")  # .replace("..", ".") # usw..
            lines += line

            section += 1
            caption = {}
            caption["section"] = section
            caption["start"]   = start
            caption["end"]     = end
            caption["text"]    = line.lstrip()
            captions.append(caption)

            start_format = format_timestamp(start)
            end_format   = format_timestamp(end)

            text += f"[{start_format} -> {end_format}] {line.lstrip()}\n"

            if split:
                count = 0
                line  = ""
                start = 0
            else:
                count = 1
                line  = curr_word
                start = curr_start

        else:
            count += 1
            line += curr_word
            end = curr_end

        pre_word = curr_word

    if len(corrected_details) > 0:
        Trace.warning(f"corrected count: {corrected_details}")

    spelling_result = spellcheck(lines.strip().split(" "))

    return captions, text, lines.strip(), corrected_details, spelling_result


# export in sentences -> TextToSpeech

def split_to_sentences(words: dict, dictionary: dict) -> list:

    result = []
    text = ""
    start = 0

    last_pause = 0
    for i, word_info in enumerate(words):
        if word_info["sentence_start"]:
            text  = word_info["word"]
            start = word_info["start"]
        else:
            text += word_info["word"]

        next_start = 0
        if word_info["sentence_end"]:
            end  = word_info["end"]
            text = format_euro(text)

            for w in dictionary:
                if w in text:
                    text = text.replace(w, dictionary[w][0])

            # text = text.replace(" …", "").replace("  ", " ").replace("...", "…")

            pause = 0
            if i < len(words) - 1:
                next_start = words[i+1]["start"]
                pause = next_start - word_info["end"]

            result.append({
                "pause": last_pause,
                "start": start,
                "end":   end,
                "text":  text.strip(),
            })

            if pause > 0:
                last_pause = round(pause, 2)

                result.append({
                    "pause": -1,
                    "start": end,
                    "end":   next_start,
                    "text":  f"[pause: {last_pause} sec]",
                })
            else:
                last_pause = 0

    return result
