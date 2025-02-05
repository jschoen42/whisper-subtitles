"""
    © Jürgen Schoenemeyer, 29.01.2025

    src/utils/format.py

    PUBLIC:
     - floor(number: float, decimals: int=2) -> int

     - convert_date_time(time_string: str) -> int

     - format_bytes( size: int, unit: str ) -> str
     - format_bytes_v2(size: int) -> str

     - convert_duration(duration: int) -> str

     - bin_nibble_null(val: int) -> str
     - bin_nibble(val: int) -> str

     - to_bool(in_text: str) -> bool
     - str_to_bool(value: str) -> bool
"""

import math
import datetime

from typing import Any

# from re import A

from dateutil.parser import parse
# from utils.trace import Trace

def floor(number: float, decimals: int=2) -> int:
    if decimals < 0:
        raise ValueError("decimal places has to be 0 or more")

    if decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return int(math.floor(number * factor) / factor)

def convert_date_time(time_string: str) -> int:
    my_time_string = parse(time_string.replace("UTC", ""))

    timestamp = datetime.datetime.timestamp(my_time_string)
    return int(timestamp)

def convert_to_seconds(timestring: str) -> float:
    tmp = timestring.split(":")
    return 60 * int(tmp[0]) + int(tmp[1]) + float("." + tmp[2])

"""
def format_bytes( size: int, reference: str ) -> str:
    # https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb#answer-77815988

    next_prefix = {"B":"KB", "KB":"MB", "MB":"GB", "GB":"TB", "TB":"PB", "b":"Kb", "Kb":"Mb", "Mb":"Gb", "Gb":"Tb", "Tb":"Pb"}
    format_size = lambda i, s: f"{i:.2f} {s}" if i<1024 or s not in next_prefix else format_size(i/1024,next_prefix[s])
    return format_size(size, reference)
"""

def format_bytes( size: int, unit: str ) -> str:
    next_unit = {
        "B":"KB", "KB":"MB", "MB":"GB", "GB":"TB", "TB":"PB",
        "b":"Kb", "Kb":"Mb", "Mb":"Gb", "Gb":"Tb", "Tb":"Pb"
    }

    if unit not in next_unit:
        return f"{size:.2f} {unit}"

    if size<1024:
        return f"{size:.2f} {unit}"

    return f"{size/1024:.2f} {next_unit[unit]}"

# https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb#answer-71538936

def format_bytes_v2(size: int) -> str:
    power = 0 if size <= 0 else math.floor(math.log(size, 1024))

    if power == 0:
        return f"{size} B"
    else:
        return f"{round(size / 1024 ** power, 3)} {["B", "KB", "MB", "GB", "TB"][int(power)]}"

def convert_duration(duration: int) -> str:
    seconds=int(duration/1000)%60
    minutes=int(duration/(1000*60))%60
    hours=int(duration/(1000*60*60))%24
    # ms = duration % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" # .{ms:03d}"

def bin_nibble_null(val: int) -> str:
    b = bin(val)[2:]
    new_b = ".".join([b[::-1][i:i+4][::-1] for i in range(0, len(b), 4)][::-1])
    return "".join(["0"]*(4 - len(b) % 4 if len(b) % 4 != 0 else 0) + [new_b])

def bin_nibble(val: int) -> str:
    b = bin(val)[2:]
    return  ".".join([b[::-1][i:i+4][::-1] for i in range(0, len(b), 4)][::-1])

FALSE_STRINGS = ("0", "F", "FALSE", "N", "NO")

def to_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.upper() in FALSE_STRINGS:
        return False
    return bool(value)

def str_to_bool(value: Any) -> bool | None:
    if not value:
        return None

    if value.lower() in ["y", "yes", "t", "true", "on", "1"]:
        return True
    elif value.lower() in ["n", "no", "f", "false", "off", "0"]:
        return False
    else:
        return None

