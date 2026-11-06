"""Connected YouTube channels."""
import webbrowser
from pathlib import Path

import requests
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from desktop.core import db, paths, settings
from desktop.services import youtube
from desktop.ui import icons
from desktop.ui.dashboard import rounded
from desktop.ui.style import badge_style
from desktop.ui.tasks import run_async
from desktop.ui.widgets import link, page_header, section

AVATAR = 56

HELP = ("1. Open " + link("https://console.cloud.google.com/apis/credentials", "Google Cloud → Credentials") +
        " and enable <b>YouTube Data API v3</b> in the same project.<br>"
        "2. Create credentials → OAuth client ID → application type <b>Desktop app</b>.<br>"
        "3. Paste its client ID and secret in <b>Settings → YouTube</b>, then press Connect here.<br>"
        "While the consent screen is in <i>Testing</i>, add your Google account as a test user.")


def avatar_path(channel_id: str) -> Path:
    d = paths.data_dir() / "channels"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{channel_id}.jpg"


def fetch_avatar(channel_id: str, url: str) -> Path:
    out = avatar_path(channel_id)
    res = requests.get(url, timeout=15)
    res.raise_for_status()
    out.write_bytes(res.content)
    return out


class ChannelCard(QFrame):
    def __init__(self, page, ch, uploads: int):
        super().__init__(objectName="storycard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.channel_db_id = ch.id
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(14)

        self.avatar = QLabel(fixedSize=QSize(AVATAR, AVATAR), alignment=Qt.AlignCenter)
        cached = avatar_path(ch.channel_id or str(ch.id))
        if cached.exists():
            self.avatar.setPixmap(rounded(QPixmap(str(cached)), AVATAR, AVATAR // 2))
        else:
            self.avatar.setPixmap(icons.pixmap("youtube", "#f87171", 28))
            self.avatar.setStyleSheet("background:#2a1020; border-radius:28px;")
            if ch.thumbnail and ch.channel_id:
                run_async(fetch_avatar, ch.channel_id, ch.thumbnail, on_done=lambda _: page.refresh())
        lay.addWidget(self.avatar)

        text = QVBoxLayout()
        text.setSpacing(5)
        self.title = QLabel(ch.title or ch.channel_id or "Channel", objectName="cardTitle")
        text.addWidget(self.title)
        row = QHBoxLayout()
        row.setSpacing(8)
        needs = ch.status == "reconnect"
        label, css = badge_style("failed" if needs else "done")
        badge = QLabel("Needs reconnect" if needs else "Connected")
        badge.setStyleSheet(css)
        row.addWidget(badge)
        since = f" · since {ch.created_at:%b %d, %Y}" if ch.created_at else ""
        row.addWidget(QLabel(f"{uploads} video{'s' if uploads != 1 else ''} uploaded{since}", objectName="cardMeta"))
        row.addStretch()
        text.addLayout(row)
        lay.addLayout(text, 1)

        if needs:
            self.reconnect_btn = QPushButton(" Reconnect", objectName="primary", clicked=page._connect)
            self.reconnect_btn.setIcon(icons.icon("refresh", "#ffffff", 15))
            lay.addWidget(self.reconnect_btn)
        if ch.channel_id:
            open_btn = QPushButton("Open on YouTube")
            url = f"https://www.youtube.com/channel/{ch.channel_id}"
            open_btn.clicked.connect(lambda: webbrowser.open(url))
            lay.addWidget(open_btn)
        self.remove_btn = QPushButton(fixedSize=QSize(36, 34), toolTip="Remove from the app")
        self.remove_btn.setIcon(icons.icon("trash", "#f87171", 16))
        self.remove_btn.clicked.connect(lambda: page._remove(self.channel_db_id))
        lay.addWidget(self.remove_btn)


class ChannelsPage(QWidget):
    def __init__(self):
        super().__init__(objectName="page")
        self.cards: list[ChannelCard] = []

        head = page_header("youtube", "YouTube Channels", "Channels your videos can be uploaded to.", "#f87171")
        self.connect_btn = QPushButton(" Connect a channel", objectName="primary", clicked=self._connect)
        self.connect_btn.setIcon(icons.icon("plus", "#ffffff", 16))
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        head.addWidget(self.connect_btn, alignment=Qt.AlignTop)

        panel, pl = section("youtube", "Connected channels", color="#f87171")
        self.count = QLabel(objectName="muted")
        pl.addWidget(self.count)
        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(8)
        self.empty = QLabel("No channels yet. Press “Connect a channel” and sign in with the Google account "
                            "that owns your channel.", objectName="muted", wordWrap=True, alignment=Qt.AlignCenter)
        self.empty.setMinimumHeight(90)
        pl.addWidget(self.empty)
        pl.addLayout(self.list_box)
        self.status = QLabel(objectName="muted", wordWrap=True)
        pl.addWidget(self.status)

        self.help_panel, hl = section("info", "One-time setup", "YouTube needs an OAuth client of type Desktop app.",
                                      "#60a5fa")
        self.help = QLabel(HELP, wordWrap=True, openExternalLinks=True)
        self.help.setTextFormat(Qt.RichText)
        hl.addWidget(self.help)

        inner = QWidget(objectName="formBody")
        il = QVBoxLayout(inner)
        il.setContentsMargins(4, 4, 12, 4)
        il.setSpacing(18)
        il.addWidget(panel)
        il.addWidget(self.help_panel)
        il.addStretch()
        scroll = QScrollArea(widgetResizable=True, frameShape=QFrame.NoFrame)
        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(14)
        root.addLayout(head)
        root.addWidget(scroll, 1)

    def refresh(self):
        has_client = bool(settings.load().get("youtube_client_id"))
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()
        self.cards = []
        with db.Session() as s:
            for ch in s.query(db.Channel).order_by(db.Channel.id):
                uploads = s.query(db.Story).filter(db.Story.channel_id == ch.id,
                                                   db.Story.youtube_video_id.isnot(None)).count()
                card = ChannelCard(self, ch, uploads)
                self.cards.append(card)
                self.list_box.addWidget(card)
        n = len(self.cards)
        self.count.setText(f"{n} channel{'s' if n != 1 else ''} connected")
        self.empty.setVisible(n == 0)
        self.connect_btn.setEnabled(has_client)
        self.connect_btn.setToolTip("" if has_client else "Add the YouTube client ID in Settings first")
        self.help_panel.setVisible(not has_client or n == 0)
        if not has_client:
            self.status.setText("Add your YouTube client ID and secret in Settings → YouTube first.")

    def _connect(self):
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText(" Waiting for browser…")
        self.status.setText("Sign in with Google in the browser tab that just opened.")

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
        self.connect_btn.setText(" Connect a channel")

    def _remove(self, channel_db_id):
        if QMessageBox.question(self, "Remove channel", "Remove this channel from the app? "
                                "Videos already on YouTube are not affected.") != QMessageBox.Yes:
            return
        with db.Session() as s:
            s.delete(s.get(db.Channel, channel_db_id))
            s.commit()
        self.refresh()
