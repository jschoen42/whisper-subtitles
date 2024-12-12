"""
    (c) Jürgen Schoenemeyer, 03.12.2024

    PUBLIC:
    open_xml_as_dict(myzip: ZipFile, path: Path | str, comment: str = "[open_xml_as_dict]") -> dict | None
"""

from pathlib import Path
from zipfile import ZipFile

import xmltodict

from src.utils.trace import Trace
from src.utils.file import get_trace_path

def open_xml_as_dict(myzip: ZipFile, path: Path | str, comment: str = "[open_xml_as_dict]") -> dict | None:
    try:
        with myzip.open(path) as xml_file:
            data = xmltodict.parse(xml_file.read())
    except OSError as err:
        error = str(err).split(":")[0]
        Trace.error(f"{error} '{get_trace_path(path)}'")
        data = None

    return data
