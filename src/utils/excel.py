"""
    (c) Jürgen Schoenemeyer, 06.01.2025

    PUBLIC:
    get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: float = 0) -> Tuple[int, Workbook, int]

    get_excel_sheet(source_path: str, filename: str, sheet: str, comment: str, last_timestamp: float = 0.0) -> Tuple[bool, Worksheet, float]
    get_excel_sheet_special(workbook: Workbook, sheet: str, comment: str) -> Tuple[bool, None | Worksheet]

    get_cell_value(in_cell: cell) -> str
    check_quotes( wb_name: str, word: str, line_number: int, function_name: str ) -> str
    check_quotes_error(wb_name: str, word: str, line_number: int, function_name: str) -> Tuple[dict | bool, str]
    check_hidden(sheet, comment: str) -> None
    excel_date(date, time_zone) -> float
"""

import re
import unicodedata
import datetime

import warnings

from typing import Any, Tuple


from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.workbook.workbook import Workbook
from openpyxl.cell.cell import Cell

from utils.trace import Trace
from utils.file  import get_modification_timestamp, check_excel_file_exists

# UserWarning: Data Validation extension is not supported and will be removed
warnings.simplefilter("ignore")

def get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: float = 0.0) -> Tuple[int, None | Workbook, float]:
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

def get_excel_sheet(source_path: str, filename: str, sheetname: str, comment: str, last_timestamp: float = 0.0) -> Tuple[bool, None | Any, float]:
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
        sheet = workbook[sheetname]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel '{filename}' {err}")
        return (True, None, 0)

    check_hidden(sheet, "get_excel_sheet")

    return (
        False,
        sheet,
        max(last_timestamp, get_modification_timestamp(file_path))
    )

def get_excel_sheet_special(workbook: Workbook, sheetname: str, comment: str) -> Tuple[bool, None | Any]:
    try:
        sheet = workbook[sheetname]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel {err}")
        return True, None

    check_hidden(sheet, "get_excel_sheet_special")
    return False, sheet

######################################################################################
# get_cell_value with converting
#  - '\n'  -> '<br>
#  - '[-]' -> '&shy;'
#  - 'true' -> True, 'false' -> False, 'N/A' -> ''
#  - '[br]' -> <br>
#  - [b]...[/b] -> <b>...</b>, same with i, u, mark, sub, sup
#  - [nobr] -> <nobr>
#  - [hide] -> <hide> (custom)
######################################################################################

def get_cell_value(in_cell: Cell) -> bool | str:
    if in_cell.value is None:
        return ""

    # data_type
    #   f: formular
    #   s: string
    #   n: numeric
    #   b: boolean
    #   n: null
    #   inlineStr: inline
    #   e: error
    #   str: formlar cached string

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

def check_quotes( wb_name: str, word: str, line_number: int, function_name: str ) -> str:
    if word == "":
        return ""

    if word[:1] == '"' and word[-1:] == '"':
        return word[1:-1]
    else:
        Trace.error( f"[{function_name}] '{wb_name}': line {line_number} quotes missing: '{word}'")
        return ""

def check_quotes_error(wb_name: str, word: str, line_number: int, function_name: str) -> Tuple[dict | bool, str]:
    if word == "":
        return False, ""

    if word[:1] == '"' and word[-1:] == '"':
        return False, word[1:-1]
    else:
        Trace.error(f"{function_name} '{wb_name}': line {line_number} quotes missing: '{word}'")
        return True, ""

def check_hidden(sheet: Worksheet, comment: str) -> None:
    for key, value in sheet.column_dimensions.items():
        if value.hidden is True:
            if key != "A":
                Trace.warning( f"{comment}:  hidden column: {key}")

    for row_num, row_dimension in sheet.row_dimensions.items():
        if row_dimension.hidden is True:
            Trace.warning( f"{comment}:  hidden row: {row_num}")

def excel_date(date: Any, time_zone: str) -> float:
    day_in_seconds = 86400

    # 30.12.1899 (+ 1 day)
    # https://forum.openoffice.org/en/forum/viewtopic.php?t=108820#post_content529967

    tz = datetime.timezone.utc if time_zone == "UTC" else None
    delta = date - datetime.datetime(1899, 12, 30, 0, 0, 0, 0, tzinfo=tz)
    return float(delta.days) + (float(delta.seconds) / day_in_seconds)
