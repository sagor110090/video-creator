"""Settings: API keys, image sources, voice and render options (saved to settings.json)."""
import shutil
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from desktop.core import paths, settings
from desktop.ui import icons
from desktop.ui.widgets import field, link, page_header, secret_edit, section

QUALITY = [("Best", "slow", "Sharpest, slowest"), ("Balanced", "medium", "Good for most videos"),
           ("Fast preview", "veryfast", "Quick drafts")]


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__(objectName="page")
        self.fields: dict[str, QLineEdit] = {}

        # ---- AI writer
        ai, ai_l = section("sparkles", "AI writer", "Writes scripts, image searches and YouTube titles.", "#c084fc")
        self.provider = QComboBox()
        self.provider.addItem("DeepSeek", "deepseek")
        self.provider.addItem("Groq", "groq")
        ai_l.addLayout(field("Provider", self.provider))
        self.fields["deepseek_api_key"] = secret_edit("sk-…")
        ai_l.addLayout(field("DeepSeek API key", self.fields["deepseek_api_key"],
                             link("https://platform.deepseek.com/api_keys", "Get a DeepSeek key")))
        self.fields["groq_api_key"] = secret_edit("gsk_…")
        ai_l.addLayout(field("Groq API key", self.fields["groq_api_key"],
                             link("https://console.groq.com/keys", "Get a free Groq key")))
        ai_l.addStretch()

        # ---- Images
        img, img_l = section("image", "Images", "Free sources, tried in order until one has a match.")
        self.fields["pexels_api_key"] = secret_edit("Optional")
        img_l.addLayout(field("Pexels API key", self.fields["pexels_api_key"],
                              link("https://www.pexels.com/api/", "Free key") + " · best stock photos"))
        self.fields["pixabay_api_key"] = secret_edit("Optional")
        img_l.addLayout(field("Pixabay API key", self.fields["pixabay_api_key"],
                              link("https://pixabay.com/api/docs/", "Free key") + " · no attribution needed"))
        self.fields["pollinations_token"] = secret_edit("Optional")
        img_l.addLayout(field("Pollinations token", self.fields["pollinations_token"],
                              link("https://auth.pollinations.ai", "Free token") + " · removes the AI-image logo"))
        self.image_sources = QLineEdit()
        img_l.addLayout(field("Source order", self.image_sources,
                              "Comma-separated; the first source with a match wins. Sources without a key are skipped."))

        # ---- Voice
        voice, voice_l = section("mic", "Voice", "Narration for every scene.")
        self.voice_engine = QComboBox()
        self.voice_engine.addItem("Chatterbox — clone my voice", "chatterbox")
        self.voice_engine.addItem("Microsoft Edge voices — fast, no cloning", "edge")
        voice_l.addLayout(field("Engine", self.voice_engine))
        sample_box = QFrame(objectName="storycard")
        sample_box.setAttribute(Qt.WA_StyledBackground, True)
        sb = QHBoxLayout(sample_box)
        sb.setContentsMargins(12, 8, 8, 8)
        self.preview_btn = QPushButton(fixedSize=QSize(36, 36), clicked=self._preview, toolTip="Play sample")
        self.preview_btn.setIcon(icons.icon("play", "#60a5fa", 16))
        self.voice_sample = QLabel(objectName="cardTitle")
        sample_text = QVBoxLayout()
        sample_text.setSpacing(0)
        sample_text.addWidget(self.voice_sample)
        sample_text.addWidget(QLabel("10–20 s of clear speech works best", objectName="cardMeta"))
        pick = QPushButton("Choose…", clicked=self._pick_sample)
        sb.addWidget(self.preview_btn)
        sb.addLayout(sample_text, 1)
        sb.addWidget(pick)
        voice_l.addWidget(QLabel("Voice sample", objectName="fieldLabel"))
        voice_l.addWidget(sample_box)
        voice_l.addStretch()

        # ---- Video
        video, video_l = section("film", "Video", "How the final video is put together.")
        self.music = QCheckBox("Add background music")
        video_l.addWidget(self.music)
        video_l.addWidget(QLabel("Render quality", objectName="fieldLabel"))
        q_row = QHBoxLayout()
        self.quality_group = QButtonGroup(self)
        self.quality_buttons = {}
        for label, preset, tip in QUALITY:
            b = QPushButton(label, objectName="pill", checkable=True, toolTip=tip)
            b.setCursor(Qt.PointingHandCursor)
            self.quality_group.addButton(b)
            self.quality_buttons[preset] = b
            q_row.addWidget(b)
        q_row.addStretch()
        video_l.addLayout(q_row)
        video_l.addStretch()

        # ---- YouTube
        yt, yt_l = section("youtube", "YouTube", "OAuth client for connecting channels.", "#f87171")
        self.fields["youtube_client_id"] = QLineEdit(placeholderText="….apps.googleusercontent.com")
        yt_l.addLayout(field("Client ID", self.fields["youtube_client_id"]))
        self.fields["youtube_client_secret"] = secret_edit("GOCSPX-…")
        yt_l.addLayout(field("Client secret", self.fields["youtube_client_secret"],
                             "Create one in " + link("https://console.cloud.google.com/apis/credentials",
                                                     "Google Cloud → Credentials") +
                             " with application type <b>Desktop app</b>."))
        yt_l.addStretch()

        grid = QGridLayout()
        grid.setSpacing(18)
        grid.addWidget(ai, 0, 0)
        grid.addWidget(img, 0, 1)
        grid.addWidget(voice, 1, 0)
        grid.addWidget(video, 1, 1)
        grid.addWidget(yt, 2, 0, 1, 2)
        inner = QWidget(objectName="formBody")
        il = QVBoxLayout(inner)
        il.setContentsMargins(4, 4, 12, 4)
        il.addLayout(grid)
        il.addStretch()
        scroll = QScrollArea(widgetResizable=True, frameShape=QFrame.NoFrame)
        scroll.setWidget(inner)

        head = page_header("settings", "Settings", "Keys and preferences are stored only on this Mac.")
        self.saved = QLabel(objectName="muted")
        self.save_btn = QPushButton(" Save changes", objectName="primary", clicked=self.save)
        self.save_btn.setIcon(icons.icon("save", "#ffffff", 16))
        self.save_btn.setCursor(Qt.PointingHandCursor)
        head.addWidget(self.saved)
        head.addWidget(self.save_btn, alignment=Qt.AlignTop)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(14)
        root.addLayout(head)
        root.addWidget(scroll, 1)

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
        self.voice_sample.setText(Path(self._sample_path).name if self._sample_path else "No sample — default voice")
        self.music.setChecked(bool(cfg["background_music"]))
        self.quality_buttons.get(cfg["render_preset"], self.quality_buttons["slow"]).setChecked(True)
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
        cfg["render_preset"] = next((p for p, b in self.quality_buttons.items() if b.isChecked()), "slow")
        settings.save(cfg)
        self.saved.setText("Saved · applies to the next render")

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
