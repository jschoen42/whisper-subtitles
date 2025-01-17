# python _mypy.py src/main.py
# uv run _mypy.py src/main.py

import sys
import subprocess
import platform

from typing import List
from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

def run_mypy() -> None:

    # https://mypy.readthedocs.io/en/stable/command_line.html
    # https://gist.github.com/Michael0x2a/36c5948a7ea571b722686226639b0859

    settings: List[str] = [
        # Incremental mode
        "--sqlite-cache",

        # Untyped definitions and calls
        "--disallow-untyped-calls",
        "--disallow-untyped-defs",
        "--disallow-untyped-decorators",
        "--disallow-incomplete-defs",

        # Configuring warnings
        "--warn-redundant-casts",
        "--warn-unused-ignores",
        "--warn-unreachable",

        # Configuring error messages
        # "--show-error-context"
        # "--show-column-numbers",
        # "--show-error-code-links".
        # "--show-error-end",
        # "--pretty",
        "--force-uppercase-builtins",

        # Miscellaneous strictness flags
        "--strict-equality",
        # "--allow-untyped-globals",
        "--allow-redefinition",
        # "--local-partial-types",
        # "--strict",

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

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: '{filepath}' not found ")
        return

    name = filepath.stem

    folder_path = BASE_PATH / RESULT_FOLDER
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    text =  f"Python:   {sys.version}\n"
    text += f"Platform: {platform.platform()}\n"
    text += f"Date:     {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n"
    text += f"Path:     {BASE_PATH}\n"
    text += "\n"

    text += "MyPy settings:\n"
    for setting in settings:
        text += f" {setting}\n"

    text += "\n"

    result = subprocess.run(["mypy"] + (settings + sys.argv[1:]), capture_output=True, text=True)

    summary = ""
    current_file = None
    for line in result.stdout.splitlines():
        if line.startswith("Found") or line.startswith("Success"):
            summary = line.strip()
        if line and not line.startswith(" "):
            file_path = line.split(":")[0]
            if file_path != current_file:
                if current_file is not None:
                    text += "\n"
                current_file = file_path

        text += f"{line}\n"

    with open(folder_path / f"mypy-{name}.txt", "w") as file:
        file.write(text)

    print(f"[MyPy] {sys.argv[1:][0]}: {summary} -> {RESULT_FOLDER}/mypy-{name}.txt")
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_mypy()
