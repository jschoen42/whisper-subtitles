"""
    © Jürgen Schoenemeyer, 18.01.2025

    PUBLIC:
      - export_TextToSpeech_excel(data: List[ColumnSubtitleInfo], pathname: Path | str, filename: str) -> bool:

    PRIVATE:
     - def page_setup_print(worksheet: Any) -> None:
"""

from typing import Any, Dict, List, NamedTuple, TypedDict, cast
from pathlib import Path
from enum import StrEnum

import xlsxwriter                               # type: ignore[import-untyped]
from xlsxwriter.exceptions import XlsxFileError # type: ignore[import-untyped]

from utils.trace     import Trace
from utils.decorator import duration
from utils.file      import create_folder
from utils.excel     import seconds_to_timecode_excel

"""
    export_TextToSpeech_excel(
        data: List[SubtitleColumnFormat],
        pathname: Path | str,
        filename: str
    ) -> bool:

    data: [
        {'start': 12.55, 'end': 18.59, 'text': "Herzlich willkommen zum Seminar 'Chancen der Digitalisierung im Rechnungswesen nutzen'.", 'pause': 0},
        {'start': 18.59, 'end': 20.43, 'text': '[pause: 1.84 sec]', 'pause': -1},
        {'start': 20.43, 'end': 23.51, 'text': 'Liebe Kolleginnen und Kollegen, ich darf mich kurz vorstellen.', 'pause': 1.84},
        {'start': 23.51, 'end': 23.85, 'text': '[pause: 0.34 sec]', 'pause': -1},
        ...
        # one paragraph:
        {'start': 100.11, 'end': 107.75, 'text': 'Im Kapitel 1 möchte ich Ihnen ganz gerne ein paar grundlegende Hinweise geben, wie Sie die Digitalisierung ins Rennen bringen.', 'pause': 0.72},
        {'start': 107.75, 'end': 121.27, 'text': 'Im Kapitel 2 befassen wir uns mit elektronischen Bankauszügen, den verschiedenen Varianten, wie wir an die Daten, die so oder so elektronisch bei der Bank vorhanden sind, optimal verarbeiten können.', 'pause': 0},
        {'start': 121.27, 'end': 125.17, 'text': 'Das Kapitel 3 betrifft die Lerndatei.', 'pause': 0},
        ...
    ]

    pathname: data / [project] / 09_excel / [settings] /
    filename: [video].xlsx

"""

# dict
class ColumnSubtitleInfo(TypedDict):
    start: float
    end:   float
    text:  str
    pause: float

# excel

class Color(StrEnum):
    WHITE     = "#ffffff"
    BLUE      = "#4f81bd"
    GREY      = "#a5a5a5"
    LIGHTGREY = "#dadcdd"
    BLACK     = "#000000"
    ERROR     = "#ff8888" # red
    WARNING   = "#fcd723" # yellow
    OK        = "#92d050" # green

class SubtitleColumnFormat(NamedTuple):
    width:        int
    header_style: str # -> global_styles
    header_text:  str
    body_style:   str # -> global_styles

excel_format_subtitle: Dict[str, SubtitleColumnFormat] = {
    "start": SubtitleColumnFormat( 15, "head", "start", "time"), # 00:09.764
    "end":   SubtitleColumnFormat( 15, "head", "end",   "time"), # 00:18.464
    "X":     SubtitleColumnFormat(  5, "head", "",      "char"), # x (start new block) | empty (continue block)
    "s-p":   SubtitleColumnFormat(  5, "head", "",      "char"), # ssml p (paragraph) | s (sentence) | > (append)
    "text":  SubtitleColumnFormat(100, "head", "text",  "text"), # subtitle text
    "pause": SubtitleColumnFormat( 10, "head", "pause", "char"), # extra pause in seconds (manual added later)
}

# column style: head / time, char, text

global_styles = {

    # header

    "head": {
        "font_name":  "Open Sans Bold",
        "font_size":  10,
        "font_color": Color.WHITE,
        "bg_color":   Color.BLUE,
        "align":      "center",
        "valign":     "vcenter",
        "text_wrap":  False,
    },

    # body

    "time": {
        "font_name":  "Segoe UI",
        "font_size":  11,
        "font_color": Color.BLACK,
        "align":      "center",
        "valign":     "top",
        "text_wrap":  True,
    },
    "char": {
        "font_name":  "Segoe UI",
        "font_size":  11,
        "font_color": Color.BLACK,
        "align":      "center",
        "valign":     "top",
        "text_wrap":  True,
    },
    "text": {
        "font_name":  "Segoe UI",
        "font_size":  11,
        "font_color": Color.BLACK,
        "align":      "left",
        "indent":     1,
        "valign":     "top",
        "text_wrap":  True,
    },
}

@duration("export '{filename}'")
def export_TextToSpeech_excel(data: List[SubtitleColumnFormat], pathname: Path | str, filename: str) -> bool:
    pathname = Path(pathname)

    create_folder(pathname)
    dest_path = Path(pathname, filename)

    workbook = xlsxwriter.Workbook(dest_path)
    worksheet = workbook.add_worksheet("whisper transcription") # type: ignore[reportUnknownVariableType]

    page_setup_print(worksheet)

    worksheet.freeze_panes(1, 0)

    named_styles: Dict[str, Any] = {}
    for key, value in global_styles.items():
        named_styles[key] = workbook.add_format(value)

    # get template infos

    header_style: List[str] = []
    header_text: List[str] = []
    body_style: List[str] = []

    for i, entry in enumerate(excel_format_subtitle):
        values = excel_format_subtitle[entry]
        worksheet.set_column(i, i, values[0])

        header_style.append(values[1])
        header_text.append(values[2])
        body_style.append(values[3])

    def append_row(worksheet: Any, line_number: int, styles: List[str], texts: List[Any]) -> None:
        for i, text in enumerate(texts):
            cell_style = named_styles[styles[i]]
            worksheet.write(line_number, i, text, cell_style)

    # header

    append_row(worksheet, 0, header_style, header_text)
    worksheet.set_row(0, 20) # set row 0 to height 20

    # body

    last_end = True
    count = 0

    for i in range(0, len(data)):
        subtitle_info = cast(ColumnSubtitleInfo, data[i])

        start = seconds_to_timecode_excel(subtitle_info["start"])
        end = seconds_to_timecode_excel(subtitle_info["end"])

        if i == 0 and last_end:
            char = "x"
        else:
            char = ""

        text = subtitle_info["text"]

        last_end = text[-1] != "…"

        if subtitle_info["pause"] == -1:
            # count += 1
            # append_row(worksheet, count+1, body_style, [start, end, char, "", text, ""])
            pass
        else:
            count += 1
            if subtitle_info["pause"] == 0 and count != 1:
                append_row(worksheet, count, body_style, [start, end, char, ">", text, 0])
            else:
                append_row(worksheet, count, body_style, [start, end, char, "p", text, 0])

    try:
        workbook.close()
        return True
    except XlsxFileError as err:
        Trace.error(f"XlsxFileError:{err}")
        return False

# https://xlsxwriter.readthedocs.io/page_setup.html

def page_setup_print(worksheet: Any) -> None:

    def inch_to_mm(inch: float) -> float:
        return inch / 2.54

    # Page Setup -> Page
    worksheet.set_landscape()
    worksheet.set_paper(9)       # A4
    worksheet.fit_to_pages(1, 0)

    # Page Setup -> Margins
    margin_left   = inch_to_mm(1.5)
    margin_right  = inch_to_mm(1.5)
    margin_top    = inch_to_mm(1.5)
    margin_bottom = inch_to_mm(1.75)
    worksheet.set_margins(margin_left, margin_right, margin_top, margin_bottom)
    worksheet.center_horizontally()

    # Page Setup -> Header/Footer
    footer_left   = "&F / &A"  # File name / Worksheet name
    footer_center = "&D / &T"  # Date / Time
    footer_right  = "&P / &N"  # Page number / Total number of pages
    margin_footer = inch_to_mm(1.0)
    worksheet.set_footer(f"&L{footer_left}&C{footer_center}&R{footer_right}", {"margin": margin_footer})

    # Page Setup -> Sheet
    worksheet.hide_gridlines(0)
    worksheet.repeat_rows(0, 0) # -> $1:$1
