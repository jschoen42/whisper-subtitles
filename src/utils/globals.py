"""
    © Jürgen Schoenemeyer, 22.02.2025

    src/utils/globals.py

    PUBLIC:
     - DRIVE: Path
     - BASE_PATH: Path
     - SYSTEM_ENV_PATHS: List[str]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

DRIVE: Path     = Path(Path(__file__).drive)
BASE_PATH: Path = Path(sys.argv[0]).parent.parent

system_paths = os.getenv("PATH")
if system_paths is None:
    system_paths = ""

if system_paths[-1:] == ";":
    system_paths = system_paths[:-1]

SYSTEM_ENV_PATHS: List[str] = system_paths.split(";")
