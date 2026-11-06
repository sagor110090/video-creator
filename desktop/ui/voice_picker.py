"""Choose which voice sample a story or schedule is narrated in (default = the one in Settings)."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QPushButton, QWidget

from desktop.core import settings, voices
from desktop.ui import icons

ADD = "__add__"


class VoicePicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(180)
        self.play_btn = QPushButton(fixedSize=QSize(38, 34), toolTip="Preview this voice")
        self.play_btn.setIcon(icons.icon("play", "#60a5fa", 14))
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self._preview)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self.combo, 1)
        lay.addWidget(self.play_btn)
        self._player = QMediaPlayer(self)
        self._out = QAudioOutput(self)
        self._player.setAudioOutput(self._out)
        self._last = 0
        self.combo.currentIndexChanged.connect(self._changed)
        self.reload()

    # ------------------------------------------------------------ data
    def reload(self, select=None):
        """Rebuild the list from Settings + the voice library, keeping (or setting) the selection."""
        keep = select if select is not None else self.value()
        self.combo.blockSignals(True)
        self.combo.clear()
        default = settings.load().get("voice_sample") or ""
        name = voices.display_name(default) if default else "no sample"
        self.combo.addItem(icons.icon("settings", "#8a9bc7", 14), f"Default voice ({name})", None)
        for p in voices.list_samples():
            self.combo.addItem(icons.icon("mic", "#60a5fa", 14), voices.display_name(p), str(p))
        self.combo.insertSeparator(self.combo.count())
        self.combo.addItem(icons.icon("plus", "#c084fc", 14), "Add a voice file…", ADD)
        idx = self.combo.findData(keep) if keep else 0
        self.combo.setCurrentIndex(max(0, idx))
        self._last = self.combo.currentIndex()
        self.combo.blockSignals(False)

    def value(self) -> str | None:
        data = self.combo.currentData() if self.combo.count() else None
        return None if data in (None, ADD) else data

    def set_value(self, path: str | None):
        if path and self.combo.findData(path) < 0 and Path(path).exists():
            self.reload(select=path)          # a sample outside the library still shows up after reload
            if self.combo.findData(path) < 0:
                self.combo.insertItem(1, voices.display_name(path), path)
        self.combo.setCurrentIndex(max(0, self.combo.findData(path)) if path else 0)
        self._last = self.combo.currentIndex()

    # ------------------------------------------------------------ actions
    def _changed(self, index):
        if self.combo.itemData(index) != ADD:
            self._last = index
            return
        path, _ = QFileDialog.getOpenFileName(self, "Voice sample — 10–20 s of clear speech", str(Path.home()),
                                              "Audio (*.wav *.mp3 *.m4a *.flac *.aiff)")
        if not path:
            self.combo.setCurrentIndex(self._last)
            return
        self.reload(select=str(voices.add_sample(path)))

    def _preview(self):
        path = self.value() or settings.load().get("voice_sample")
        if path and Path(path).exists():
            self._player.setSource(QUrl.fromLocalFile(path))
            self._player.play()
