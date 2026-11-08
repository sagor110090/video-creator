"""Entry point for the standalone (exportable) AI Video Creator.app build.

Unlike the alias build, everything the app needs is inside the bundle (Python, Qt, deps,
static ffmpeg/ffprobe). Only the Chatterbox voice-clone stack is excluded for size; the voice
pipeline then falls back to Microsoft Edge voices automatically.

The __main__ guard matters: spawn-mode workers re-import this module as __mp_main__, and must
not boot the GUI again. freeze_support() runs the worker instead when the app binary is
relaunched with multiprocessing's frozen flag."""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from desktop.main import main
    main()
