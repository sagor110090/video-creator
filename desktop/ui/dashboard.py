"""Dashboard: story cards (left) + create-story panel (right), Dark Blue design."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from desktop.core import db, paths, settings
from desktop.pipeline.images import IMAGE_STYLES
from desktop.services import story_ai
from desktop.services.stories import create_story
from desktop.ui import icons
from desktop.ui.style import ACCENT, MUTED, badge_style, glow
from desktop.ui.tasks import run_async
from desktop.ui.voice_picker import VoicePicker

SCRIPT_LIMIT = 5000
THUMB = 64


def rounded(pixmap: QPixmap, size: int, radius: int = 12) -> QPixmap:
    """Square-crop and round the corners (story card thumbnails)."""
    src = pixmap.scaled(size * 2, size * 2, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x, y = (src.width() - size * 2) // 2, (src.height() - size * 2) // 2
    src = src.copy(x, y, size * 2, size * 2)
    out = QPixmap(size * 2, size * 2)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size * 2, size * 2, radius * 2, radius * 2)
    p.setClipPath(path)
    p.drawPixmap(0, 0, src)
    p.end()
    out.setDevicePixelRatio(2)
    return out


def _thumb_for(story) -> QPixmap | None:
    for sc in story.scenes:
        if sc.image_status == "done" and sc.image_path and Path(sc.image_path).exists():
            return rounded(QPixmap(sc.image_path), THUMB)
    return None


def _icon_label(name, color=ACCENT, size=16):
    lbl = QLabel()
    lbl.setPixmap(icons.pixmap(name, color, size))
    lbl.setFixedSize(size + 2, size + 2)
    return lbl


def _field_label(icon_name, text, color="#c084fc"):
    row = QHBoxLayout()
    row.setSpacing(6)
    row.addWidget(_icon_label(icon_name, color, 15))
    row.addWidget(QLabel(text, objectName="fieldLabel"))
    row.addStretch()
    return row


class StoryCard(QFrame):
    def __init__(self, story):
        super().__init__(objectName="storycard")
        self.story_id = story.id
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 10, 12, 10)
        lay.setSpacing(12)
        thumb = QLabel(fixedSize=QSize(THUMB, THUMB), alignment=Qt.AlignCenter)
        pm = _thumb_for(story)
        if pm:
            thumb.setPixmap(pm)
        else:
            thumb.setPixmap(icons.pixmap("film", "#3b5bb5", 28))
            thumb.setStyleSheet("background:#0b1430; border-radius:12px;")
        lay.addWidget(thumb)

        text = QVBoxLayout()
        text.setSpacing(5)
        title = QLabel(story.title or "Untitled", objectName="cardTitle")
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        text.addWidget(title)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        label, css = badge_style(story.status)
        badge = QLabel(label)
        badge.setStyleSheet(css)
        meta_row.addWidget(badge)
        done = sum(sc.clip_status == "done" for sc in story.scenes)
        fmt = "Shorts" if story.aspect_ratio == "9:16" else "16:9"
        meta = QLabel(f"{done}/{len(story.scenes)} scenes · {fmt} · {story.created_at:%b %d %H:%M}",
                      objectName="cardMeta")
        meta.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        meta_row.addWidget(meta, 1)
        text.addLayout(meta_row)
        lay.addLayout(text, 1)

        self.check = QLabel()
        self.check.setPixmap(icons.pixmap("check", ACCENT, 22))
        self.check.hide()
        self.dots = QLabel()
        self.dots.setPixmap(icons.pixmap("dots", MUTED, 18))
        lay.addWidget(self.check)
        lay.addWidget(self.dots)

    def set_selected(self, on: bool):
        self.setProperty("selected", "true" if on else "false")
        self.check.setVisible(on)
        self.dots.setVisible(not on)
        self.style().unpolish(self)
        self.style().polish(self)


class DashboardPage(QWidget):
    def __init__(self, bridge, open_story):
        super().__init__(objectName="page")
        self.bridge, self.open_story = bridge, open_story
        self._yt = {}

        # ---------------------------------------------------------- stories panel
        stories_panel = QFrame(objectName="panel")
        sp = QVBoxLayout(stories_panel)
        sp.setContentsMargins(18, 18, 18, 14)
        sp.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(_icon_label("book", "#dbe4ff", 22))
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(QLabel("Stories", objectName="panelTitle"))
        self.count_label = QLabel(objectName="muted")
        titles.addWidget(self.count_label)
        head.addLayout(titles)
        head.addStretch()
        self.search = QLineEdit(objectName="search", placeholderText="Search stories…")
        self.search.addAction(icons.icon("search", MUTED, 16), QLineEdit.LeadingPosition)
        self.search.setFixedWidth(220)
        self.search.textChanged.connect(self._filter)
        head.addWidget(self.search)
        sp.addLayout(head)

        self.stories = QListWidget()
        self.stories.setSpacing(5)
        self.stories.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.stories.itemDoubleClicked.connect(lambda it: self.open_story(it.data(Qt.UserRole)))
        self.stories.currentItemChanged.connect(self._on_select)
        sp.addWidget(self.stories, 1)
        hint = QHBoxLayout()
        hint.addWidget(_icon_label("info", MUTED, 14))
        hint.addWidget(QLabel("Double-click a story to see every scene.", objectName="muted"))
        hint.addStretch()
        sp.addLayout(hint)

        # ---------------------------------------------------------- create panel
        create_panel = QFrame(objectName="panel")
        cp = QVBoxLayout(create_panel)
        cp.setContentsMargins(0, 0, 0, 0)
        cp.setSpacing(0)

        banner = QFrame(objectName="banner")
        banner.setAttribute(Qt.WA_StyledBackground, True)
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(20, 16, 16, 16)
        bl.addWidget(_icon_label("wand", "#ffffff", 26))
        bt = QVBoxLayout()
        bt.setSpacing(2)
        bt.addWidget(QLabel("Create New Story", objectName="bannerTitle"))
        bt.addWidget(QLabel("Pick a topic, let AI write it, then render it in your voice.", objectName="bannerSub"))
        bl.addLayout(bt, 1)
        art = QLabel()
        art.setPixmap(QPixmap(str(paths.assets_dir() / "logo.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        bl.addWidget(art)
        cp.addWidget(banner)

        body = QWidget(objectName="formBody")   # transparent via the theme (a local stylesheet would cascade)
        form = QVBoxLayout(body)
        form.setContentsMargins(20, 16, 20, 18)
        form.setSpacing(8)

        form.addLayout(_field_label("tag", "Topic"))
        self.topic = QLineEdit(placeholderText="What is the video about? e.g. The Man Who Sold the Eiffel Tower")
        form.addWidget(self.topic)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.addLayout(_field_label("palette", "Content style", "#60a5fa"), 0, 0)
        grid.addLayout(_field_label("mic", "Talking style", "#60a5fa"), 0, 1)
        self.style = QComboBox()
        for key, label in story_ai.STYLES.items():
            self.style.addItem(label, key)
        self.talking = QComboBox()
        for key, label in story_ai.TALKING_STYLES.items():
            self.talking.addItem(label, key)
        grid.addWidget(self.style, 1, 0)
        grid.addWidget(self.talking, 1, 1)
        form.addSpacing(4)
        form.addLayout(grid)

        fmt_voice = QGridLayout()
        fmt_voice.setHorizontalSpacing(12)
        fmt_voice.setVerticalSpacing(6)
        fmt_voice.addLayout(_field_label("image", "Image style", "#60a5fa"), 0, 0)
        fmt_voice.addLayout(_field_label("mic", "Voice", "#60a5fa"), 0, 1)
        self.image_style = QComboBox()
        for key, st in IMAGE_STYLES.items():
            self.image_style.addItem(st["label"], key)
        self.image_style.setToolTip("What the scene images should look like. Cartoon, Anime and 3D are drawn by AI.")
        fmt_voice.addWidget(self.image_style, 1, 0)
        fmt_voice.addLayout(_field_label("film", "Format", "#60a5fa"), 2, 0)
        fmt = QHBoxLayout()
        fmt.setSpacing(8)
        self.landscape = QPushButton(" Landscape 16:9", objectName="pill", checkable=True, checked=True)
        self.landscape.setIcon(icons.icon("monitor", "#dbe4ff", 16))
        self.shorts = QPushButton(" Shorts 9:16", objectName="pill", checkable=True)
        self.shorts.setIcon(icons.icon("phone", "#dbe4ff", 16))
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b in (self.landscape, self.shorts):
            b.setCursor(Qt.PointingHandCursor)
            group.addButton(b)
            fmt.addWidget(b)
        fmt.addStretch()
        fmt_voice.addLayout(fmt, 3, 0, 1, 2)
        self.voice = VoicePicker()
        self.voice.setToolTip("Default uses the voice sample from Settings")
        fmt_voice.addWidget(self.voice, 1, 1)
        fmt_voice.setColumnStretch(0, 1)
        fmt_voice.setColumnStretch(1, 1)
        form.addSpacing(4)
        form.addLayout(fmt_voice)

        form.addSpacing(4)
        form.addLayout(_field_label("pencil", "Title", "#60a5fa"))
        self.title = QLineEdit(placeholderText="A catchy title for your story")
        form.addWidget(self.title)

        form.addSpacing(4)
        script_head = _field_label("lines", "Script", "#60a5fa")
        self.counter = QLabel(f"0 / {SCRIPT_LIMIT}", objectName="counter")
        script_head.addWidget(self.counter)
        form.addLayout(script_head)
        self.script = QPlainTextEdit(placeholderText="Write your own script, or use Write with AI to generate one. "
                                                     "Each sentence becomes one scene.")
        self.script.textChanged.connect(self._count)
        form.addWidget(self.script, 1)

        self.error = QLabel(objectName="error", wordWrap=True)
        form.addWidget(self.error)
        actions = QHBoxLayout()
        self.write_btn = QPushButton(" Write with AI", objectName="ai")
        self.write_btn.setIcon(icons.icon("sparkles", "#ffffff", 16))
        self.write_btn.clicked.connect(self._write)
        self.create_btn = QPushButton("Create && Render", objectName="primary")
        self.create_btn.setIcon(icons.icon("arrow", "#ffffff", 16))
        self.create_btn.setLayoutDirection(Qt.RightToLeft)   # arrow after the text
        self.create_btn.clicked.connect(self._create)
        for b in (self.write_btn, self.create_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(40)
        actions.addWidget(self.write_btn)
        actions.addStretch()
        actions.addWidget(self.create_btn)
        form.addLayout(actions)
        cp.addWidget(body, 1)

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(18)
        root.addWidget(stories_panel, 5)
        root.addWidget(create_panel, 6)
        glow(stories_panel)
        glow(create_panel)

        bridge.storyChanged.connect(lambda _id: self.refresh())
        self.refresh()

    @property
    def aspect_ratio(self):
        return "9:16" if self.shorts.isChecked() else "16:9"

    # ------------------------------------------------------------ list
    def refresh(self):
        self.voice.reload()   # the Settings default may have changed
        current = self.stories.currentItem().data(Qt.UserRole) if self.stories.currentItem() else None
        self.stories.clear()
        with db.Session() as s:
            stories = s.query(db.Story).order_by(db.Story.created_at.desc(), db.Story.id.desc()).all()
            for st in stories:
                card = StoryCard(st)
                item = QListWidgetItem()
                item.setData(Qt.UserRole, st.id)
                item.setData(Qt.UserRole + 1, (st.title or "").lower())
                item.setSizeHint(QSize(0, THUMB + 22))
                self.stories.addItem(item)
                self.stories.setItemWidget(item, card)
                if st.id == current:
                    self.stories.setCurrentItem(item)
        n = len(stories)
        self.count_label.setText(f"{n} {'story' if n == 1 else 'stories'}")
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.strip().lower()
        for i in range(self.stories.count()):
            item = self.stories.item(i)
            item.setHidden(bool(text) and text not in item.data(Qt.UserRole + 1))

    def _on_select(self, current, previous):
        for item, on in ((previous, False), (current, True)):
            if item is not None:
                card = self.stories.itemWidget(item)
                if card:
                    card.set_selected(on)

    def _count(self):
        n = len(self.script.toPlainText())
        self.counter.setText(f"{n} / {SCRIPT_LIMIT}")
        self.counter.setStyleSheet("color:#f87171;" if n > SCRIPT_LIMIT else "")

    # ------------------------------------------------------------ actions
    def _busy(self, button, text):
        button.setEnabled(False)
        button.setText(text)
        self.error.clear()

    def _write(self):
        topic = self.topic.text().strip()
        if not topic:
            self.error.setText("Enter a topic first.")
            return
        self._busy(self.write_btn, " Writing…")
        run_async(story_ai.generate_story, settings.load(), topic, self.style.currentData(), self.aspect_ratio,
                  self.talking.currentData(), on_done=self._written, on_error=self._write_failed)

    def _written(self, data):
        self.write_btn.setEnabled(True)
        self.write_btn.setText(" Write with AI")
        self.title.setText(data.get("title", ""))
        self.script.setPlainText(data.get("content", ""))
        self._yt = data

    def _write_failed(self, e):
        self.write_btn.setEnabled(True)
        self.write_btn.setText(" Write with AI")
        self.error.setText(str(e))

    def _create(self):
        content = self.script.toPlainText().strip()
        if not content:
            self.error.setText("The script is empty.")
            return
        if len(content) > SCRIPT_LIMIT:
            self.error.setText(f"The script is over {SCRIPT_LIMIT} characters. Shorten it to keep render times sane.")
            return
        self._busy(self.create_btn, "Planning scenes…")
        run_async(create_story, self.title.text().strip() or self.topic.text().strip(), content,
                  self.style.currentData(), self.talking.currentData(), self.aspect_ratio, settings.load(), self._yt,
                  voice_sample=self.voice.value(), image_style=self.image_style.currentData(),
                  on_done=self._created, on_error=self._create_failed)

    def _created(self, story_id):
        self.create_btn.setEnabled(True)
        self.create_btn.setText("Create && Render")
        self.title.clear()
        self.script.clear()
        self._yt = {}
        self.bridge.submit_render(story_id)
        self.refresh()
        self.open_story(story_id)

    def _create_failed(self, e):
        self.create_btn.setEnabled(True)
        self.create_btn.setText("Create && Render")
        self.error.setText(str(e))
