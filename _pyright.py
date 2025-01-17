# python _pyright.py src
# uv run _pyright.py src

# install pyright: npm install --global pyright

import sys
import subprocess
import platform
import json
import os
import shutil

from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

def run_pyright(target_file: str) -> None:

    settings = {
        "reportMissingImports": "warning",
        "reportPossiblyUnboundVariable": "none",

        # strict
        "reportMissingTypeStubs": True,
        "reportOptionalSubscript": True,
        "reportOptionalMemberAccess": True,
        "reportOptionalCall": True,
        "reportOptionalIterable": True,
        "reportOptionalContextManager": True,
        "reportOptionalOperand": True,
        "reportUntypedFunctionDecorator": True,
        "reportUntypedClassDecorator": True,
        "reportUntypedBaseClass": True,
        "reportUntypedNamedTuple": True,
        "reportFunctionMemberAccess": True,
        "reportPrivateUsage": True,
        "reportUnusedImport": True,
        "reportUnusedClass": True,
        "reportUnusedFunction": True,
        "reportUnusedVariable": True,
        "reportDuplicateImport": True,
        "reportUnnecessaryTypeIgnoreComment": True,
    }

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: '{filepath}' not found ")
        return

    folder_path = BASE_PATH / RESULT_FOLDER
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    name = filepath.stem

    npx_path = shutil.which("npx")
    if not npx_path:
        print("Error: 'npx' not found")
        return

    text =  f"Python:   {sys.version}\n"
    text += f"Platform: {platform.platform()}\n"
    text += f"Date:     {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n"
    text += f"Path:     {BASE_PATH}\n"
    text += "\n"

    text += "PyRight settings:\n"
    for key, value in settings.items():
        text += f" - {key}: {value}\n"

    config = "tmp.json"
    with open(config, "w") as config_file:
        json.dump(settings, config_file)

    try:
        result = subprocess.run([npx_path, "pyright", target_file, "--project", config], capture_output=True, text=True, shell=True)
    finally:
        os.remove(config)

    path = str(BASE_PATH)[0].lower() + str(BASE_PATH)[1:]

    stdout = result.stdout.encode("cp1252").decode("utf-8")
    summary = "no summary"
    for line in stdout.splitlines():
        if line.startswith("  "):
            if path in line:
                text += line[3 + len(str(BASE_PATH)):] + "\n"
            else:
                text += " - " + line[4:] + "\n"
        else:
            if "informations" in line:
                summary = line.strip()
                text += f"\n{summary}\n"
            else:
                text += "\n"

    with open(folder_path / f"pyright-{name}.txt", "w") as file:
        file.write(text)

    print(f"[PyRight] {target_file}: {summary} -> {RESULT_FOLDER}/pyright-{name}.txt")

    sys.exit(result.returncode)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: __pyright.py <target_file>")
        sys.exit(1)

    run_pyright(sys.argv[1])
