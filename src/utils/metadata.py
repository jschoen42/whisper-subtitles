"""
    © Jürgen Schoenemeyer, 04.01.2025

    PUBLIC:
     - get_media_info(filepath: str | BytesIO) -> None | Dict
     - get_audio_duration(filepath: str) -> float
     - get_media_trackinfo(filepath: str) -> None | Dict
     - get_video_metadata_mediainfo(filepath: str) -> None | Dict
"""

from io import BytesIO
from typing import Any, Dict

from pymediainfo import MediaInfo

from utils.trace import Trace

def get_media_info(filepath: str | BytesIO) -> None | Dict:
    """
    {
        "track_type": "Audio",
        "count": "285",
        "count_of_stream_of_this_kind": "1",
        "kind_of_stream": "Audio",
        "other_kind_of_stream": ["Audio"],
        "stream_identifier": "0",
        "streamorder": "1",
        "track_id": 2,
        "other_track_id": ["2"],
        "format": "AAC",
        "other_format": ["AAC LC"],
        "format_info": "Advanced Audio Codec Low Complexity",
        "commercial_name": "AAC",
        "format_additionalfeatures": "LC",
        "codec_id": "mp4a-40-2",
        "duration": 97431,
        "other_duration": ["1 min 37 s", "1 min 37 s 431 ms", "1 min 37 s", "00:01:37.431", "00:01:37.431"],
        "bit_rate_mode": "VBR",
        "other_bit_rate_mode": ["Variable"],
        "bit_rate": 125492,
        "other_bit_rate": ["125 kb/s"],
        "maximum_bit_rate": 167441,
        "other_maximum_bit_rate": ["167 kb/s"],
        "channel_s": 2,
        "other_channel_s": ["2 channels"],
        "channel_positions": "Front: L R",
        "other_channel_positions": ["2/0/0"],
        "channel_layout": "L R",
        "samples_per_frame": "1024",
        "sampling_rate": 44100,
        "other_sampling_rate": ["44.1 kHz"],
        "samples_count": "4296707",
        "frame_rate": "43.066",
        "other_frame_rate": ["43.066 FPS (1024 SPF)"],
        "frame_count": "4196",
        "compression_mode": "Lossy",
        "other_compression_mode": ["Lossy"],
        "stream_size": 1528361,
        "other_stream_size": ["1.46 MiB (36%)", "1 MiB", "1.5 MiB", "1.46 MiB", "1.458 MiB", "1.46 MiB (36%)"],
        "proportion_of_this_stream": "0.35704",
        "language": "en",
        "other_language": ["English", "English", "en", "eng", "en"],
        "encoded_date": "2023-11-30 11:57:50 UTC",
        "tagged_date": "2023-11-30 11:57:50 UTC"
    }
    """

    try:
        ret = get_media_trackinfo(filepath)
        return {
            "duration":     round(ret.duration/1000, 3),
            "channels":     ret.channel_s,
            "samplingRate": ret.sampling_rate,
        }
    except Exception as error: # pylint: disable=broad-except
        Trace.error(f"MediaInfo: {error}")
        return None

def get_audio_duration(filepath: str | BytesIO) -> float:
    duration = -1

    media_info = MediaInfo.parse(filepath)
    for track in media_info.tracks:
        if track.track_type == "Audio":
            duration = round(track.duration / 1000, 3)

    return duration

def get_media_trackinfo(filepath: str | BytesIO) -> None | Dict:
    ret = None

    media_info = MediaInfo.parse(filepath)
    for track in media_info.tracks:
        if track.track_type == "Audio":
            ret = track

    return ret

def get_video_metadata_mediainfo(filepath: str | BytesIO) -> None | Dict:

    info: Dict[str, Any] = {
        "width":    "",
        "height":   "",
        "duration": "",
        "bitrate":  "",
        "tracks":   0,

        "video": {
            "trackID":    "",
            "format":     "",
            "bitrate":    "",
            "fps":        "",
            # "colorSpace": "",
            # "cromaSubSampling": "",
            "colorInfo":  ""
        },

        "audio": {
            "trackID":  "",
            "format":   "",
            "channels": "",
            "bitrate":  "",
            "samplingRate": "",
        }
    }

    # https://pymediainfo.readthedocs.io/en/stable/

    try:
        media_info = MediaInfo.parse(filepath)

        for track in media_info.tracks:
            if track.track_type == "Video":
                # print("######### VIDEO # ######")
                # print(track.__dict__)
                # print("########################")

                info["width"]  = track.width
                info["height"] = track.height
                info["tracks"] += 1

                if track.duration:
                    info["duration"] = round(track.duration / 1000, 3)

                info["video"]["track"] = track.track_id
                if track.bit_rate:
                    bitrate =  track.bit_rate / 1000
                    info["video"]["bitrate"]  = bitrate

                    if info["bitrate"] == "":
                        info["bitrate"] = bitrate
                    else:
                        info["bitrate"] += bitrate

                info["video"]["format"]     = track.format + " " + track.format_profile
                info["video"]["fps"]        = float(track.frame_rate)
                # info["video"]["colorSpace"] = track.color_space
                # info["video"]["cromaSubSampling"] = track.chroma_subsampling
                info["video"]["colorInfo"] = track.color_space + " " + track.chroma_subsampling

            if track.track_type == "Audio":
                # print("####### AUDIO #########")
                # print(track.__dict__)
                # print("#######################")

                info["tracks"] += 1
                info["audio"]["trackID"] = track.track_id
                if track.bit_rate:
                    bitrate =  track.bit_rate / 1000
                    info["audio"]["bitrate"] = bitrate
                    if info["bitrate"] == "":
                        info["bitrate"] = bitrate
                    else:
                        info["bitrate"] += bitrate

                if track.channel_s < 3:
                    channels = ["mono", "stereo"][track.channel_s-1]
                else:
                    channels = track.channel_s + " channels"

                info["audio"]["channels"]     = track.channel_s
                info["audio"]["samplingRate"] = track.sampling_rate
                info["audio"]["format"]       = track.format  + " " + track.format_additionalfeatures + " (" + channels + ")"

    except Exception as error: # pylint: disable=broad-except
        Trace.error(f"MediaInfo: {error}")
        return None

    return info
