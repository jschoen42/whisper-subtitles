"""
    © Jürgen Schoenemeyer, 08.01.2025

    PUBLIC:
    get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: float = 0) -> Tuple[Workbook, int]

    get_excel_sheet(source_path: str, filename: str, sheet: str, comment: str, last_timestamp: float = 0.0) -> Tuple[None | Worksheet, float]
    get_excel_sheet_special(workbook: Workbook, sheet: str, comment: str) -> None | Worksheet

    get_cell_text(in_cell: Cell | MergedCell) -> str:
    get_cell_value(in_cell: Cell | MergedCell) -> bool | str

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
from openpyxl.cell.cell import Cell, MergedCell

from utils.trace import Trace
from utils.file  import get_modification_timestamp, check_excel_file_exists

# UserWarning: Data Validation extension is not supported and will be removed
warnings.simplefilter("ignore")

def get_excel_file(source_path: str, filename: str, comment: str, last_timestamp: float = 0.0) -> Tuple[None | Workbook, float]:
    file_path = source_path + filename

    if check_excel_file_exists(file_path) is False:
        Trace.error(f"{comment} - file not found '{file_path}'")
        return (None, 0)

    try:
        workbook = load_workbook(filename = file_path)
    except OSError as err:
        Trace.error(f"{comment} - importExcel {err}")
        return (None, 0)

    return (workbook, max(last_timestamp, get_modification_timestamp(file_path)))

def get_excel_sheet(source_path: str, filename: str, sheet_name: str, comment: str, last_timestamp: float = 0.0) -> Tuple[None | Worksheet, float]:
    file_path = source_path + filename

    if check_excel_file_exists(file_path) is False:
        Trace.error(f"{comment} - file not found '{file_path}'")
        return (None, 0)

    try:
        workbook = load_workbook(filename = file_path)
    except OSError as err:
        Trace.error(f"{comment} - importExcel '{err}'")
        return (None, 0)

    try:
        sheet = workbook[sheet_name]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel '{filename}' {err}")
        return (None, 0)

    check_hidden(sheet, "get_excel_sheet")

    return (
        sheet,
        max(last_timestamp, get_modification_timestamp(file_path))
    )

def get_excel_sheet_special(workbook: Workbook, sheet_name: str, comment: str) -> None | Worksheet:
    try:
        sheet = workbook[sheet_name]
    except KeyError as err:
        Trace.error(f"{comment} - importExcel {err}")
        return None

    check_hidden(sheet, "get_excel_sheet_special")
    return sheet

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

def get_cell_value(in_cell: Cell | MergedCell) -> bool | str:
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

def get_cell_text(in_cell: Cell | MergedCell) -> str:
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
