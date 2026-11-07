"""YouTube section of the story screen: channel, metadata, publish time, upload."""
from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QDateTimeEdit, QFormLayout, QGroupBox, QHBoxLayout,
                               QInputDialog,
                               QLabel, QLineEdit, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)

from desktop.core import db, settings
from desktop.services import stories, story_ai, youtube
from desktop.ui.tasks import run_async

STATUS_TEXT = {"manual": "Uploaded by you", None: "Not uploaded", "uploading": "Uploading…", "scheduled": "Uploaded privately — goes public at {when}",
               "completed": "Published", "failed": "Upload failed"}


class YouTubePanel(QGroupBox):
    def __init__(self, upload_fn=None):
        super().__init__("YouTube")
        self.setCheckable(True)
        self.setChecked(False)          # collapsed by default; tick to expand
        self.story_id = None
        self.channel = QComboBox()
        self.title = QLineEdit(placeholderText="YouTube title")
        self.description = QPlainTextEdit(fixedHeight=80, placeholderText="Description")
        self.tags = QLineEdit(placeholderText="tags, separated, by commas")
        when_row = QHBoxLayout()
        self.now = QRadioButton("Publish right away", checked=True)
        self.later = QRadioButton("Publish at")
        grp = QButtonGroup(self)
        for b in (self.now, self.later):
            grp.addButton(b)
        self.when = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600), displayFormat="yyyy-MM-dd HH:mm",
                                  calendarPopup=True)
        for w in (self.now, self.later, self.when):
            when_row.addWidget(w)
        when_row.addStretch()
        buttons = QHBoxLayout()
        self.meta_btn = QPushButton("✨ Generate title && tags", clicked=self._generate)
        self.save_btn = QPushButton("Save", clicked=self.save)
        self.upload_btn = QPushButton("Upload to YouTube", objectName="primary", clicked=self._upload)
        self.manual_btn = QPushButton("I uploaded it myself…", clicked=self._toggle_manual,
                                      toolTip="Already uploaded it in YouTube Studio? Mark it so the app won't upload it")
        for b in (self.meta_btn, self.save_btn, self.upload_btn, self.manual_btn):
            buttons.addWidget(b)
        buttons.addStretch()
        self.progress = QProgressBar(textVisible=False)
        self.progress.hide()
        self.status = QLabel(objectName="muted", wordWrap=True, openExternalLinks=True)

        self.body = QWidget()
        form = QFormLayout(self.body)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.addRow("Channel", self.channel)
        form.addRow("Title", self.title)
        form.addRow("Description", self.description)
        form.addRow("Tags", self.tags)
        form.addRow("When", when_row)
        form.addRow(buttons)
        form.addRow(self.progress)
        form.addRow(self.status)
        QVBoxLayout(self).addWidget(self.body)
        self.toggled.connect(self.body.setVisible)   # tick the group title to expand
        self.body.setVisible(False)

    def load(self, story_id):
        self.story_id = story_id
        self.channel.clear()
        self.channel.addItem("Choose a channel…", None)
        with db.Session() as s:
            for ch in s.query(db.Channel).order_by(db.Channel.id):
                self.channel.addItem(ch.title or ch.channel_id, ch.id)
            st = s.get(db.Story, story_id)
            self.channel.setCurrentIndex(max(0, self.channel.findData(st.channel_id)))
            self.title.setText(st.youtube_title or st.title or "")
            self.description.setPlainText(st.youtube_description or "")
            self.tags.setText(st.youtube_tags or "")
            if st.publish_at and st.publish_at > datetime.now():
                self.later.setChecked(True)
                self.when.setDateTime(st.publish_at)
            else:
                self.now.setChecked(True)
        self.refresh_status()

    def refresh_status(self):
        if self.story_id is None:
            return
        with db.Session() as s:
            st = s.get(db.Story, self.story_id)
            text = STATUS_TEXT.get(st.youtube_upload_status, st.youtube_upload_status or "")
            text = text.format(when=st.publish_at.strftime("%b %d %H:%M") if st.publish_at else "")
            if st.youtube_video_id:
                url = youtube.video_url(st.youtube_video_id)
                text += f' · <a style="color:#22d3ee" href="{url}">{url}</a>'
            if st.youtube_upload_status == "failed" and st.youtube_error:
                text += f"<br><span style='color:#f87171'>{st.youtube_error}</span>"
            ready = st.status == "done" and bool(st.final_path)
            busy = st.youtube_upload_status == "uploading"
            self.upload_btn.setEnabled(ready and not busy)
            self.upload_btn.setText("Upload again" if st.youtube_video_id else "Upload to YouTube")
            manual = st.youtube_upload_status == "manual"
            self.manual_btn.setText("Mark as not uploaded" if manual else "I uploaded it myself…")
            self.manual_btn.setVisible(manual or st.youtube_upload_status in (None, "failed"))
            if not ready:
                text += " · render the video first"
        self.status.setText(text)

    def _toggle_manual(self):
        with db.Session() as s:
            manual = s.get(db.Story, self.story_id).youtube_upload_status == "manual"
        if manual:
            stories.unmark_uploaded(self.story_id)
        else:
            url, ok = QInputDialog.getText(self, "Mark as uploaded",
                                           "You uploaded this video yourself.\nYouTube link (optional):")
            if not ok:
                return
            stories.mark_uploaded(self.story_id, url)
        self.refresh_status()

    def save(self):
        with db.Session() as s:
            st = s.get(db.Story, self.story_id)
            st.channel_id = self.channel.currentData()
            st.youtube_title = self.title.text().strip()
            st.youtube_description = self.description.toPlainText().strip()
            st.youtube_tags = self.tags.text().strip()
            st.publish_at = self.when.dateTime().toPython().replace(second=0, microsecond=0) \
                if self.later.isChecked() else None
            s.commit()

    def _generate(self):
        with db.Session() as s:
            content = s.get(db.Story, self.story_id).content
        self.meta_btn.setEnabled(False)

        def done(meta):
            self.meta_btn.setEnabled(True)
            self.title.setText(meta.get("youtube_title", ""))
            self.description.setPlainText(meta.get("youtube_description", ""))
            self.tags.setText(meta.get("youtube_tags", ""))

        run_async(story_ai.generate_metadata, settings.load(), content, on_done=done,
                  on_error=lambda e: (self.meta_btn.setEnabled(True), self.status.setText(str(e))))

    def _upload(self):
        if self.channel.currentData() is None:
            self.status.setText("Choose a channel first (connect one on the YouTube Channels page).")
            return
        self.save()
        with db.Session() as s:
            st = s.get(db.Story, self.story_id)
            st.youtube_upload_status, st.youtube_error, st.youtube_video_id = "uploading", None, None
            s.commit()
        story_id = self.story_id
        self.progress.setRange(0, 0)   # busy indicator while the upload thread runs
        self.progress.show()
        self.refresh_status()

        def finished(*_):
            self.progress.hide()
            self.refresh_status()

        run_async(youtube.upload, settings.load(), db.Session, story_id, on_done=finished, on_error=finished)
