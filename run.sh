#!/bin/zsh
# Run AI Video Creator from the code base (full venv: cloned voice + all features).
cd "$(dirname "$0")"
exec desktop/.venv/bin/python -m desktop.main
