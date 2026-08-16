#!/usr/bin/env python
"""Startet die CMDB im Entwicklungsmodus. Aequivalent zu 'npm run start'.

Nutzt bewusst nicht sys.executable, da das Skript sonst vom System-Python
statt vom projekteigenen .venv ausgefuehrt wird, falls jemand einfach
'python start.py' ohne aktiviertes venv aufruft.

FLASK_APP/FLASK_DEBUG kommen aus .flaskenv (von der Flask-CLI automatisch
geladen).
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON_CANDIDATES = [
    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
    PROJECT_ROOT / ".venv" / "bin" / "python",  # Linux/macOS
]


def find_venv_python() -> str:
    for candidate in VENV_PYTHON_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    sys.exit(
        "Kein .venv gefunden. Zuerst einrichten:\n"
        "  python -m venv .venv\n"
        "  .venv/Scripts/pip install -r requirements.txt   (Windows)\n"
        "  .venv/bin/pip install -r requirements.txt        (Linux/macOS)"
    )


def main() -> None:
    subprocess.run([find_venv_python(), "-m", "flask", "run"], check=True)


if __name__ == "__main__":
    main()
