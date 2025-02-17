from typing import Any, Dict
from pathlib import Path
from enum import StrEnum, IntEnum

from openpyxl import load_workbook
from openpyxl.styles import NamedStyle, Font, Alignment
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from utils.trace     import Trace
from utils.decorator import duration
from utils.excel     import get_cell_text, check_excel_file_exists

class Color(StrEnum):
    WHITE   = "00ffffff"
    BLUE    = "004f81bd"
    GREY    = "00a5a5a5"
    BLACK   = "00000000"
    ERROR   = "00FF8888" # red
    WARNING = "00fcd723" # yellow
    OK      = "0092d050" # green

class Fontname(StrEnum):
    HEAD = "Open Sans Bold"
    BODY = "Consolas"

class Fontsize(IntEnum):
    HEAD = 10
    BODY = 11

@duration("update '{filename}' -> '{filename_update}'")
def update_dictionary_excel(pathname: Path | str, filename: str, filename_update: str, column_name: str, data: Dict[str, Any]) -> None | bool:
    pathname = Path(pathname)
    source = pathname / filename

    def set_styles(wb: Workbook) -> None:
        if "used" not in wb.style_names:
            style = NamedStyle(name="used")
            style.font = Font(name=Fontname.BODY, color=Color.BLACK, size=Fontsize.HEAD)
            style.alignment = Alignment(vertical="top", horizontal="center")
            wb.add_named_style(style)

    if not check_excel_file_exists(source):
        Trace.error(f"file not found: {source}")
        return None

    try:
        wb: Workbook= load_workbook(filename=source)
    except OSError as err:
        Trace.error(f"importExcel: {err}")
        return None

    set_styles(wb)

    for sheet_name in wb.sheetnames:
        if sheet_name[:1] == "-":
            continue

        if sheet_name in data:
            data_info_sheet = data[sheet_name]
        else:
            Trace.error(f"sheet '{sheet_name}' missing in update info")
            continue

        ws: Worksheet = wb[sheet_name]

        row = -1
        for i in range(0, ws.max_column):
            if get_cell_text(ws[1][i]) == column_name:
                row = i
                break

        if row < 0:
            Trace.error(f"sheet '{sheet_name}' - column '{column_name}' not found")
            continue

        for i in range(3, ws.max_row + 1):
            row_cells = ws[i]

            ws.cell(i, row + 1).value = ""

            if get_cell_text(row_cells[0]) != "":
                if str(i) in data_info_sheet:
                    ws.cell(i, row + 1).value = data_info_sheet[str(i)]
                else:
                    ws.cell(i, row + 1).value = 0

                if get_cell_text(row_cells[1]) != "":
                    ws.cell(i, row + 1).style = "used"

    dest_path = pathname / filename_update
    try:
        wb.save(filename=dest_path)
        Trace.result(f"'{dest_path}'")
        return True
    except OSError as err:
        Trace.error(f"{err}")
        return False
