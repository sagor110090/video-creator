"""Entry point: desktop/.venv/bin/python -m desktop.main"""
import multiprocessing
import sys


def main():
    multiprocessing.freeze_support()
    from PySide6.QtWidgets import QApplication

    from desktop.core import db, paths, settings
    from desktop.pipeline.worker import recover_interrupted
    from desktop.ui.bridge import WorkerBridge
    from desktop.ui.main_window import MainWindow
    from desktop.ui.style import QSS

    settings.seed_from_env(paths.REPO_ROOT / ".env")
    db.init_db()
    recover_interrupted(db.Session)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Video Creator")
    app.setApplicationDisplayName("AI Video Creator")
    from PySide6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(paths.assets_dir() / "app_icon.png")))   # Dock icon too
    app.setQuitOnLastWindowClosed(False)  # the window may hide to the tray while rendering
    app.setStyleSheet(QSS)
    bridge = WorkerBridge(paths.data_dir())
    bridge.start()
    win = MainWindow(bridge)
    win.show()
    code = app.exec()
    bridge.stop()
    sys.exit(code)


if __name__ == "__main__":
    main()
