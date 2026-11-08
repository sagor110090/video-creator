"""Build the standalone (exportable) AI Video Creator.app — works on other Macs.

Run from the repo root:  desktop/.venv/bin/python desktop/packaging/setup_exportable.py py2app
Output: dist/AI Video Creator.app (arm64). Requires desktop/packaging/bin/{ffmpeg,ffprobe}
(arm64 static builds) — see the README note in packaging/.

Note: the standalone bundle leaves out the Chatterbox voice-clone stack (torch, ~2 GB).
Scenes then narrate with Edge voices. For your cloned voice, run from the code base instead:
./run.sh  (or the alias build: setup_app.py py2app -A), which uses desktop/.venv.
"""
import shutil
import sys
import tempfile
from pathlib import Path

from setuptools import setup

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parents[1]          # the desktop/ package
BIN = Path(__file__).resolve().parent / "bin"

# Stage a clean copy of the package: the real desktop/ also holds .venv/, tests/ and caches,
# which py2app would blindly copy into the bundle (and then die rewriting nested .so headers).
STAGE_PARENT = Path(tempfile.mkdtemp(prefix="vc_stage_"))
STAGE = STAGE_PARENT / "desktop"
STAGE.mkdir(parents=True)
for item in ("__init__.py", "main.py", "cli.py", "core", "pipeline", "services", "ui", "assets"):
    src, dst = PKG / item, STAGE / item
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        shutil.copy2(src, dst)
sys.path.insert(0, str(STAGE_PARENT))

setup(
    name="AI Video Creator",
    app=[str(Path(__file__).resolve().parent / "launch_exportable.py")],
    data_files=[("bin", [str(BIN / "ffmpeg"), str(BIN / "ffprobe")])],
    options={"py2app": {
        "dist_dir": str(ROOT / "dist"),
        "iconfile": str(ROOT / "desktop" / "assets" / "AppIcon.icns"),
        "plist": {
            "CFBundleName": "AI Video Creator",
            "CFBundleDisplayName": "AI Video Creator",
            "CFBundleIdentifier": "com.sagor.videocreator",
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleVersion": "2",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": "Record a voice sample for narration.",
        },
        # whole-package copies (data files like fonts/music/icons travel with them)
        "packages": ["desktop", "PySide6", "edge_tts", "readability", "lxml", "selectolax",
                     "googlenewsdecoder", "PIL", "requests", "certifi"],
        # the Chatterbox voice-clone stack is ~3 GB; voice falls back to Edge TTS without it
        "excludes": ["torch", "chatterbox_tts", "chatterbox", "perth", "transformers", "tokenizers",
                     "safetensors", "numpy", "scipy", "huggingface_hub", "desktop.tests",
                     "pytest", "responses", "tkinter", "matplotlib", "IPython", "pandas"],
    }},
)
