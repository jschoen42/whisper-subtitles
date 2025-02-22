# uv run _mypy.py src

from __future__ import annotations

import json
import locale
import platform
import re
import shutil
import subprocess
import sys
import time
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime
from pathlib import Path
from re import Match
from subprocess import CompletedProcess
from typing import List

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

LINEFEET = "\n"

# temp.toml

CONFIG = \
"""
[tool.mypy]
mypy_path = "src"
python_version = "[version]"
exclude = [
    "/extras/*",
    "/faster_whisper/*",
]

[[tool.mypy.overrides]]
module = "faster_whisper.*"
ignore_errors = true
"""
def run_mypy(src_path: Path, python_version: str) -> None:

    if python_version == "":
        try:
            with Path.open(Path(".python-version"), mode="r") as f:
                python_version = f.read().strip()
        except OSError:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    configuration = CONFIG.replace("[version]", python_version )

    # https://mypy.readthedocs.io/en/stable/command_line.html
    # https://gist.github.com/Michael0x2a/36c5948a7ea571b722686226639b0859

    settings: List[str] = [

        "--sqlite-cache",                 # default: False
        "--namespace-packages",

        ### Import discovery
        "--namespace-packages",           # default: True
        "--explicit-package-bases",       # default: False
        # "--ignore-missing-imports",     # default: False
        # "--follow-untyped-imports",     # default: False
        # "--follow-imports",             # default: str normal (normal, silent, skip, error)
        # "--follow-imports-for-stubs",   # default: False
        # "--python-executable",          # default: str
        # "--no-site-packages",           # default: False
        # "--no-silence-site-packages",   # default: False

        ### Platform configuration
        # "--python-version",             # default: str -> pyproject.toml
        # "--platform",                   # default: str
        # "--always-true",                # default: str constant, constant, ...

        ### Disallow dynamic typing
        # "--disallow-any-unimported",    # default: False
        # "--disallow-any-expr",          # default: False
        # "--disallow-any-decorated",     # default: False
        # "--disallow-any-explicit",      # default: False
        # "--disallow-any-generics",      # default: False
        # "--disallow-subclassing-any",   # default: False

        ### Untyped definitions and calls
        "--disallow-untyped-calls",       # default: False
        # "--untyped-calls-exclude",      # default: str call, call, ...
        "--disallow-untyped-defs",        # default: False
        "--disallow-incomplete-defs",     # default: False
        # "--check-untyped-defs",         # default: False
        "--disallow-untyped-decorators",  # default: False

        ###  None and Optional handling
        # "--implicit-optional",          # default: False
        # "--strict-optional",            # default: False

        ###  Configuring warnings
        "--warn-redundant-casts",         # default: False
        # "--warn-unused-ignores",        # default: False
        "--warn-no-return",               # default: False
        # "--warn-return-any",            # default: False
        "--warn-unreachable",             # default: False

        ### Suppressing errors
        # "--ignore-errors",              # default: False

        ### Miscellaneous strictness flags
        # "--allow-untyped-globals",      # default: False
        "--allow-redefinition",           # default: False
        # "--local-partial-types",        # default: False
        # "--disable-error-code",         # default: str error, error, ...
        # "--enable-error-code",          # default: str error, error, ...
        "--extra-checks",                 # default: False
        # "--implicit-reexport",          # default: True
        # "--strict-concatenate",         # default: False
        # "--strict",                     # default: False

        ### Configuring error messages
        # "--show-error-context"          # default: False
        # "--show-column-numbers",        # default: False
        # "--show-error-code-links".      # default: False
        # "--hide-error-codes",           # default: False
        # "--show-error-end",             # default: False
        # "--pretty",                     # default: False
        # "--error-summary",              # default: True
        # "--show-absolute-path",         # default: False
        "--force-uppercase-builtins",     # default: False
        # "--force-union-syntax",         # default: False

        ### Advanced options
        # "--plugins",                    # default: [str] plugin, plugin, ...
        # "--pdb",                        # default: False
        # "--show-traceback",             # default: False
        # "--raise-exceptions",           # default: False
        # "--custom-typing-module",       # default: str
        # "--custom-typeshed-dir",        # default: str
        # "--warn-incomplete-stub",       # default: False

        ### Report generation
        # "--any-exprs-report",           # default: str
        # "--cobertura-xml-report",       # default: str
        # "--html-report",                # default: str
        # "--xslt-html-report",           # default: str
        # "--linecount-report",           # default: str
        # "--linecoverage-report",        # default: str
        # "--lineprecision-report",       # default: str
        # "--txt-report",                 # default: str
        # "--xslt-txt-report",            # default: str
        # "--xml-report",                 # default: str

        ### Miscellaneous
        # "--junit-xml",                  # default: str
        # "--scripts-are-modules",        # default: False
        # "--warn-unused-configs",        # default: False
        # "--verbosity",                  # default: 0

        ### Miscellaneous strictness flags
        "--strict-equality",
        # "--allow-untyped-globals",
        # "--local-partial-types",

        # strict mode enables the following flags:
        #     --warn-unused-configs
        #     --disallow-untyped-calls
        #     --disallow-untyped-defs
        #     --disallow-incomplete-defs
        #     --check-untyped-defs
        #     --no-implicit-optional
        #     --warn-redundant-casts
        #     --warn-return-any
        #     --warn-unused-ignores
        #     --disallow-subclassing-any
        #     --disallow-untyped-decorators

        # Advanced options
        # "--show-traceback", # -> fatal error

        # Enabling incomplete/experimental features
        # "--enable-incomplete-feature", # Tuple[int, ...]
    ]

    if not src_path.exists():
        print(f"Error: path '{src_path}' not found ")
        return

    start = time.time()

    name = src_path.stem
    if name == "":
        name = "."

    folder_path = BASE_PATH / RESULT_FOLDER
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    text  = f"Python:   {sys.version.replace(LINEFEET, ' ')}\n"
    text += f"Platform: {platform.platform()}\n"
    text += f"Date:     {datetime.now().astimezone().strftime('%d.%m.%Y %H:%M:%S')}\n"
    text += f"Path:     {BASE_PATH}\n"
    text += "\n"

    text += "MyPy [version] settings:\n"
    text += f" » Python version {python_version}\n"
    for setting in settings:
        text += f" {setting}\n"
    text += "\n"

    config = Path("tmp.toml")
    with Path.open(config, mode="w", newline="\n") as config_file:
        config_file.write(configuration)

    try:
        mypy_path = shutil.which("mypy")
        if mypy_path is None:
            print("Error: 'mypy' not installed -> uv add mypy --dev")
            sys.exit(1)

        result: CompletedProcess[str] = subprocess.run(
            [mypy_path, str(src_path), "--config-file", "tmp.toml", "--verbose", "--output=json", *settings],
            capture_output=True,
            text=True,
            check=False,
        )
        # result: CompletedProcess[str] = subprocess.run(["mypy", str(src_path), "--config-file", "tmp.toml", "--verbose", "--output=json"] + settings, capture_output=True, text=True, check=False)
    except Exception as err:
        print(f"error: {err} - mypy")
        sys.exit(1)
    finally:
        Path.unlink(config)

    # analyse stderr ("--verbose")

    # LOG:  Mypy Version: 1.14.0
    # LOG:  Found source: BuildSource(path='src\\__init__.py', module='__main__', has_text=False, base_dir='G:\\Python\\Whisper\\whisper-datev-gitlab\\src', followed=False)
    # ...
    # LOG:  Metadata fresh for __main__: file src\__init__.py

    codepage = locale.getpreferredencoding() # cp1252 ...
    stderr = result.stderr.encode(encoding=codepage).decode(encoding="utf-8").replace("\xa0", " ")

    sources: List[str] = []
    version = ""
    for line in stderr.splitlines():
        if "Mypy Version:" in line:
            version = line.split("Mypy Version:")[-1].strip()
            text = text.replace("[version]", version)

        if "Found source:" in line:
            pattern = r"path='([^']*)'"
            matches: Match[str] | None = re.search(pattern, line)
            if matches:
                path: str = Path(matches.group(1)).as_posix()
                sources.append(path)
            continue

        if "Metadata fresh for" in line:
            break

    text += "Source files:\n"
    for source in sources:
        text += f" - {source}\n"
    text += "\n"

    # read missing stubs

    mypy_missing_stubs = Path(".mypy_cache") / "missing_stubs"
    if mypy_missing_stubs.exists():
        with Path.open(mypy_missing_stubs, "r") as f:
            lines = f.read()

        text += f"stubs missing -> '{mypy_missing_stubs.as_posix()}'\n"
        for line in lines.splitlines():
            text += f" - uv add {line} --dev\n"

        text += "\n"

    # analyse stdout ("--output=json")

    # {
    #   "file":     "src/utils/prefs.py",
    #   "line":     23,
    #   "column":   0,
    #   "message":  "Library stubs not installed for \"yaml\"",
    #   "hint":     "Hint: \"python3 -m pip install types-PyYAML\"\n(or run \"mypy --install-types\" to install all missing stub packages)",
    #   "code":     "import-untyped",
    #   "severity": "error"
    # }
    # {
    #   "file": "src/utils/metadata.py",
    #   "line": 17,
    #   "column": 0,
    #   "message": "Skipping analyzing \"pymediainfo\": module is installed, but missing library stubs or py.typed marker",
    #   "hint": null,
    #   "code": "import-untyped",
    #   "severity": "error"
    # }

    errors = 0
    error_files = 0
    last_file = ""
    error_types: Counter[str] = Counter()

    for line in result.stdout.splitlines():
        if line == "":
            continue

        data = json.loads(line)
        file = Path(data["file"]).as_posix()

        if last_file != file:
            if last_file != "":
                text += "\n"
            text += "### " + file + " ###\n\n"
            last_file = file
            error_files += 1

        error_type = data["code"]
        error_types[error_type] += 1

        pre = f"{file}:{data["line"]}:{data["column"]+1}" # column 0-based
        text += f"{pre} {data["severity"]}: {data["message"]} [{error_type}]\n"

        if data["hint"] is not None:
            hints = data["hint"].split("\n")
            for hint in hints:
                text += f"{pre}  - {hint}\n"

        errors += 1

    if len(error_types)>0:
        text += "\nError types (sorted)"
        for error_type in error_types.most_common():
            text += f"\n - {error_type[0]}: {error_type[1]}"
        text += "\n\n"

    footer = f"Found {errors} errors in {error_files} files (checked {len(sources)} source files)"
    text += "\n" + footer + "\n"

    result_filename = f"mypy-{python_version}-'{name}'.txt"
    with Path.open(folder_path / result_filename, "w", newline="\n") as file:
        file.write(text)

    duration = time.time() - start
    print(f"[MyPy {version} ({duration:.2f} sec)] {footer} -> {RESULT_FOLDER}/{result_filename}")
    sys.exit(result.returncode)

if __name__ == "__main__":
    parser = ArgumentParser(description="static type check with mypy")
    parser.add_argument("path", nargs="?", type=str, default=".", help="relative path to a file or folder")
    parser.add_argument("-v", "--version", type=str, default="",  help="Python version 3.10/3.11/...")

    args = parser.parse_args()

    try:
        run_mypy(Path(args.path), args.version)
    except KeyboardInterrupt:
        print(" --> KeyboardInterrupt")
        sys.exit(1)
