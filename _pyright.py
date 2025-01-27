# python _pyright.py src

# install: npm install --global pyright
# update: npm update --global pyright

import os
import sys
import subprocess
import platform
import json
import shutil
import time

from pathlib import Path
from datetime import datetime

BASE_PATH = Path(sys.argv[0]).parent.parent.resolve()
RESULT_FOLDER = ".type-check-result"

# {
#     "exclude": [
#         "path/to/exclude"
#     ]
# }

def run_pyright(target_file: str) -> None:

    # https://microsoft.github.io/pyright/#/configuration?id=diagnostic-settings-defaults

    settings = {
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
            "src/faster_whisper/*",
            "src/extras/*",
        ]
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

    text += "PyRight [version] settings:\n"
    for key, value in settings.items():
        text += f" - {key}: {value}\n"

    config = "tmp.json"
    with open(config, "w") as config_file:
        json.dump(settings, config_file, indent=2)

    start = time.time()
    try:
        result = subprocess.run([npx_path, "pyright", target_file, "--verbose", "--project", config], capture_output=True, text=True, shell=True)
    finally:
        os.remove(config)

    if result.returncode == 2:
        print(f"errorcode: {result.returncode}")
        print(result.stderr)
        sys.exit(result.returncode)

    stdout = result.stdout.encode("cp1252").decode("utf-8").replace("\xa0", " ")

    path = str(BASE_PATH)[0].lower() + str(BASE_PATH)[1:]
    version = ""
    num_files = 0
    summary = "no summary"

    verbose_info = False
    for line in stdout.splitlines():
        if line.startswith("Loading configuration"):
            verbose_info = True
            continue

        if line.startswith("pyright"):
            version = line.split(" ")[1]
            text = text.replace("[version]", version)
            verbose_info = False
            continue

        if verbose_info:
            # print( "****", line )

            if "Found" in line:
                num_files = int(line.split(" ")[1])
            continue

        if line.startswith("  "):
            if path in line:
                text += line[3 + len(str(BASE_PATH)):] + "\n"
            else:
                text += " - " + line[4:] + "\n"
        else:
            if "informations" in line:
                summary = line.strip()
                text += f"\n'{target_file}' {num_files} source file(s): {summary}"

            text += "\n"

    with open(folder_path / f"pyright-{name}.txt", "w") as file:
        file.write(text)

    duration = time.time() - start
    print(f"[PyRight {version} ({duration:.2f} sec)] '{target_file}' - {num_files} source file(s): {summary} -> {RESULT_FOLDER}/pyright-{name}.txt")

    sys.exit(result.returncode)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: _pyright.py <target_file>")
        sys.exit(1)

    run_pyright(sys.argv[1])
