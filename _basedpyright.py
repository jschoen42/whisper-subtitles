"""
    © Jürgen Schoenemeyer, 30.03.2025 15:54

    _basedpyright.py

    INSTALL:
     - uv add basedpyright --dev

    INSTALL STUBS - https://github.com/python/typeshed/tree/main/stubs
     - uv add lxml-stubs --dev
     - uv add pandas-stubs --dev
     - uv add types-beautifulsoup4 --dev
     - uv add types-openpyxl --dev
     - uv add types-python-dateutil --dev
     - uv add types-pyyaml --dev
     - uv add types-toml --dev
     - uv add types-xmltodict --dev

    RUN CLI
     - uv run _basedpyright.py .
     - uv run _basedpyright.py src
     - uv run _basedpyright.py src/main.py

    PUBLIC:
     - run_pyright(src_path: Path, python_version: str) -> None

    PRIVAT:
     - format_singular_plural(value: int, text: str) -> str
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time

from argparse import ArgumentParser
from collections import Counter
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict, List

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

LINEFEET = "\n"

CONFIG_FILE = "_basedpyright.tmp.json"

def format_singular_plural(value: int, text: str) -> str:
    if value == 1:
        return f"{value} {text}"
    return f"{value} {text}s"

def check_types(src_path: Path, python_version: str) -> None:

    if python_version == "":
        try:
            filepath = Path(".python-version")
            with filepath.open(mode="r") as f:
                python_version = f.read().strip()
        except OSError:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    # https://microsoft.github.io/pyright/#/configuration?id=diagnostic-settings-defaults

    settings: Dict[str, str | bool | List[str]] = {
        "pythonVersion": python_version,
        # "pythonPlatform": "Linux", # "Windows", "Darwin"

        "venvPath": ".",
        "venv": ".venv",

        # "typeCheckingMode": "off",
        # "typeCheckingMode": "basic",
        # "typeCheckingMode": "standard",
        "typeCheckingMode": "strict",

        # deactivate some Strict rules
        "reportUnknownArgumentType":  False,
        "reportUnknownMemberType":    False,
        "reportUnknownVariableType":  False,

        # extra rules
        "enableExperimentalFeatures":          True,
        "reportImplicitOverride":              True,
        "reportImplicitStringConcatenation":   True,
        "reportImportCycles":                  True,
        "reportMissingSuperCall":              True,
        "reportPropertyTypeMismatch":          True,
        "reportShadowedImports":               True,
        "reportUninitializedInstanceVariable": True,

        "reportCallInDefaultInitializer":      False,
        "reportUnnecessaryTypeIgnoreComment":  False, # mypy <-> pyright

        "deprecateTypingAliases": False,       # always False -> typing: List, Dict, ...
        "reportUnusedCallResult": False,       # always False -> _vars

        "exclude": [
            "**/.venv",
            "**/site-packages",
            "**/Scripts/activate_this.py",
            "**/src/faster_whisper/*",
            "**/src/extras/*",
        ],
    }

    if not src_path.exists():
        print(f"Error: path '{src_path}' not found")
        return

    start = time.perf_counter()

    folder_path = BASE_PATH / RESULT_FOLDER
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    name = src_path.stem
    if name == "":
        name = "."

    text  = f"Python:   {sys.version.replace(LINEFEET, ' ')}\n"
    text += f"Platform: {platform.platform()}\n"
    text += f"Date:     {datetime.now().astimezone():%d.%m.%Y %H:%M:%S}\n"
    text += f"Path:     {BASE_PATH}\n"
    text += "\n"

    text += "BasedPyRight [version] settings:\n"
    for key, value in settings.items():
        text += f" - {key}: {value}\n"

    config = Path(CONFIG_FILE)
    with config.open(mode="w", newline="\n") as config_file:
        json.dump(settings, config_file, indent=2)

    try:
        basedpyright_path = shutil.which("basedpyright")
        if not basedpyright_path:
            print("Error: 'basedpyright' not installed -> uv add basedpyright --dev")
            sys.exit(1)

        # https://github.com/DetachHead/basedpyright/blob/main/docs/configuration/command-line.md

        result: CompletedProcess[str] = subprocess.run(
            [basedpyright_path, src_path, "--project", config, "--outputjson"],
            capture_output=True,
            text=True,
            check=False, # important
            encoding="utf-8",
            errors="replace",
        )

    except subprocess.CalledProcessError as e:
        print(f"BasedPyRight error: {e}")
        sys.exit(1)

    finally:
        config.unlink()

    # returncode:
    #   0: No errors reported
    #   1: One or more errors reported
    #   2: Fatal error occurred with no errors or warnings reported
    #   3: Config file could not be read or parsed
    #   4: Illegal command-line parameters specified

    returncode = result.returncode
    stdout = result.stdout
    stderr = result.stderr

    if stderr != "":
        print(f"exit code: {returncode} - {stderr}")
        sys.exit(returncode)

    data = json.loads(stdout.replace("\xa0", " ")) # non breaking space

    # {
    #   "version": "1.1.394",
    #   "time": "1739984210930",
    #   "generalDiagnostics": [
    #     {
    #       "file": "g:\\Python\\Whisper\\whisper-datev-gitlab\\src\\combine_srt.py",
    #       "severity": "error",
    #       "message": "Type \"float\" is not assignable to declared type \"int\"\n  \"float\" is not assignable to \"int\"",
    #       "range": {
    #           "start": {
    #           "line": 49,
    #           "character": 32
    #         },
    #           "end": {
    #           "line": 49,
    #           "character": 40
    #         }
    #       },
    #       "rule": "reportAssignmentType" -> severity: only for file / error / warning, not for information
    #     }
    #   ],
    #   "summary": {
    #     "filesAnalyzed": 1,
    #     "errorCount": 0,
    #     "warningCount": 0,
    #     "informationCount": 0,
    #     "timeInSec": 2.583
    #   }
    # }

    version     = data["version"]
    diagnostics = data["generalDiagnostics"]
    summary     = data["summary"]

    text = text.replace("[version]", version )

    n = len(str(Path.cwd().absolute())) + 1

    msg_files = 0
    last_file = ""
    error_types: Counter[str] = Counter()
    for diagnostic in diagnostics:

        file = Path(diagnostic["file"]).as_posix()
        severity = diagnostic["severity"]
        if severity == "information":
            error_type = ""
        else:
            error_type = diagnostic["rule"]
            error_types[error_type] += 1

        if "range" in diagnostic:
            range_start = diagnostic["range"]["start"]
            range_text = f"{range_start['line']+1}:{range_start['character']+1}"
        else:
            range_text = ""

        msg = file[n:]
        msg += f":{range_text} - {severity}: " # 0-based
        msg += diagnostic["message"]
        if error_type != "":
            msg += f" ({error_type})"

        if last_file != file:
            if last_file != "":
                text += "\n"
            text += "\n### " + file[n:] + " ###\n"
            last_file = file
            msg_files += 1

        text += "\n" + msg

    text += "\n"

    if len(error_types)>0:
        text += "\nError types (sorted)"
        for error_type, count in error_types.most_common():
            text += f"\n - {error_type}: {count}"
        text += "\n\n"

    text += "\n"

    footer = "Found "
    footer += f"{format_singular_plural(summary['errorCount'],'error')}, "
    footer += f"{format_singular_plural(summary['warningCount'],'warning')}, "
    footer += f"{format_singular_plural(summary['informationCount'],'information')} in "
    footer += f"{msg_files} of {format_singular_plural(summary['filesAnalyzed'], 'file')}"

    text += footer + "\n"

    result_filename = f"BasedPyRight-{python_version}-[{name}].txt"
    with (folder_path / result_filename).open(mode="w", newline="\n") as f:
        f.write(text)

    duration = time.perf_counter() - start
    print(f"[BasedPyRight {version} ({duration:.2f} sec)] {footer} -> {RESULT_FOLDER}/{result_filename}")
    sys.exit(returncode)

if __name__ == "__main__":
    parser = ArgumentParser(description="static type check with BasedPyRight")
    parser.add_argument("path", nargs="?", type=str, default=".", help="relative path to a file or folder")
    parser.add_argument("-v", "--version", type=str, default="",  help="Python version 3.10/3.11/...")

    args = parser.parse_args()

    try:
        check_types(Path(args.path), args.version)
    except KeyboardInterrupt:
        print(" --> KeyboardInterrupt")
        sys.exit()
