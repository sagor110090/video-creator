"""Build AI Video Creator.app (py2app alias mode: the app runs this project's code and venv).

Run from the repo root:  desktop/.venv/bin/python desktop/packaging/setup_app.py py2app -A
"""
import sys
from pathlib import Path

from setuptools import setup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

setup(
    name="AI Video Creator",
    app=[str(ROOT / "desktop" / "packaging" / "launch.py")],
    options={"py2app": {
        "iconfile": str(ROOT / "desktop" / "assets" / "AppIcon.icns"),
        "plist": {
            "CFBundleName": "AI Video Creator",
            "CFBundleDisplayName": "AI Video Creator",
            "CFBundleIdentifier": "com.sagor.videocreator",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": "Record a voice sample for narration.",
        },
    }},
)
