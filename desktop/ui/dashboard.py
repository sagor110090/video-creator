"""Dashboard: story list + create-story form."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)

from desktop.core import db, settings
from desktop.services import story_ai
from desktop.ui.tasks import run_async

STATUS_ICON = {"draft": "○", "queued": "◔", "rendering": "◑", "done": "●", "failed": "✕"}


def create_story(title, content, style, talking_style, aspect_ratio, cfg, yt=None) -> int:
    """Split into scenes (AI image prompts) and save. Runs off the GUI thread."""
    scenes = story_ai.split_scenes(content, style, talking_style, cfg)
    if not scenes:
        raise story_ai.StoryAIError("The script has no sentences long enough to become scenes.")
    yt = yt or {}
    with db.Session() as s:
        st = db.Story(title=title or "Untitled", content=content, style=style, talking_style=talking_style,
                      aspect_ratio=aspect_ratio, youtube_title=yt.get("youtube_title"),
                      youtube_description=yt.get("youtube_description"), youtube_tags=yt.get("youtube_tags"))
        st.scenes = [db.Scene(order=i, narration=x["narration"], image_prompt=x["image_prompt"])
                     for i, x in enumerate(scenes)]
        s.add(st)
        s.commit()
        return st.id


class DashboardPage(QWidget):
    def __init__(self, bridge, open_story):
        super().__init__(objectName="page")
        self.bridge, self.open_story = bridge, open_story
        self._yt = {}

        # ---- story list
        left = QVBoxLayout()
        left.addWidget(QLabel("Stories", objectName="h1"))
        self.stories = QListWidget()
        self.stories.itemDoubleClicked.connect(lambda it: self.open_story(it.data(Qt.UserRole)))
        left.addWidget(self.stories, 1)
        hint = QLabel("Double-click a story to see every scene.", objectName="muted")
        left.addWidget(hint)

        # ---- create form
        card = QFrame(objectName="card")
        form_box = QVBoxLayout(card)
        form_box.addWidget(QLabel("Create New Story", objectName="h2"))
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.topic = QLineEdit(placeholderText="What is the video about? e.g. The Man Who Sold the Eiffel Tower")
        self.style = QComboBox()
        for key, label in story_ai.STYLES.items():
            self.style.addItem(label, key)
        self.talking = QComboBox()
        for key, label in story_ai.TALKING_STYLES.items():
            self.talking.addItem(label, key)
        fmt = QHBoxLayout()
        self.landscape = QRadioButton("Landscape 16:9", checked=True)
        self.shorts = QRadioButton("Shorts 9:16")
        group = QButtonGroup(self)
        for b in (self.landscape, self.shorts):
            group.addButton(b)
            fmt.addWidget(b)
        fmt.addStretch()
        form.addRow("Topic", self.topic)
        form.addRow("Content style", self.style)
        form.addRow("Talking style", self.talking)
        form.addRow("Format", fmt)
        form_box.addLayout(form)
        self.write_btn = QPushButton("✨ Write with AI")
        self.write_btn.clicked.connect(self._write)
        form_box.addWidget(self.write_btn, alignment=Qt.AlignLeft)
        self.title = QLineEdit(placeholderText="Title")
        self.script = QPlainTextEdit(placeholderText="Script — write your own or use Write with AI. "
                                                     "Each sentence becomes one scene.")
        form_box.addWidget(self.title)
        form_box.addWidget(self.script, 1)
        self.error = QLabel(objectName="error", wordWrap=True)
        form_box.addWidget(self.error)
        self.create_btn = QPushButton("Create && Render", objectName="primary")
        self.create_btn.clicked.connect(self._create)
        form_box.addWidget(self.create_btn, alignment=Qt.AlignRight)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)
        root.addLayout(left, 2)
        root.addWidget(card, 3)

        bridge.storyChanged.connect(lambda _id: self.refresh())
        self.refresh()

    @property
    def aspect_ratio(self):
        return "9:16" if self.shorts.isChecked() else "16:9"

    def refresh(self):
        current = self.stories.currentItem().data(Qt.UserRole) if self.stories.currentItem() else None
        self.stories.clear()
        with db.Session() as s:
            for st in s.query(db.Story).order_by(db.Story.created_at.desc(), db.Story.id.desc()):
                done = sum(sc.clip_status == "done" for sc in st.scenes)
                fmt = "Shorts" if st.aspect_ratio == "9:16" else "16:9"
                item = QListWidgetItem(
                    f"{STATUS_ICON.get(st.status, '?')}  {st.title or 'Untitled'}\n"
                    f"      {st.status} · {done}/{len(st.scenes)} scenes · {fmt} · {st.created_at:%b %d %H:%M}")
                item.setData(Qt.UserRole, st.id)
                self.stories.addItem(item)
                if st.id == current:
                    self.stories.setCurrentItem(item)

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
        self._busy(self.write_btn, "Writing…")
        run_async(story_ai.generate_story, settings.load(), topic, self.style.currentData(), self.aspect_ratio,
                  self.talking.currentData(), on_done=self._written, on_error=self._write_failed)

    def _written(self, data):
        self.write_btn.setEnabled(True)
        self.write_btn.setText("✨ Write with AI")
        self.title.setText(data.get("title", ""))
        self.script.setPlainText(data.get("content", ""))
        self._yt = data

    def _write_failed(self, e):
        self.write_btn.setEnabled(True)
        self.write_btn.setText("✨ Write with AI")
        self.error.setText(str(e))

    def _create(self):
        content = self.script.toPlainText().strip()
        if not content:
            self.error.setText("The script is empty.")
            return
        self._busy(self.create_btn, "Planning scenes…")
        run_async(create_story, self.title.text().strip() or self.topic.text().strip(), content,
                  self.style.currentData(), self.talking.currentData(), self.aspect_ratio, settings.load(), self._yt,
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
