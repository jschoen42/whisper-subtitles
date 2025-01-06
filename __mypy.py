# python __mypy.py > __mypy-result-00.txt

import sys
import subprocess
import platform

from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()

def run_mypy():

    settings = [
        "--disallow-untyped-calls",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs",

        "src/main.py"
    ]

    print(f"Python:   {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Date:     {datetime.now()}")
    print(f"Path:     {BASE_PATH}")
    print()

    result = subprocess.run(["mypy"] + (settings + sys.argv[1:]), capture_output=True, text=True)

    current_file = None
    for line in result.stdout.splitlines():
        if line and not line.startswith(" "):
            file_path = line.split(":")[0]
            if file_path != current_file:
                if current_file is not None:
                    print()
                current_file = file_path

        print(line)

    sys.exit(result.returncode)

if __name__ == "__main__":
    run_mypy()