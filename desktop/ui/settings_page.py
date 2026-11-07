"""Settings: API keys, image sources, voice and render options (saved to settings.json)."""
import subprocess
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from desktop.core import db, settings, voices
from desktop.pipeline import export
from desktop.pipeline.images import GEMINI_MODELS, OPENROUTER_MODELS
from desktop.ui import icons
from desktop.ui.tasks import run_async
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
        self.provider.addItem("OpenRouter", "openrouter")
        ai_l.addLayout(field("Provider", self.provider))
        self.fields["channel_name"] = QLineEdit(placeholderText="e.g. The 60s Lab (optional)")
        ai_l.addLayout(field("Channel name", self.fields["channel_name"],
                             "The writer may mention it once near the end. Never used in kids stories."))
        self.fields["openrouter_text_model"] = QLineEdit(placeholderText="deepseek/deepseek-chat-v3.1")
        ai_l.addLayout(field("OpenRouter writer model", self.fields["openrouter_text_model"],
                             "Used when Provider is OpenRouter. Shares the OpenRouter key from Images."))
        self.fields["deepseek_text_model"] = QLineEdit(placeholderText="deepseek-chat")
        ai_l.addLayout(field("DeepSeek writer model", self.fields["deepseek_text_model"],
                             "Blank = deepseek-chat (fast). deepseek-v4-pro writes stronger scripts."))
        self.fields["deepseek_api_key"] = secret_edit("sk-…")
        ai_l.addLayout(field("DeepSeek API key", self.fields["deepseek_api_key"],
                             link("https://platform.deepseek.com/api_keys", "Get a DeepSeek key")))
        self.fields["groq_api_key"] = secret_edit("gsk_…")
        ai_l.addLayout(field("Groq API key", self.fields["groq_api_key"],
                             link("https://console.groq.com/keys", "Get a free Groq key")))
        ai_l.addStretch()

        # ---- Images
        img, img_l = section("image", "Images", "Where scene images come from.")
        img_l.addWidget(QLabel("Image source", objectName="fieldLabel"))
        prov = QHBoxLayout()
        self.provider_group = QButtonGroup(self)
        self.provider_free = QPushButton(" Free sources", objectName="pill", checkable=True)
        self.provider_free.setIcon(icons.icon("image", "#dbe4ff", 15))
        self.provider_gemini = QPushButton(" Gemini (paid)", objectName="pill", checkable=True)
        self.provider_gemini.setIcon(icons.icon("sparkles", "#c084fc", 15))
        self.provider_openrouter = QPushButton(" OpenRouter (paid)", objectName="pill", checkable=True)
        self.provider_openrouter.setIcon(icons.icon("sparkles", "#60a5fa", 15))
        for b in (self.provider_free, self.provider_gemini, self.provider_openrouter):
            b.setCursor(Qt.PointingHandCursor)
            self.provider_group.addButton(b)
            prov.addWidget(b)
        prov.addStretch()
        img_l.addLayout(prov)

        self.gemini_box = QFrame(objectName="storycard")
        self.gemini_box.setAttribute(Qt.WA_StyledBackground, True)
        gl = QVBoxLayout(self.gemini_box)
        gl.setContentsMargins(12, 10, 12, 12)
        gl.setSpacing(8)
        self.fields["gemini_api_key"] = secret_edit("AIza…")
        gl.addLayout(field("Gemini API key", self.fields["gemini_api_key"],
                           link("https://aistudio.google.com/apikey", "Get a key in Google AI Studio") +
                           " · image generation is billed per image"))
        self.gemini_model = QComboBox()
        for model_id, label in GEMINI_MODELS.items():
            self.gemini_model.addItem(label, model_id)
        gl.addLayout(field("Model", self.gemini_model))
        gl.addWidget(QLabel("Image size", objectName="fieldLabel"))
        size_row = QHBoxLayout()
        self.size_group = QButtonGroup(self)
        self.size_buttons = {}
        for size, tip in (("1K", "Cheapest; a little soft at 1080p"), ("2K", "Sharp at 1080p (recommended)"),
                          ("4K", "Largest, most expensive")):
            b = QPushButton(size, objectName="pill", checkable=True, toolTip=tip)
            self.size_group.addButton(b)
            self.size_buttons[size] = b
            size_row.addWidget(b)
        size_row.addStretch()
        gl.addLayout(size_row)
        gl.addWidget(QLabel("Every scene image is generated to match your Image style. If Gemini fails for a "
                            "scene, that scene uses the free sources and its Image chip says why.",
                            objectName="muted", wordWrap=True))
        img_l.addWidget(self.gemini_box)
        self.provider_gemini.toggled.connect(self.gemini_box.setVisible)

        self.openrouter_box = QFrame(objectName="storycard")
        self.openrouter_box.setAttribute(Qt.WA_StyledBackground, True)
        ol = QVBoxLayout(self.openrouter_box)
        ol.setContentsMargins(12, 10, 12, 12)
        ol.setSpacing(8)
        self.fields["openrouter_api_key"] = secret_edit("sk-or-…")
        ol.addLayout(field("OpenRouter API key", self.fields["openrouter_api_key"],
                           link("https://openrouter.ai/settings/keys", "Create a key") + " · pay-as-you-go credits, "
                           "" + link("https://openrouter.ai/settings/credits", "add credits")))
        self.openrouter_model = QComboBox(editable=True)
        for model_id, label in OPENROUTER_MODELS.items():
            self.openrouter_model.addItem(model_id, model_id)
            self.openrouter_model.setItemData(self.openrouter_model.count() - 1, label, Qt.ToolTipRole)
        ol.addLayout(field("Model", self.openrouter_model,
                           "Nano Banana costs about $0.04 per image. Any OpenRouter image model ID works here."))
        ol.addWidget(QLabel("Images match your Image style. If OpenRouter fails for a scene (no credits, refused "
                            "prompt), that scene uses the free sources and its Image chip says why.",
                            objectName="muted", wordWrap=True))
        img_l.addWidget(self.openrouter_box)
        self.provider_openrouter.toggled.connect(self.openrouter_box.setVisible)

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
        img_l.addLayout(field("Free source order", self.image_sources,
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

        video_l.addWidget(QLabel("Output folder", objectName="fieldLabel"))
        out_box = QFrame(objectName="storycard")
        out_box.setAttribute(Qt.WA_StyledBackground, True)
        ob = QHBoxLayout(out_box)
        ob.setContentsMargins(12, 8, 8, 8)
        self.output_label = QLabel(objectName="cardTitle", wordWrap=True)
        self.output_choose_btn = QPushButton("Choose…", clicked=self._choose_output)
        self.output_open_btn = QPushButton("Open", clicked=self._open_output)
        self.output_clear_btn = QPushButton("Clear", clicked=lambda: self._set_output(""))
        ob.addWidget(self.output_label, 1)
        for b in (self.output_choose_btn, self.output_open_btn, self.output_clear_btn):
            ob.addWidget(b)
        video_l.addWidget(out_box)
        self.output_hint = QLabel("Every finished video is also saved here as “Title (number).mp4”.",
                                  objectName="muted", wordWrap=True)
        video_l.addWidget(self.output_hint)
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
        provider = cfg.get("image_provider", "free")
        {"gemini": self.provider_gemini, "openrouter": self.provider_openrouter}.get(
            provider, self.provider_free).setChecked(True)
        self.gemini_box.setVisible(provider == "gemini")
        self.openrouter_box.setVisible(provider == "openrouter")
        self.openrouter_model.setCurrentText(cfg.get("openrouter_image_model") or "google/gemini-2.5-flash-image")
        self.gemini_model.setCurrentIndex(max(0, self.gemini_model.findData(cfg.get("gemini_image_model"))))
        self.size_buttons.get(cfg.get("gemini_image_size"), self.size_buttons["2K"]).setChecked(True)
        self.voice_engine.setCurrentIndex(max(0, self.voice_engine.findData(cfg["voice_engine"])))
        self._sample_path = cfg.get("voice_sample", "")
        self.voice_sample.setText(Path(self._sample_path).name if self._sample_path else "No sample — default voice")
        self.music.setChecked(bool(cfg["background_music"]))
        self.quality_buttons.get(cfg["render_preset"], self.quality_buttons["slow"]).setChecked(True)
        self._set_output(cfg.get("output_dir", ""))
        self.saved.clear()

    def save(self):
        cfg = settings.load()
        cfg["ai_provider"] = self.provider.currentData()
        for key, f in self.fields.items():
            cfg[key] = f.text().strip()
        cfg["image_sources"] = ",".join(s.strip() for s in self.image_sources.text().split(",") if s.strip())
        cfg["image_provider"] = ("gemini" if self.provider_gemini.isChecked() else
                                 "openrouter" if self.provider_openrouter.isChecked() else "free")
        cfg["openrouter_image_model"] = self.openrouter_model.currentText().strip() or "google/gemini-2.5-flash-image"
        cfg["gemini_image_model"] = self.gemini_model.currentData()
        cfg["gemini_image_size"] = next((k for k, b in self.size_buttons.items() if b.isChecked()), "2K")
        cfg["voice_engine"] = self.voice_engine.currentData()
        cfg["voice_sample"] = self._sample_path
        cfg["background_music"] = self.music.isChecked()
        cfg["output_dir"] = self._output_dir
        cfg["render_preset"] = next((p for p, b in self.quality_buttons.items() if b.isChecked()), "slow")
        settings.save(cfg)
        self.saved.setText("Saved · applies to the next render")

    def _set_output(self, path: str):
        self._output_dir = path or ""
        self.output_label.setText(self._output_dir or "Not set — videos stay inside the app")
        self.output_open_btn.setEnabled(bool(self._output_dir))
        self.output_clear_btn.setEnabled(bool(self._output_dir))

    def _choose_output(self):
        start = self._output_dir or str(Path.home() / "Movies")
        path = QFileDialog.getExistingDirectory(self, "Save finished videos to…", start)
        if not path:
            return
        self._set_output(path)
        with db.Session() as s:
            finished = s.query(db.Story).filter(db.Story.status == "done").count()
        if finished and QMessageBox.question(
                self, "Copy existing videos?",
                f"Copy your {finished} finished video{'s' if finished != 1 else ''} to this folder now?") \
                == QMessageBox.Yes:
            self.saved.setText("Copying videos…")
            run_async(export.export_all, db.Session, path,
                      on_done=lambda n: self.saved.setText(f"Copied {n} video{'s' if n != 1 else ''} · "
                                                           "press Save changes to keep this folder"),
                      on_error=lambda e: self.saved.setText(f"Copy failed: {e}"))
        else:
            self.saved.setText("Press Save changes to keep this folder")

    def _open_output(self):
        if self._output_dir:
            Path(self._output_dir).mkdir(parents=True, exist_ok=True)
            subprocess.run(["open", self._output_dir], check=False)

    def _pick_sample(self):
        path, _ = QFileDialog.getOpenFileName(self, "Voice sample (10–20 s of clear speech)", str(Path.home()),
                                              "Audio (*.wav *.mp3 *.m4a)")
        if not path:
            return
        dest = voices.add_sample(path)   # into the voice library; never overwrites another voice
        self._sample_path = str(dest)
        self.voice_sample.setText(dest.name)

    def _preview(self):
        if self._sample_path:
            self._player.setSource(QUrl.fromLocalFile(self._sample_path))
            self._player.play()
