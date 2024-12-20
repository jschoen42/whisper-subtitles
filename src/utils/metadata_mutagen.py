"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - get_audioinfo_mutagen(filepath: str) -> dict:
     - get_audio_metadata_mutagen(filepath: Path | str) -> dict | None:
     - get_video_metadata_mutagen(filepath: Path | str) -> dict | None:
"""

from pathlib import Path

import mutagen.mp3
from mutagen import MutagenError

import mutagen.mp4
#from mutagen.mp3 import MP3, MPEGInfo
#from mutagen.mp4 import MP4
#from mutagen.wave import WAVE

from utils.trace import Trace
from utils.decorator import deprecation

###########################################
#  mutagen
#  https://pypi.org/project/mutagen/
###########################################

@deprecation("licence does not fit")
def get_audioinfo_mutagen(filepath: str) -> dict:
    metadata = mutagen.mp3.Open(filepath)

    duration = metadata.info.length
    if getattr(metadata.info, "mode", None) == 0:
        channels = 1
    else:
        channels = 2

    samples = 44100
    bits = int(channels * duration * samples * 2)
    sample_count = int(bits / 2)
    start_ptr = 106
    bytes = bits + start_ptr

    info = {
        "bytes":     bytes,
        "channels":  channels,
        "samples":   samples,
        "bits":      bits,
        "sampleCnt": sample_count,
        "startPt":   start_ptr
    }
    return info

@deprecation("licence does not fit")
def get_audio_metadata_mutagen(filepath: Path | str) -> dict | None:

    try:
        metadata = mutagen.mp3.Open(Path(filepath))
    except MutagenError as err:
        Trace.error(f"MutagenError: {err}")
        return None

    duration     = metadata.info.length
    channels     = getattr(metadata.info, "channels", None)
    mode         = ["STEREO", "JOINTSTEREO", "DUALCHANNEL", "MONO"][int(getattr(metadata.info, "mode", None))]
    bitrate_mode = str(getattr(metadata.info, "bitrate_mode", None)).split(".")[1]
    bitrate      = getattr(metadata.info, "bitrate", None)
    sample_rate  = getattr(metadata.info, "sample_rate", None)

    return {
        "duration":    round(duration, 2),
        "channels":    channels,
        "mode":        mode,
        "bitrateMode": bitrate_mode,
        "bitrate":     int(bitrate / 1000),
        "sampleRate":  sample_rate,
    }

@deprecation("licence does not fit")
def get_video_metadata_mutagen(filepath: Path | str) -> dict | None:
    try:
        metadata = mutagen.mp4.Open(Path(filepath))
    except MutagenError as err:
        Trace.error(f"MutagenError: {err}")
        return None

    duration    = metadata.info.length
    mode        = ["STEREO", "JOINTSTEREO", "DUALCHANNEL", "MONO"][int(getattr(metadata.info, "mode", None))]
    bitrate     = getattr(metadata.info, "bitrate", None)
    sample_rate = getattr(metadata.info, "sample_rate", None)

    return {
        "audio":           True,
        "durationAudio":   round(duration, 2),
        "bitrateAudio":    int(bitrate / 1000),
        "modeAudio":       mode,
        "sampleRateAudio": sample_rate
    }
