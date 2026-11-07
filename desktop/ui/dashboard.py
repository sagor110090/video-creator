"""Dashboard: story cards (left) + create-story panel (right), Dark Blue design."""
import subprocess
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
                               QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from desktop.core import db, paths, settings
from desktop.pipeline.images import IMAGE_STYLES
from desktop.services import story_ai
from desktop.services import stories
from desktop.services.stories import create_story
from desktop.ui import icons
from desktop.ui.style import ACCENT, MUTED, badge_style, glow
from desktop.ui.tasks import run_async
from desktop.ui.voice_picker import VoicePicker
from desktop.ui.widgets import image_source_combo, settings_source_label

SCRIPT_LIMIT = 5000
STATUS_FILTERS = [("All stories", ""), ("Done", "done"), ("Rendering", "rendering"), ("Review images", "review"),
                  ("Failed", "failed"), ("Draft", "draft"), ("On YouTube", "uploaded"),
                  ("Done, not uploaded", "not_uploaded")]
_STATUS_ORDER = {"rendering": 0, "queued": 0, "review": 1, "failed": 2, "draft": 3, "done": 4}
SORTS = {"newest": lambda st: (-st.created_at.timestamp(), -st.id),
         "oldest": lambda st: (st.created_at.timestamp(), st.id),
         "title": lambda st: ((st.title or "").lower(), st.id),
         "status": lambda st: (_STATUS_ORDER.get(st.status, 9), -st.created_at.timestamp())}
# YouTube state shown next to the render status: (label, background, text colour)
UPLOAD_BADGES = {"completed": ("Uploaded", "#3a0d14", "#ff6b6b"), "manual": ("Uploaded", "#3a0d14", "#ff6b6b"), "scheduled": ("Scheduled", "#3a2a0d", "#fbbf24"),
                 "uploading": ("Uploading…", "#102a5c", "#60a5fa"), "failed": ("Upload failed", "#4a1420", "#f87171")}
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
    def __init__(self, story, page=None):
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
        self.title = title = QLabel(story.title or "Untitled", objectName="cardTitle")
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        text.addWidget(title)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        label, css = badge_style(story.status)
        badge = QLabel(label)
        badge.setStyleSheet(css)
        meta_row.addWidget(badge)
        self.upload_badge = QLabel()
        up = UPLOAD_BADGES.get(story.youtube_upload_status)
        if up:
            up_label, bg, fg = up
            self.upload_badge.setText(up_label)
            self.upload_badge.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:8px; padding:2px 8px;"
                                            "font-size:11px; font-weight:600;")
            who = "Uploaded by you" if story.youtube_upload_status == "manual" else ""
            if story.youtube_video_id:
                self.upload_badge.setToolTip(f"{who + ' · ' if who else ''}https://youtu.be/{story.youtube_video_id}")
            elif who:
                self.upload_badge.setToolTip(who)
            elif story.youtube_error:
                self.upload_badge.setToolTip(story.youtube_error)
        else:
            self.upload_badge.hide()
        meta_row.addWidget(self.upload_badge)
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
        self.dots = QToolButton(objectName="dots", toolTip="More actions")
        self.dots.setIcon(icons.icon("dots", MUTED, 18))
        self.dots.setAutoRaise(True)
        self.dots.setCursor(Qt.PointingHandCursor)
        self.dots.setPopupMode(QToolButton.InstantPopup)
        self.menu = QMenu(self)
        if page is not None:
            sid = story.id
            self.menu.addAction("Open story", lambda: page.open_story(sid))
            if story.youtube_upload_status == "manual":
                self.menu.addAction("Mark as not uploaded", lambda: page._unmark_uploaded(sid))
            elif story.youtube_upload_status not in ("completed", "scheduled", "uploading"):
                self.menu.addAction("Mark as uploaded…", lambda: page._mark_uploaded(sid))
            self.menu.addSeparator()
            video = next((p for p in (story.export_path, story.final_path) if p and Path(p).exists()), None)
            if video:
                self.menu.addAction("Show video in Finder", lambda: subprocess.run(["open", "-R", video], check=False))
            self.menu.addAction("Open folder", lambda: subprocess.run(["open", str(paths.story_dir(sid))], check=False))
            self.menu.addSeparator()
            delete = self.menu.addAction(icons.icon("trash", "#f87171", 14), "Delete story…",
                                         lambda: page._delete_story(sid))
            if story.status in ("rendering", "queued"):
                delete.setEnabled(False)
                delete.setToolTip("Wait for the render to finish")
        self.dots.setMenu(self.menu)
        lay.addWidget(self.check)
        lay.addWidget(self.dots)

    def action(self, text):
        return next((a for a in self.menu.actions() if a.text() == text), None)

    def set_selected(self, on: bool):
        self.setProperty("selected", "true" if on else "false")
        self.check.setVisible(on)
        self.style().unpolish(self)
        self.style().polish(self)


class DashboardPage(QWidget):
    def __init__(self, bridge, open_story):
        super().__init__(objectName="page")
        self.bridge, self.open_story = bridge, open_story
        self._yt = {}
        self._review = False
        self.select_mode = False

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
        self.search.textChanged.connect(lambda _t: self._apply_filters())
        head.addWidget(self.search)
        sp.addLayout(head)

        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.format_filter = QComboBox(toolTip="Show only one format")
        for label, data in (("All formats", ""), ("Shorts 9:16", "9:16"), ("Landscape 16:9", "16:9")):
            self.format_filter.addItem(label, data)
        self.status_filter = QComboBox(toolTip="Show only stories in this state")
        for label, data in STATUS_FILTERS:
            self.status_filter.addItem(label, data)
        self.sort = QComboBox(toolTip="Sort stories")
        for label, data in (("Newest first", "newest"), ("Oldest first", "oldest"), ("Title A–Z", "title"),
                            ("Status", "status")):
            self.sort.addItem(label, data)
        self.select_btn = QPushButton("Select", objectName="pill", checkable=True,
                                      toolTip="Pick several stories to delete at once")
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.toggled.connect(self._set_select_mode)
        for w in (self.format_filter, self.status_filter, self.sort):
            w.currentIndexChanged.connect(lambda _=0: self._apply_filters())
            tools.addWidget(w)
        self.sort.currentIndexChanged.disconnect()
        self.sort.currentIndexChanged.connect(lambda _=0: self.refresh())
        tools.addStretch()
        tools.addWidget(self.select_btn)
        sp.addLayout(tools)

        self.bulk_bar = QFrame(objectName="storycard")
        self.bulk_bar.setAttribute(Qt.WA_StyledBackground, True)
        bb = QHBoxLayout(self.bulk_bar)
        bb.setContentsMargins(10, 6, 8, 6)
        self.select_all_btn = QPushButton("Select all", clicked=self._select_all)
        self.select_none_btn = QPushButton("Select none", clicked=lambda: self.stories.clearSelection())
        self.selected_count = QLabel("0 selected", objectName="muted")
        self.delete_selected_btn = QPushButton(" Delete selected", objectName="danger", clicked=self._delete_selected)
        self.delete_selected_btn.setIcon(icons.icon("trash", "#ffffff", 14))
        for w in (self.select_all_btn, self.select_none_btn, self.selected_count):
            bb.addWidget(w)
        bb.addStretch()
        bb.addWidget(self.delete_selected_btn)
        self.bulk_bar.hide()
        sp.addWidget(self.bulk_bar)

        self.stories = QListWidget()
        self.stories.setSpacing(5)
        self.stories.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.stories.itemDoubleClicked.connect(lambda it: self.open_story(it.data(Qt.UserRole)))
        self.stories.itemSelectionChanged.connect(self._on_select)
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
        fmt_voice.addLayout(_field_label("sparkles", "Image source", "#60a5fa"), 2, 1)
        self.image_source = image_source_combo(settings_source_label())
        self.image_source.setToolTip("Free sources, or paid AI images from Gemini / OpenRouter. "
                                     "You can still change it per scene when reviewing.")
        fmt_voice.addWidget(self.image_source, 3, 1)
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
        fmt_voice.addLayout(fmt, 3, 0)
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
        self.next_btn = QPushButton("Next: review images", clicked=self._next)
        self.next_btn.setIcon(icons.icon("arrow", "#dbe4ff", 16))
        self.next_btn.setLayoutDirection(Qt.RightToLeft)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setMinimumHeight(40)
        self.next_btn.setToolTip("Step by step: fetch the images first, check or change them, then build the video")
        actions.addWidget(self.write_btn)
        actions.addStretch()
        actions.addWidget(self.next_btn)
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
        self.image_source.setItemText(0, settings_source_label())
        keep = {it.data(Qt.UserRole) for it in self.stories.selectedItems()}
        self.stories.blockSignals(True)
        self.stories.clear()
        with db.Session() as s:
            stories = sorted(s.query(db.Story).all(), key=SORTS[self.sort.currentData() or "newest"])
            for st in stories:
                card = StoryCard(st, self)
                item = QListWidgetItem()
                item.setData(Qt.UserRole, st.id)
                item.setData(Qt.UserRole + 1, (st.title or "").lower())
                item.setData(Qt.UserRole + 2, st.aspect_ratio)
                item.setData(Qt.UserRole + 3, st.status)
                item.setData(Qt.UserRole + 4, st.youtube_upload_status or "")
                item.setSizeHint(QSize(0, THUMB + 22))
                self.stories.addItem(item)
                self.stories.setItemWidget(item, card)
                if st.id in keep:
                    item.setSelected(True)
        self.stories.blockSignals(False)
        self._total = len(stories)
        self._apply_filters()
        self._on_select()

    def _matches(self, item) -> bool:
        text = self.search.text().strip().lower()
        if text and text not in item.data(Qt.UserRole + 1):
            return False
        fmt = self.format_filter.currentData()
        if fmt and item.data(Qt.UserRole + 2) != fmt:
            return False
        want = self.status_filter.currentData()
        status, upload = item.data(Qt.UserRole + 3), item.data(Qt.UserRole + 4)
        if want == "uploaded":
            return upload in ("completed", "manual", "scheduled")
        if want == "not_uploaded":
            return status == "done" and upload in ("", "failed")
        if want == "rendering":
            return status in ("rendering", "queued")
        return not want or status == want

    def _apply_filters(self):
        shown = 0
        for i in range(self.stories.count()):
            item = self.stories.item(i)
            ok = self._matches(item)
            item.setHidden(not ok)
            if not ok and item.isSelected():
                item.setSelected(False)      # never act on stories you can't see
            shown += ok
        total = getattr(self, "_total", shown)
        noun = "story" if total == 1 else "stories"
        self.count_label.setText(f"{total} {noun}" if shown == total else f"{shown} of {total} {noun}")

    def _on_select(self, *_):
        for i in range(self.stories.count()):
            item = self.stories.item(i)
            card = self.stories.itemWidget(item)
            if card:
                card.set_selected(item.isSelected())
        n = len(self.stories.selectedItems())
        self.selected_count.setText(f"{n} selected")
        self.delete_selected_btn.setEnabled(n > 0)

    def _set_select_mode(self, on: bool):
        self.select_mode = on
        self.stories.clearSelection()
        self.stories.setSelectionMode(QAbstractItemView.MultiSelection if on else QAbstractItemView.SingleSelection)
        self.bulk_bar.setVisible(on)
        self.select_btn.setText("Done" if on else "Select")
        self._on_select()

    def _select_all(self):
        for i in range(self.stories.count()):
            item = self.stories.item(i)
            if not item.isHidden():
                item.setSelected(True)

    def _delete_selected(self):
        ids = [it.data(Qt.UserRole) for it in self.stories.selectedItems() if not it.isHidden()]
        if not ids:
            return
        with db.Session() as s:
            rows = {st.id: st for st in s.query(db.Story).filter(db.Story.id.in_(ids))}
            busy = [i for i in ids if rows[i].status in ("rendering", "queued")]
        todo = [i for i in ids if i not in busy]
        if not todo:
            self.error.setText("The selected stories are rendering. Wait for them to finish, then delete them.")
            return
        n = len(todo)
        msg = (f"Delete {n} {'story' if n == 1 else 'stories'}?\n\nTheir scenes, images, voice clips and videos "
               "inside the app will be removed. Copies in your output folder and videos on YouTube are kept.")
        if busy:
            msg += f"\n\n{len(busy)} rendering {'story is' if len(busy) == 1 else 'stories are'} skipped."
        if QMessageBox.question(self, "Delete stories", msg) != QMessageBox.Yes:
            return
        for sid in todo:
            try:
                stories.delete_story(sid)
            except stories.StoryBusyError:
                busy.append(sid)
        self.error.setText(f"Skipped {len(busy)} rendering {'story' if len(busy) == 1 else 'stories'}." if busy else "")
        QTimer.singleShot(0, self.refresh)

    def _mark_uploaded(self, story_id):
        url, ok = QInputDialog.getText(self, "Mark as uploaded",
                                       "You uploaded this video yourself.\nYouTube link (optional):")
        if not ok:
            return
        stories.mark_uploaded(story_id, url)
        QTimer.singleShot(0, self.refresh)   # after the card's menu has closed: refresh deletes the card

    def _delete_story(self, story_id):
        with db.Session() as s:
            st = s.get(db.Story, story_id)
            if st is None:
                return
            title, export_path, on_youtube = st.title or "Untitled", st.export_path, bool(st.youtube_video_id)
        notes = ["Its scenes, images, voice clips and video inside the app will be removed."]
        if export_path and Path(export_path).exists():
            notes.append("The copy in your output folder is kept.")
        if on_youtube:
            notes.append("The video on YouTube is not affected.")
        if QMessageBox.question(self, "Delete story", f"Delete “{title}”?\n\n" + "\n".join(notes)) \
                != QMessageBox.Yes:
            return
        try:
            stories.delete_story(story_id)
        except stories.StoryBusyError as e:
            self.error.setText(str(e))
            return
        QTimer.singleShot(0, self.refresh)   # the card's menu is still open: refresh deletes the card

    def _unmark_uploaded(self, story_id):
        stories.unmark_uploaded(story_id)
        QTimer.singleShot(0, self.refresh)

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

    def _next(self):
        self._create(review=True)

    def _create(self, review: bool = False):
        content = self.script.toPlainText().strip()
        if not content:
            self.error.setText("The script is empty.")
            return
        if len(content) > SCRIPT_LIMIT:
            self.error.setText(f"The script is over {SCRIPT_LIMIT} characters. Shorten it to keep render times sane.")
            return
        self._review = review
        for b in (self.create_btn, self.next_btn):
            b.setEnabled(False)
        self._busy(self.next_btn if review else self.create_btn, "Planning scenes…")
        run_async(create_story, self.title.text().strip() or self.topic.text().strip(), content,
                  self.style.currentData(), self.talking.currentData(), self.aspect_ratio, settings.load(), self._yt,
                  voice_sample=self.voice.value(), image_style=self.image_style.currentData(),
                  image_provider=self.image_source.currentData() or None,
                  on_done=self._created, on_error=self._create_failed)

    def _reset_buttons(self):
        for b, text in ((self.create_btn, "Create && Render"), (self.next_btn, "Next: review images")):
            b.setEnabled(True)
            b.setText(text)

    def _created(self, story_id):
        self._reset_buttons()
        self.title.clear()
        self.script.clear()
        self._yt = {}
        if self._review:
            self.bridge.submit_review(story_id)
        else:
            self.bridge.submit_render(story_id)
        self.refresh()
        self.open_story(story_id)

    def _create_failed(self, e):
        self._reset_buttons()
        self.error.setText(str(e))
