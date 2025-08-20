import os
import sys
from pathlib import Path

# Force isolation from user/system site-packages (e.g., Python 3.13 user site)
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "server.log"

def _log(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

# Ensure Python ignores user site-packages
os.environ.setdefault("PYTHONNOUSERSITE", "1")

# Prefer this project's venv site-packages explicitly and drop foreign ones
venv_candidates = [
    BASE_DIR / ".venv" / "Lib" / "site-packages",  # Windows
    BASE_DIR / "venv" / "Lib" / "site-packages",   # Windows alt
    # Common POSIX layouts (kept for portability)
    BASE_DIR / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
    BASE_DIR / "venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]

venv_site = next((str(p) for p in venv_candidates if p.exists()), None)

if venv_site:
    # Remove paths pointing to unrelated user/system installs (e.g., Python 3.13 from WindowsApps)
    # Keep only venv site, project paths, and stdlib for the current interpreter.
    original_path = list(sys.path)
    block_substrings = (
        "pythonsoftwarefoundation.python.3.13",
        "python313",
        "python\\python313",
        "python.3.13",
        "windowsapps\\pythonsoftwarefoundation",
    )
    filtered = []
    for p in original_path:
        pl = p.lower()
        if any(b in pl for b in block_substrings):
            continue
        if ("site-packages" in p or "dist-packages" in p) and not p.startswith(venv_site):
            # Drop third-party packages not from our venv
            continue
        filtered.append(p)

    # Ensure venv site and project root are at the front
    sys.path = [venv_site]
    if str(BASE_DIR) not in filtered:
        sys.path.append(str(BASE_DIR))
    sys.path.extend([p for p in filtered if p != venv_site])

_log(f"Bootstrap: PY {sys.version}")
_log(f"EXE: {sys.executable}")
_log("sys.path (truncated): " + " | ".join(sys.path[:10]))

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
