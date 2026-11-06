"""Story view: header + final player + one row per scene showing image, voice and clip with their status."""
import subprocess
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSlider, QVBoxLayout,
                               QWidget)

from desktop.core import db, paths
from desktop.ui.style import chip_style

BUSY = ("queued", "rendering")
SOURCE_NAMES = {"openverse": "Openverse", "pexels": "Pexels", "pixabay": "Pixabay", "pollinations": "Pollinations (AI)",
                "loremflickr": "LoremFlickr", "previous_scene": "Reused previous scene", "placeholder": "Placeholder",
                "manual": "Your file", "imported": "Imported"}


class ClickLabel(QLabel):
    def __init__(self, on_click, **kw):
        super().__init__(**kw)
        self.on_click = on_click
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, e):
        self.on_click()


class Player(QWidget):
    """Video player with play/pause and a seek slider. Also used for single scene clips."""

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video = QVideoWidget()
        self.video.setMinimumHeight(260)
        self.player.setVideoOutput(self.video)
        self.label = QLabel(objectName="muted")
        self.play_btn = QPushButton("▶", fixedWidth=40)
        self.play_btn.clicked.connect(self.toggle)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.durationChanged.connect(lambda d: self.slider.setRange(0, d))
        self.player.positionChanged.connect(self.slider.setValue)
        self.player.playbackStateChanged.connect(
            lambda st: self.play_btn.setText("⏸" if st == QMediaPlayer.PlayingState else "▶"))
        controls = QHBoxLayout()
        controls.addWidget(self.play_btn)
        controls.addWidget(self.slider, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.video, 1)
        lay.addLayout(controls)
        lay.addWidget(self.label)

    def load(self, path, label, autoplay=False):
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.label.setText(label)
        if autoplay:
            self.player.play()

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()


class SceneRow(QFrame):
    def __init__(self, view, scene):
        super().__init__(objectName="card")
        self.view, self.scene_id, self.story_id = view, scene.id, scene.story_id
        grid = QGridLayout(self)
        grid.setColumnStretch(1, 1)

        # thumbnail + source
        self.thumb = ClickLabel(self._show_full, fixedWidth=224, fixedHeight=126, alignment=Qt.AlignCenter)
        self.thumb.setStyleSheet("background:#0b1220; border-radius:6px;")
        self.source = QLabel(objectName="muted", wordWrap=True, openExternalLinks=True)
        self.source.setFixedWidth(224)
        left = QVBoxLayout()
        left.addWidget(self.thumb)
        left.addWidget(self.source)
        left.addStretch()
        grid.addLayout(left, 0, 0, 3, 1)

        # header: number + chips
        head = QHBoxLayout()
        self.number = QLabel(objectName="h2")
        head.addWidget(self.number)
        self.chips = {}
        for stage in db.STAGES:
            chip = QLabel()
            self.chips[stage] = chip
            head.addWidget(chip)
        self.meta = QLabel(objectName="muted")
        head.addWidget(self.meta)
        head.addStretch()
        grid.addLayout(head, 0, 1)

        # editable text
        self.narration = QPlainTextEdit(fixedHeight=64)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Image search prompt")
        edits = QVBoxLayout()
        edits.addWidget(self.narration)
        edits.addWidget(self.prompt)
        grid.addLayout(edits, 1, 1)

        # actions
        bar = QHBoxLayout()
        self.voice_btn = QPushButton("▶ Voice", clicked=self._play_voice)
        self.clip_btn = QPushButton("▶ Clip", clicked=self._play_clip)
        self.save_btn = QPushButton("Save text", clicked=self._save)
        self.replace_btn = QPushButton("Replace image…", clicked=self._replace_image)
        self.refetch_btn = QPushButton("New image", clicked=lambda: self._redo("image"))
        self.revoice_btn = QPushButton("Re-voice", clicked=lambda: self._redo("voice"))
        self.rerender_btn = QPushButton("Re-render clip", clicked=lambda: self._redo("clip"))
        for b in (self.voice_btn, self.clip_btn, self.save_btn, self.replace_btn, self.refetch_btn,
                  self.revoice_btn, self.rerender_btn):
            bar.addWidget(b)
        bar.addStretch()
        grid.addLayout(bar, 2, 1)
        self.update_from(scene, busy=False, force_text=True)

    # ------------------------------------------------------------ display
    def update_from(self, sc, busy: bool, force_text=False):
        self.paths = {st: getattr(sc, f"{st}_path") for st in db.STAGES}
        self.number.setText(f"Scene {sc.order + 1}")
        for stage in db.STAGES:
            status = getattr(sc, f"{stage}_status")
            chip = self.chips[stage]
            chip.setText(f"{stage.capitalize()}: {status}")
            chip.setStyleSheet(chip_style(status))
            chip.setToolTip(getattr(sc, f"{stage}_error") or "")
        bits = []
        if sc.voice_engine:
            bits.append(f"voice: {sc.voice_engine}")
        if sc.duration_s:
            bits.append(f"{sc.duration_s:.1f}s")
        self.meta.setText(" · ".join(bits))
        self._set_thumb(sc.image_path if sc.image_status == "done" else None)
        name = SOURCE_NAMES.get(sc.image_source, sc.image_source or "")
        lic = f" · {sc.image_license}" if sc.image_license else ""
        link = f' · <a style="color:#22d3ee" href="{sc.image_source_url}">source</a>' if sc.image_source_url else ""
        self.source.setText(f"{name}{lic}{link}" if name else "")
        if force_text or not self._dirty():
            self.narration.setPlainText(sc.narration)
            self.prompt.setText(sc.image_prompt or "")
            self._saved_text = (sc.narration, sc.image_prompt or "")
        self.voice_btn.setEnabled(sc.voice_status == "done" and bool(sc.voice_path))
        self.clip_btn.setEnabled(sc.clip_status == "done" and bool(sc.clip_path))
        for b in (self.save_btn, self.replace_btn, self.refetch_btn, self.revoice_btn, self.rerender_btn):
            b.setEnabled(not busy)
        self.rerender_btn.setEnabled(not busy and sc.image_status == "done" and sc.voice_status == "done")

    def _set_thumb(self, path):
        self._image = path if path and Path(path).exists() else None
        if self._image:
            pm = QPixmap(self._image).scaled(224, 126, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.thumb.setPixmap(pm)
        else:
            self.thumb.setPixmap(QPixmap())
            self.thumb.setText("no image yet")

    def _dirty(self):
        saved = getattr(self, "_saved_text", None)
        return saved is not None and (self.narration.toPlainText(), self.prompt.text()) != saved

    # ------------------------------------------------------------ actions
    def _show_full(self):
        if not self._image:
            return
        dlg = QDialog(self, windowTitle="Scene image")
        lbl = QLabel()
        lbl.setPixmap(QPixmap(self._image).scaled(1280, 720, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        QVBoxLayout(dlg).addWidget(lbl)
        dlg.exec()

    def _play_voice(self):
        self.view.play_audio(self.paths["voice"])

    def _play_clip(self):
        self.view.player.load(self.paths["clip"], f"Scene clip: {self.number.text()}", autoplay=True)
        self.view.player.show()

    def _save(self):
        narration, prompt = self.narration.toPlainText().strip(), self.prompt.text().strip()
        with db.Session() as s:
            sc = s.get(db.Scene, self.scene_id)
            prompt_changed = prompt != (sc.image_prompt or "")
            narration_changed = narration and narration != sc.narration
            if narration_changed:
                sc.narration = narration
            if prompt_changed:
                sc.image_prompt = prompt
                sc.reset_from("image")       # new image, so voice+clip too (clip needs both)
            elif narration_changed:
                sc.reset_from("voice")       # image stays; voice and clip are stale
            s.commit()
        self._saved_text = None
        self.view.refresh()

    def _replace_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose an image", str(Path.home()),
                                              "Images (*.jpg *.jpeg *.png *.webp)")
        if not path:
            return
        out = paths.scene_dir(self.story_id, self.scene_id) / "image.jpg"
        Image.open(path).convert("RGB").save(out, "JPEG", quality=92)
        with db.Session() as s:
            sc = s.get(db.Scene, self.scene_id)
            sc.image_path, sc.image_status, sc.image_error = str(out), "done", None
            sc.image_source, sc.image_source_url, sc.image_license = "manual", None, None
            sc.reset_from("clip")
            s.commit()
        self.view.bridge.submit_redo(self.story_id, self.scene_id, "clip")
        self.view.refresh()

    def _redo(self, stage):
        self.view.bridge.submit_redo(self.story_id, self.scene_id, stage)
        self.view.refresh()


class StoryView(QWidget):
    def __init__(self, bridge, back):
        super().__init__(objectName="page")
        self.bridge, self.story_id, self.rows = bridge, None, {}
        self.audio_player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.audio_out)

        head = QHBoxLayout()
        back_btn = QPushButton("← Stories", clicked=lambda: (self.stop_media(), back()))
        self.title = QLabel(objectName="h1")
        self.status = QLabel()
        head.addWidget(back_btn)
        head.addWidget(self.title)
        head.addWidget(self.status)
        head.addStretch()
        self.render_btn = QPushButton("Render", objectName="primary", clicked=self._render)
        self.rebuild_btn = QPushButton("Rebuild final video", clicked=self._rebuild)
        self.folder_btn = QPushButton("Open folder", clicked=self._open_folder)
        for b in (self.rebuild_btn, self.folder_btn, self.render_btn):
            head.addWidget(b)

        self.progress = QProgressBar(textVisible=False)
        self.progress_text = QLabel(objectName="muted")
        self.error = QLabel(objectName="error", wordWrap=True)
        self.player = Player()
        self.player.hide()

        self.list_box = QVBoxLayout()
        self.list_box.addStretch()
        inner = QWidget()
        inner.setLayout(self.list_box)
        scroll = QScrollArea(widgetResizable=True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QFrame.NoFrame)

        top = QVBoxLayout()
        top.addLayout(head)
        prog = QHBoxLayout()
        prog.addWidget(self.progress, 1)
        prog.addWidget(self.progress_text)
        top.addLayout(prog)
        top.addWidget(self.error)
        top.addWidget(self.player)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.addLayout(top)
        root.addWidget(scroll, 1)

        bridge.storyChanged.connect(self._on_story)
        bridge.sceneChanged.connect(self._on_scene)

    # ------------------------------------------------------------ loading
    def show_story(self, story_id):
        self.stop_media()
        self.story_id = story_id
        for row in self.rows.values():
            row.setParent(None)
            row.deleteLater()
        self.rows = {}
        with db.Session() as s:
            st = s.get(db.Story, story_id)
            busy = st.status in BUSY
            for sc in st.scenes:
                row = SceneRow(self, sc)
                row.update_from(sc, busy, force_text=True)
                self.rows[sc.id] = row
                self.list_box.insertWidget(self.list_box.count() - 1, row)
        self.refresh(rows=False)
        self._load_final()

    def refresh(self, rows=True):
        if self.story_id is None:
            return
        with db.Session() as s:
            st = s.get(db.Story, self.story_id)
            if st is None:
                return
            busy = st.status in BUSY
            self.title.setText(st.title or "Untitled")
            self.status.setText(st.status)
            self.status.setStyleSheet(chip_style(st.status))
            total = len(st.scenes) * len(db.STAGES)
            done = sum(getattr(sc, f"{x}_status") == "done" for sc in st.scenes for x in db.STAGES)
            self.progress.setRange(0, max(total, 1))
            self.progress.setValue(done)
            final = "final video ready" if st.final_path and Path(st.final_path).exists() else "no final video yet"
            self.progress_text.setText(f"{done}/{total} steps · {final}")
            self.error.setText(st.error or "")
            self.render_btn.setEnabled(not busy)
            self.render_btn.setText({"draft": "Render", "failed": "Retry / resume",
                                     "done": "Render missing"}.get(st.status, "Rendering…"))
            self.rebuild_btn.setEnabled(not busy and all(sc.clip_status == "done" for sc in st.scenes))
            if rows:
                for sc in st.scenes:
                    if sc.id in self.rows:
                        self.rows[sc.id].update_from(sc, busy)

    def _load_final(self):
        with db.Session() as s:
            st = s.get(db.Story, self.story_id)
            final = st.final_path if st and st.final_path and Path(st.final_path).exists() else None
        if final:
            self.player.load(final, "Final video")
            self.player.show()
        else:
            self.player.stop()
            self.player.hide()

    # ------------------------------------------------------------ signals
    def _on_story(self, story_id):
        if story_id == self.story_id:
            self.refresh()
            with db.Session() as s:
                st = s.get(db.Story, story_id)
                if st and st.status == "done":
                    self._load_final()

    def _on_scene(self, story_id, scene_id):
        if story_id != self.story_id or scene_id not in self.rows:
            return
        with db.Session() as s:
            sc = s.get(db.Scene, scene_id)
            busy = sc.story.status in BUSY
            self.rows[scene_id].update_from(sc, busy)
        self.refresh(rows=False)

    # ------------------------------------------------------------ actions
    def play_audio(self, path):
        self.audio_player.setSource(QUrl.fromLocalFile(str(path)))
        self.audio_player.play()

    def stop_media(self):
        self.audio_player.stop()
        self.player.stop()

    def _render(self):
        self.bridge.submit_render(self.story_id)
        self.refresh()

    def _rebuild(self):
        with db.Session() as s:
            s.get(db.Story, self.story_id).final_path = None
            s.commit()
        self.player.stop()
        self.bridge.submit_render(self.story_id)
        self.refresh()

    def _open_folder(self):
        subprocess.run(["open", str(paths.story_dir(self.story_id))], check=False)
