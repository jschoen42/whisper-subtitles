# video subtitles with Faster-Whisper ...

used packages

```console
  SpeechToText faster-whisper (1.1.1 optimized)
  SpeechToText whisper (only for tests)
  SpeechToText whisper timestamp (only for tests)

  NLP spaCy (3.8.4)

  Hunspell (-> Firefox/LibreOffice/...) to check spelling: spylls (hunspell in pure python)
   - with >>2000 new german entries
   - german rules from 2017
   - de-DE.dic: refactor
   - de-DE.aff: add new rules (-> Plural Umlaute)
   - toDo: adapt to Rechtschreibreform 2024
```

```console
  https://github.com/SYSTRAN/faster-whisper
  https://github.com/openai/whisper
  https://github.com/linto-ai/whisper-timestamped
  https://github.com/explosion/spaCy
```

supported models for 'faster-whisper' (SpeechToText)

```console

  # multi language models

  Systran--faster-whisper-tiny
  Systran--faster-whisper-base
  Systran--faster-whisper-small
  Systran--faster-whisper-medium
  Systran--faster-whisper-large-v1
  Systran--faster-whisper-large-v2            # best model for german
  Systran--faster-whisper-large-v3            # to many errors

  deepdml--faster-whisper-large-v3-turbo      # best v3 model, but the 'old' v2 has fewer errors
  Primeline--faster-whisper-large-v3-turbo-de # almost all 'ß' are converted to 'ss'

  bofenghuang--faster-whisper-large-v2-de     # problem with numbers: 2024 -> zwanzig vierundzwanzig
  nyrahealth--faster-CrisperWhisper-v3        # problem with numbers: §17 -> Paragraph siebzehn
  Primeliner--faster-whsiper-large-v3-de      # only < 30 sec, if inner prompting is active

  # single language models "en"

  Systran--faster-distil-whisper-large-v2
  Systran--faster-distil-whisper-large-v3
```

supported models for 'whisper', 'whisper timestamped' (SpeechToText)

```console

  openAI tiny
  openAI small
  openAI base
  openAI medium
  openAI large-v1
  openAI large-v2
  openAI large-v3
  openAI large-v3-turbo
```

models for 'spaCy' (Sentence detection)

```console
  de_dep_news_trf-3.7.2
  de_core_news_lg-3.7.2
  en_core_web_lg-3.7.2

  the new models 3.8.0 are worse than 3.7.2
```

```console
  path to project settings
    ./_prefs/base.yaml
    ./_prefs/projects.yaml
    ./_prefs/projects_all.yaml

  path to models (not included in the repo):
    ../models/faster-whisper/
    ../models/whisper/
    ../models/spacy/

  path to data (not included in the repo):
    ../data/

  e.g. 'Kurzbeitrag September 2024'
    ../data/Kurzbeitrag/OSR_2409_KB/OSR_2409_KB.xlsx
    ../data/Kurzbeitrag/OSR_2409_KB/02_video/
    ../data/Kurzbeitrag/OSR_2409_KB/03_audio/
      ...
    ../data/Kurzbeitrag/OSR_2409_KB/09_srt/
  ```
