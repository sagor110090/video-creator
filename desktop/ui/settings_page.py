"""Settings: API keys, image sources, voice and render options (saved to settings.json)."""
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout, QWidget)

from desktop.core import paths, settings

KEY_FIELDS = [("deepseek_api_key", "DeepSeek API key"), ("groq_api_key", "Groq API key"),
              ("pexels_api_key", "Pexels API key (free)"), ("pixabay_api_key", "Pixabay API key (free)"),
              ("pollinations_token", "Pollinations token (optional)")]


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__(objectName="page")
        card = QFrame(objectName="card")
        form = QFormLayout(card)
        form.setLabelAlignment(Qt.AlignRight)

        self.provider = QComboBox()
        self.provider.addItem("DeepSeek", "deepseek")
        self.provider.addItem("Groq", "groq")
        form.addRow("AI writer", self.provider)
        self.fields = {}
        for key, label in KEY_FIELDS:
            f = QLineEdit(echoMode=QLineEdit.Password)
            self.fields[key] = f
            form.addRow(label, f)
        self.image_sources = QLineEdit()
        self.image_sources.setToolTip("Tried in order: pexels, pixabay, openverse, pollinations, loremflickr")
        form.addRow("Image source order", self.image_sources)

        self.voice_engine = QComboBox()
        self.voice_engine.addItem("Chatterbox — clone my voice", "chatterbox")
        self.voice_engine.addItem("Microsoft Edge voices (fast, no cloning)", "edge")
        form.addRow("Voice", self.voice_engine)
        sample_row = QHBoxLayout()
        self.voice_sample = QLabel(objectName="muted")
        pick = QPushButton("Choose…", clicked=self._pick_sample)
        self.preview_btn = QPushButton("▶", fixedWidth=36, clicked=self._preview)
        sample_row.addWidget(self.voice_sample, 1)
        sample_row.addWidget(pick)
        sample_row.addWidget(self.preview_btn)
        form.addRow("Voice sample", sample_row)

        self.music = QCheckBox("Add background music")
        form.addRow("", self.music)
        self.quality = QComboBox()
        for label, preset in [("Best (slow)", "slow"), ("Balanced", "medium"), ("Fast preview", "veryfast")]:
            self.quality.addItem(label, preset)
        form.addRow("Render quality", self.quality)

        self.saved = QLabel(objectName="muted")
        self.save_btn = QPushButton("Save", objectName="primary", clicked=self.save)
        bottom = QHBoxLayout()
        bottom.addWidget(self.saved)
        bottom.addStretch()
        bottom.addWidget(self.save_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.addWidget(QLabel("Settings", objectName="h1"))
        root.addWidget(card)
        root.addLayout(bottom)
        root.addStretch()
        self._player = QMediaPlayer(self)
        self._out = QAudioOutput(self)
        self._player.setAudioOutput(self._out)
        self._sample_path = ""

    def load(self):
        cfg = settings.load()
        self.provider.setCurrentIndex(max(0, self.provider.findData(cfg["ai_provider"])))
        for key, f in self.fields.items():
            f.setText(cfg.get(key, ""))
        self.image_sources.setText(cfg["image_sources"])
        self.voice_engine.setCurrentIndex(max(0, self.voice_engine.findData(cfg["voice_engine"])))
        self._sample_path = cfg.get("voice_sample", "")
        self.voice_sample.setText(Path(self._sample_path).name if self._sample_path else "none — default voice")
        self.music.setChecked(bool(cfg["background_music"]))
        self.quality.setCurrentIndex(max(0, self.quality.findData(cfg["render_preset"])))
        self.saved.clear()

    def save(self):
        cfg = settings.load()
        cfg["ai_provider"] = self.provider.currentData()
        for key, f in self.fields.items():
            cfg[key] = f.text().strip()
        cfg["image_sources"] = ",".join(s.strip() for s in self.image_sources.text().split(",") if s.strip())
        cfg["voice_engine"] = self.voice_engine.currentData()
        cfg["voice_sample"] = self._sample_path
        cfg["background_music"] = self.music.isChecked()
        cfg["render_preset"] = self.quality.currentData()
        settings.save(cfg)
        self.saved.setText("Saved. New settings apply to the next render.")

    def _pick_sample(self):
        path, _ = QFileDialog.getOpenFileName(self, "Voice sample (10–20 s of clear speech)", str(Path.home()),
                                              "Audio (*.wav *.mp3 *.m4a)")
        if not path:
            return
        dest = paths.data_dir() / "voice" / f"sample{Path(path).suffix.lower()}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, dest)
        self._sample_path = str(dest)
        self.voice_sample.setText(Path(path).name)

    def _preview(self):
        if self._sample_path:
            self._player.setSource(QUrl.fromLocalFile(self._sample_path))
            self._player.play()
