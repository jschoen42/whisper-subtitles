"""
    © Jürgen Schoenemeyer, 01.03.2025 15:26

    src/utils/audio.py

    PUBLIC:
     - split_audio(source_path: Path | str, dest_path: Path | str, filename: str, ffmpeg: str) -> None

     - convert_to_mp3(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None
     - convert_to_wav(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None
     - convert_to_flac(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None

     - filter_to_wav(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str, filter_path: str, filter_name: str) -> None
"""
from __future__ import annotations

import subprocess

from pathlib import Path

from utils.trace import Trace

""" FFmeg

    -i {source}
    -y
    -loglevel erro
    -vn
    -sample_fmt s16
    -ar {sampling}
    -ac 1
    -af "arnndn=m={filter_path}/{filter_name}.rnnn"
    -c:a flac
    -c:a mp3

    mp3:
        -b:a 96k

    wav:
        result e.g.: 216 MB

    flac:
        -compression_level [n]  # flac 0 ... 12 (default: 5)
        result e.g.: 0 -> 115 MB, 5 -> 104 MB, 8 -> 103 MB, 12 ->  103 MB
"""

def split_audio(source_path: Path | str, dest_path: Path | str, filename: str, ffmpeg: str) -> None:
    source_path = Path(source_path)
    dest_path = Path(dest_path)

    if not dest_path.is_dir():
        dest_path.mkdir(parents=True)

    source = source_path / filename
    dest   = dest_path / (Path(filename).stem + ".m4a")

    if dest.is_file():
        Trace.info(f"{dest} always exists")
    else:
        commands = f'"{ffmpeg}" -y -loglevel error -i "{source}" -c copy "{dest}"'

        if subprocess.run(commands, check=False).returncode == 0:
            Trace.info(f"FFmpeg Script Ran Successfully {dest}")
        else:
            Trace.error(f"There was an error running your FFmpeg script - {commands}")

def convert_to_mp3(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None:
    source_path = Path(source_path)
    dest_path   = Path(dest_path)

    if not dest_path.is_dir():
        dest_path.mkdir(parents=True)

    source = source_path / filename
    dest   = dest_path / (Path(filename).stem + ".wav")

    if dest.is_file():
        Trace.info(f"{dest} always exists")
    else:
        commands = f'"{ffmpeg}" -y -loglevel error -i "{source}" -vn -ar {sampling} -ac {channels} -b:a 96k "{dest}"'

        if subprocess.run(commands, check=False).returncode == 0:
            Trace.info(f"FFmpeg Script Ran Successfully {dest}")
        else:
            Trace.error(f"There was an error running your FFmpeg script - {commands}")

def convert_to_wav(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None:
    source_path = Path(source_path)
    dest_path   = Path(dest_path)

    if not dest_path.is_dir():
        dest_path.mkdir(parents=True)

    source = source_path / filename
    dest   = dest_path / (Path(filename).stem + ".wav")

    if dest.is_file():
        Trace.info(f"{dest} always exists")
    else:
        commands = f'"{ffmpeg}" -y -loglevel error -i "{source}" -vn -ar {sampling} -ac {channels} "{dest}"'

        if subprocess.run(commands, check=False).returncode == 0:
            Trace.info(f"FFmpeg Script Ran Successfully {dest}")
        else:
            Trace.error(f"There was an error running your FFmpeg script - {commands}")

def convert_to_flac(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str) -> None:
    source_path = Path(source_path)
    dest_path   = Path(dest_path)

    if not dest_path.is_dir():
        dest_path.mkdir(parents=True)

    source = source_path / filename
    dest   = dest_path / (Path(filename).stem + ".flac")

    if dest.is_file():
        Trace.info(f"{dest} always exists")
    else:
        commands = f'"{ffmpeg}" -y -loglevel error -i "{source}" -vn -ar {sampling} -ac {channels} -sample_fmt s16 -c:a flac -compression_level 5 "{dest}"'

        if subprocess.run(commands, check=False).returncode == 0:
            Trace.info(f"FFmpeg Script Ran Successfully {dest}")
        else:
            Trace.error(f"There was an error running your FFmpeg script - {commands}")

def filter_to_wav(source_path: Path | str, dest_path: Path | str, filename: str, sampling: int, channels: int, ffmpeg: str, filter_path: str, filter_name: str) -> None:
    source_path = Path(source_path)
    dest_path   = Path(dest_path)

    if not dest_path.is_dir():
        dest_path.mkdir(parents=True)

    source = source_path / filename
    dest   = dest_path / (Path(filename).stem + ".wav")

    if dest.is_file():
        Trace.info(f"{dest} always exists")
    else:
        filter_cmd = f"arnndn=m={filter_path}/{filter_name}.rnnn"
        commands = f'"{ffmpeg}" -y -loglevel error -i "{source}" -vn -ar {sampling} -ac {channels} -af "{filter_cmd}" "{dest}"'

        if subprocess.run(commands, check=False).returncode == 0:
            Trace.info(f"FFmpeg Script Ran Successfully {dest}")
        else:
            Trace.error(f"There was an error running your FFmpeg script - {commands}")
