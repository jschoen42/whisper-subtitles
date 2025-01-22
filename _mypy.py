# python _mypy.py src/main.py

import re
import sys
import subprocess
import platform
import time

from typing import List
from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

def run_mypy(target_file: str) -> None:

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
        # "--warn-unused-ignores",
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

    start = time.time()

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

    text += "MyPy [version] settings:\n"
    for setting in settings:
        text += f" {setting}\n"
    text += "\n"

    result = subprocess.run(["mypy", target_file, "--verbose"] + settings, capture_output=True, text=True)
    # if result.returncode == 2:
    #     print("error: ", result.stderr)
    #     sys.exit(2)

    # "--verbose" -> stderr

    sources = []
    version = ""
    for line in result.stderr.splitlines():
        if "Mypy Version:" in line:
            version = line.split("Mypy Version:")[-1].strip()
            text = text.replace("[version]", version)

        if "Found source:" in line:
            pattern = r"path='([^']*)'"
            matches = re.search(pattern, line)
            if matches:
                path = matches.group(1).replace("\\\\", "/")
                # if not path.endswith("__init__.py"):
                sources.append(path)
            continue

        # if "Build finished" in line:
        #     pattern = r"finished in ([\d\.]+) seconds.*with (\d+) modules"
        #     matches = re.search(pattern, line)
        #     if matches:
        #         seconds = matches.group(1)
        #         modules = matches.group(2)

    text += "Source files:\n"
    for source in sources:
        text += f" - {source}\n"
    text += "\n"

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

    duration = time.time() - start
    print(f"[MyPy {version} ({duration:.2f} sec)] {sys.argv[1:][0]}: {summary} -> {RESULT_FOLDER}/mypy-{name}.txt")
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_mypy(sys.argv[1])
