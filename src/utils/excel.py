"""
    PUBLIC:
    get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: int = 0) -> Tuple[int, Workbook, int]

    get_excel_sheet(source_path: str, filename: str, sheet: str, comment: str, last_timestamp: int = 0) -> Tuple[bool, Worksheet, int]
    get_excel_sheet_special(workbook: Workbook, sheet: str, comment: str) -> Tuple[bool, None | Worksheet]

    get_cell_value(in_cell: cell) -> str
    check_hidden(sheet, comment: str) -> None
    excel_date(date, time_zone) -> float
"""

import unicodedata
import re
import datetime

from typing import Tuple

from openpyxl import Workbook, cell
from openpyxl import load_workbook

from src.utils.trace import Trace
from src.utils.file  import get_modification_timestamp, check_excel_file_exists

def get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: int = 0) -> Tuple[int, Workbook, int]:
    file_path = source_path + filename

    if check_excel_file_exists(file_path) is False:
        Trace.error(f"{comment} - file not found '{file_path}'")
        return (1, None, 0)

    try:
        workbook = load_workbook(filename = file_path)
    except OSError as err:
        Trace.error(f"{comment} - importExcel {err}")
        return (1, None, 0)

    return (0, workbook, max(last_timestamp, get_modification_timestamp(file_path)))

def get_excel_sheet(source_path: str, filename: str, sheet: str, comment: str, last_timestamp: int = 0) -> Tuple[bool, any, int]:
    file_path = source_path + filename

    if check_excel_file_exists(file_path) is False:
        Trace.error(f"{comment} - file not found '{file_path}'")
        return (True, None, 0)

    try:
        workbook = load_workbook(filename = file_path)
    except OSError as err:
        Trace.error(f"{comment} - importExcel '{err}'")
        return (True, None, 0)

    try:
        sheet = workbook[sheet]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel '{filename}' {err}")
        return (True, None, 0)

    check_hidden(sheet, sheet)

    return (
        False,
        sheet,
        max(last_timestamp, get_modification_timestamp(file_path))
    )

def get_excel_sheet_special(workbook: Workbook, sheet: str, comment: str) -> Tuple[bool, any]:
    try:
        sheet = workbook[sheet]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel {err}")
        return True, None

    check_hidden(sheet, sheet)
    return False, sheet

def get_cell_value(in_cell: cell) -> bool | str:
    if in_cell.value is None:
        return ""

    if in_cell.data_type == "f":
        return f"formula not support: {in_cell.value}"

    txt = unicodedata.normalize("NFC", str(in_cell.value).rstrip())
    txt = txt.replace("\n", "<br>")
    txt = txt.replace("[-]", "&shy;")
    if txt == "true":
        return True

    if txt == "false":
        return False

    if txt == "N/A":
        return ""

    return re.sub(r"\[(\/*)(br|b|i|u|mark|hide|nobr|sub|sup)\]", r"<\1\2>", txt)

def check_hidden(sheet, comment: str) -> None:
    for key, value in sheet.column_dimensions.items():
        if value.hidden is True:
            if key != "A":
                Trace.warning( f"{comment}:  hidden column: {key}")

    for row_num, row_dimension in sheet.row_dimensions.items():
        if row_dimension.hidden is True:
            Trace.warning( f"{comment}:  hidden row: {row_num}")

def excel_date(date, time_zone) -> float:
    day_in_seconds = 86400

    # 30.12.1899 (+ 1 day)
    # https://forum.openoffice.org/en/forum/viewtopic.php?t=108820#post_content529967

    delta = date - datetime.datetime(1899, 12, 30, 0, 0, 0, 0, time_zone)
    return float(delta.days) + (float(delta.seconds) / day_in_seconds)
