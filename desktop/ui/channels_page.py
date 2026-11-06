"""Connected YouTube channels."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from desktop.core import db, settings
from desktop.services import youtube
from desktop.ui.tasks import run_async

HELP = """<b>One-time setup:</b> YouTube needs an OAuth client of type <b>Desktop app</b>.<br>
1. Open <a style="color:#22d3ee" href="https://console.cloud.google.com/apis/credentials">Google Cloud Console → Credentials</a>
(enable <i>YouTube Data API v3</i> in the same project).<br>
2. Create credentials → OAuth client ID → Application type <b>Desktop app</b>.<br>
3. Paste its Client ID and Client secret in <b>Settings</b>, then come back and press Connect.<br>
While the app is in Google's "Testing" mode, add your Google account as a test user on the OAuth consent screen."""


class ChannelsPage(QWidget):
    def __init__(self):
        super().__init__(objectName="page")
        self.list = QListWidget()
        self.connect_btn = QPushButton("Connect a channel", objectName="primary", clicked=self._connect)
        self.remove_btn = QPushButton("Remove", clicked=self._remove)
        self.status = QLabel(objectName="muted", wordWrap=True)
        self.help = QLabel(HELP, wordWrap=True, openExternalLinks=True)
        bar = QHBoxLayout()
        bar.addWidget(self.connect_btn)
        bar.addWidget(self.remove_btn)
        bar.addStretch()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.addWidget(QLabel("YouTube Channels", objectName="h1"))
        root.addWidget(self.list, 1)
        root.addLayout(bar)
        root.addWidget(self.status)
        root.addWidget(self.help)

    def refresh(self):
        has_client = bool(settings.load().get("youtube_client_id"))
        self.connect_btn.setEnabled(has_client)
        self.help.setVisible(not has_client or self.list.count() == 0)
        self.list.clear()
        with db.Session() as s:
            for ch in s.query(db.Channel).order_by(db.Channel.id):
                state = "⚠ needs reconnect" if ch.status == "reconnect" else "connected"
                uploads = s.query(db.Story).filter(db.Story.channel_id == ch.id,
                                                   db.Story.youtube_video_id.isnot(None)).count()
                item = QListWidgetItem(f"{ch.title or ch.channel_id}\n      {state} · {uploads} videos uploaded")
                item.setData(Qt.UserRole, ch.id)
                self.list.addItem(item)
        self.help.setVisible(not has_client or self.list.count() == 0)
        if not has_client:
            self.status.setText("Add your YouTube OAuth Client ID in Settings first.")

    def _connect(self):
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Waiting for browser…")
        self.status.setText("Sign in with Google in the browser window that just opened.")

        def done(_):
            self._reset()
            self.status.setText("Channel connected.")
            self.refresh()

        def failed(e):
            self._reset()
            self.status.setText(f"Could not connect: {e}")

        run_async(youtube.connect_channel, settings.load(), db.Session, on_done=done, on_error=failed)

    def _reset(self):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect a channel")

    def _remove(self):
        item = self.list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Remove channel", "Remove this channel from the app? "
                                "Videos already on YouTube are not affected.") != QMessageBox.Yes:
            return
        with db.Session() as s:
            s.delete(s.get(db.Channel, item.data(Qt.UserRole)))
            s.commit()
        self.refresh()
