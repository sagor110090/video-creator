"""Shared building blocks for the Dark Blue pages."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from desktop.core import characters
from desktop.ui import icons
from desktop.ui.style import MUTED, glow


def icon_label(name, color="#60a5fa", size=16):
    lbl = QLabel()
    lbl.setPixmap(icons.pixmap(name, color, size))
    lbl.setFixedSize(size + 2, size + 2)
    return lbl


def page_header(icon_name, title, subtitle="", color="#dbe4ff"):
    """Big page title row with an icon and a muted subtitle."""
    row = QHBoxLayout()
    row.setSpacing(12)
    row.addWidget(icon_label(icon_name, color, 26), alignment=Qt.AlignTop)
    text = QVBoxLayout()
    text.setSpacing(2)
    text.addWidget(QLabel(title, objectName="h1"))
    if subtitle:
        sub = QLabel(subtitle, objectName="muted", wordWrap=True)
        text.addWidget(sub)
    row.addLayout(text, 1)
    return row


def section(icon_name, title, subtitle="", color="#60a5fa", glowing=True):
    """A glowing panel with an icon title. Returns (frame, body_layout)."""
    frame = QFrame(objectName="panel")
    frame.setAttribute(Qt.WA_StyledBackground, True)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 16, 18, 18)
    lay.setSpacing(10)
    head = QHBoxLayout()
    head.setSpacing(10)
    head.addWidget(icon_label(icon_name, color, 20))
    t = QVBoxLayout()
    t.setSpacing(0)
    t.addWidget(QLabel(title, objectName="panelTitle"))
    if subtitle:
        t.addWidget(QLabel(subtitle, objectName="muted", wordWrap=True))
    head.addLayout(t, 1)
    lay.addLayout(head)
    if glowing:
        glow(frame, radius=26, alpha=90)
    return frame, lay


def field(label, widget, hint=""):
    """Label above a field, optional muted hint (may contain links) below it."""
    box = QVBoxLayout()
    box.setSpacing(5)
    box.addWidget(QLabel(label, objectName="fieldLabel"))
    box.addWidget(widget)
    if hint:
        h = QLabel(hint, objectName="muted", wordWrap=True, openExternalLinks=True)
        box.addWidget(h)
    return box


def secret_edit(placeholder="") -> QLineEdit:
    """Password-style line edit with an eye toggle to reveal the value."""
    e = QLineEdit(echoMode=QLineEdit.Password, placeholderText=placeholder)
    action = e.addAction(icons.icon("eye", MUTED, 16), QLineEdit.TrailingPosition)
    action.setToolTip("Show / hide")

    def toggle():
        e.setEchoMode(QLineEdit.Normal if e.echoMode() == QLineEdit.Password else QLineEdit.Password)
    action.triggered.connect(toggle)
    return e


def link(url, text):
    return f'<a style="color:#60a5fa; text-decoration:none" href="{url}">{text}</a>'


IMAGE_SOURCES = [("free", "Free sources"), ("gemini", "Gemini (paid)"), ("openrouter", "OpenRouter (paid)")]


def image_source_combo(default_label: str = "Default") -> "QComboBox":
    """Free / Gemini / OpenRouter picker. Data '' means 'use the default' (Settings, or the story's choice)."""
    from PySide6.QtWidgets import QComboBox
    combo = QComboBox()
    combo.addItem(icons.icon("settings", "#8a9bc7", 14), default_label, "")
    for key, label in IMAGE_SOURCES:
        combo.addItem(icons.icon("sparkles" if key != "free" else "image",
                                 "#c084fc" if key != "free" else "#60a5fa", 14), label, key)
    return combo


def settings_source_label() -> str:
    from desktop.core import settings
    provider = settings.load().get("image_provider", "free")
    return f"Default · {dict(IMAGE_SOURCES).get(provider, 'Free sources')}"


class CharacterPicker(QFrame):
    """Optional per-video character: one clear face photo, kept in every AI-generated scene."""

    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 4, 4)
        row.setSpacing(8)
        self._path = None
        self.thumb = QLabel(fixedSize=QSize(30, 30), alignment=Qt.AlignCenter)
        self.thumb.setStyleSheet("border:1px solid #1a2d63; border-radius:8px; background:#0b1430;")
        self.label = QLabel("None", objectName="cardMeta")
        pick = QPushButton("Choose…", clicked=self._pick)
        self.clear_btn = QPushButton("✕", flat=True, cursor=Qt.PointingHandCursor, toolTip="No character")
        self.clear_btn.setStyleSheet("color:#8a9bc7; font-weight:700; border:none; padding:2px 6px;")
        self.clear_btn.clicked.connect(lambda: self.setValue(""))
        row.addWidget(self.thumb)
        row.addWidget(self.label, 1)
        row.addWidget(self.clear_btn)
        row.addWidget(pick)

    def value(self) -> str | None:
        return self._path

    def setValue(self, path: str):
        self._path = path or None
        name = Path(path).name if path else ""
        self.label.setText(name or "None")
        self.clear_btn.setVisible(bool(path))
        pix = QPixmap(path) if path else QPixmap()
        self.thumb.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                             if not pix.isNull() else QPixmap())

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "Character image (one clear face photo)",
                                              str(Path.home()),
                                              "Images (*.jpg *.jpeg *.png *.webp)")
        if not path:
            return
        try:
            self.setValue(str(characters.add_image(path)))
        except OSError as e:                      # never die silently inside a Qt slot
            self.label.setText(f"Couldn't load image: {e}")
