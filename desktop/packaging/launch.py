"""Entry point used by AI Video Creator.app (py2app alias build).

The bundle only provides the app identity (name, icon, Dock); the code and libraries come from this
project and its venv. Two fixes make that work:
- py2app marks the process as "frozen", which makes multiprocessing launch the render worker with
  '--multiprocessing-fork' (a frozen-app convention plain Python rejects). Alias builds are not frozen,
  so drop the flag and point multiprocessing at the venv's Python.
- py2app also adds the base Homebrew site-packages; keep only the venv's so library versions match.
"""
import multiprocessing
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV = ROOT / "desktop" / ".venv"
VENV_PYTHON = VENV / "bin" / "python"
VENV_SITE = VENV / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

if getattr(sys, "frozen", None):
    del sys.frozen
sys.path[:] = [p for p in sys.path if not (p.startswith("/opt/homebrew/lib/") and "site-packages" in p)]
for extra in (str(VENV_SITE), str(ROOT)):
    if extra not in sys.path:
        sys.path.insert(0, extra)
os.chdir(ROOT)

if __name__ == "__main__":
    multiprocessing.set_executable(str(VENV_PYTHON))
    multiprocessing.freeze_support()
    from desktop.main import main
    main()
