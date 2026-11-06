from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QMenu,
                               QMessageBox, QPushButton, QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget)

from desktop.core import paths
from desktop.ui.dashboard import DashboardPage
from desktop.ui.settings_page import SettingsPage
from desktop.ui.story_view import StoryView

STATE_TEXT = {"starting": "Starting render worker…", "idle": "Worker idle", "busy": "Rendering…",
              "crashed": "Worker crashed — restarting", "stopped": "Worker stopped"}


class MainWindow(QMainWindow):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.setWindowTitle("AI Video Creator")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        icon = QIcon(str(paths.assets_dir() / "logo.png"))
        self.setWindowIcon(icon)

        self.dashboard = DashboardPage(bridge, open_story=self.open_story)
        self.story_view = StoryView(bridge, back=self.show_dashboard)
        self.settings_page = SettingsPage()
        self.stack = QStackedWidget()
        for w in (self.dashboard, self.story_view, self.settings_page):
            self.stack.addWidget(w)

        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(200)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(12, 16, 12, 16)
        logo = QLabel("VideoAI", objectName="h2")
        sl.addWidget(logo)
        sl.addSpacing(12)
        self.nav = QButtonGroup(self)
        self.nav_buttons = {}
        for key, label, enabled in [("dashboard", "Dashboard", True), ("schedules", "Schedules", False),
                                    ("channels", "YouTube Channels", False), ("statistics", "Statistics", False),
                                    ("settings", "Settings", True)]:
            b = QPushButton(label, objectName="nav", checkable=True, enabled=enabled)
            if not enabled:
                b.setToolTip("Coming in a later phase")
            b.clicked.connect(lambda _=False, k=key: self.show_page(k))
            self.nav.addButton(b)
            self.nav_buttons[key] = b
            sl.addWidget(b)
        sl.addStretch()
        self.worker_label = QLabel(STATE_TEXT["starting"], objectName="muted", wordWrap=True)
        sl.addWidget(self.worker_label)

        root = QWidget()
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(sidebar)
        rl.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.show_page("dashboard")

        bridge.stateChanged.connect(self._on_state)
        bridge.workerCrashed.connect(lambda msg: QMessageBox.warning(self, "Render worker", msg))
        self._tray(icon)

    # ------------------------------------------------------------ navigation
    def show_page(self, key):
        page = {"dashboard": self.dashboard, "settings": self.settings_page}.get(key)
        if page is None:
            return
        self.nav_buttons[key].setChecked(True)
        if page is self.dashboard:
            self.dashboard.refresh()
        if page is self.settings_page:
            self.settings_page.load()
        self.stack.setCurrentWidget(page)

    def show_dashboard(self):
        self.show_page("dashboard")

    def open_story(self, story_id: int):
        self.story_view.show_story(story_id)
        self.nav_buttons["dashboard"].setChecked(True)
        self.stack.setCurrentWidget(self.story_view)

    # ------------------------------------------------------------ worker state / tray
    def _on_state(self, state):
        text = STATE_TEXT.get(state, state)
        if state == "busy" and self.bridge.current_story:
            text = f"Rendering story {self.bridge.current_story}"
        self.worker_label.setText(text)
        self.statusBar().showMessage(text)

    def _tray(self, icon):
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        show = QAction("Show", self, triggered=self._show)
        quit_ = QAction("Quit", self, triggered=self._quit)
        menu.addAction(show)
        menu.addAction(quit_)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("AI Video Creator")
        self.tray.show()
        self._quitting = False

    def _show(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        self._quitting = True
        self.close()

    def closeEvent(self, e):
        if not self._quitting and self.bridge.busy:
            # keep rendering in the background; the tray icon brings the window back
            e.ignore()
            self.hide()
            self.tray.showMessage("AI Video Creator", "Still rendering in the background. Use the tray icon to quit.")
            return
        self.bridge.stop()
        self.tray.hide()
        e.accept()
        QApplication.quit()
