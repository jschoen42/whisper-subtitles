# python __mypy.py > __mypy-result-00.txt

import sys
import subprocess
import platform

from typing import List
from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()

def run_mypy() -> None:

    settings: List[str] = [
        "--disallow-untyped-calls",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs",
        "--disallow-untyped-decorators",

        "--warn-redundant-casts",
        "--warn-unused-ignores",
        "--warn-unreachable",

        "--sqlite-cache",
    ]

    filepath = Path(sys.argv[1]).stem

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

    current_file = None
    for line in result.stdout.splitlines():
        if line and not line.startswith(" "):
            file_path = line.split(":")[0]
            if file_path != current_file:
                if current_file is not None:
                    text += "\n"
                current_file = file_path

        text += f"{line}\n"

    with open(f"__mypy-{filepath}.txt", "w") as file:
        file.write(text)

    sys.exit(result.returncode)

if __name__ == "__main__":
    run_mypy()