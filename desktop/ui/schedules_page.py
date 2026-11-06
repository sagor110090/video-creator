"""Recurring schedules: a new AI story every day at a set time (optionally uploaded to a channel)."""
from datetime import datetime

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox, QFormLayout, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QPushButton, QRadioButton, QTableWidget,
                               QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget)

from desktop.core import db, settings, voices
from desktop.services import scheduler, story_ai
from desktop.ui.tasks import run_async
from desktop.ui.voice_picker import VoicePicker

COLUMNS = ["Topic", "Style", "Format", "Voice", "Daily at", "Channel", "Last run", "Status"]


class SchedulesPage(QWidget):
    COLUMNS = COLUMNS

    def __init__(self, bridge):
        super().__init__(objectName="page")
        self.bridge = bridge

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        actions = QHBoxLayout()
        self.run_btn = QPushButton("Run now", clicked=self._run_now)
        self.pause_btn = QPushButton("Pause / Resume", clicked=self._toggle)
        self.delete_btn = QPushButton("Delete", clicked=self._delete)
        for b in (self.run_btn, self.pause_btn, self.delete_btn):
            actions.addWidget(b)
        actions.addStretch()
        self.message = QLabel(objectName="muted", wordWrap=True)

        card = QFrame(objectName="card")
        form = QFormLayout(card)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.addRow(QLabel("New schedule", objectName="h2"))
        self.topic = QLineEdit(placeholderText="Topic or channel theme, e.g. space facts")
        self.style = QComboBox()
        for k, v in story_ai.STYLES.items():
            self.style.addItem(v, k)
        self.talking = QComboBox()
        for k, v in story_ai.TALKING_STYLES.items():
            self.talking.addItem(v, k)
        fmt = QHBoxLayout()
        self.landscape = QRadioButton("Landscape 16:9", checked=True)
        self.shorts = QRadioButton("Shorts 9:16")
        grp = QButtonGroup(self)
        for b in (self.landscape, self.shorts):
            grp.addButton(b)
            fmt.addWidget(b)
        fmt.addStretch()
        self.time = QTimeEdit(QTime(9, 0), displayFormat="HH:mm")
        self.channel = QComboBox()
        self.add_btn = QPushButton("Add schedule", objectName="primary", clicked=self._add)
        form.addRow("Topic", self.topic)
        form.addRow("Content style", self.style)
        form.addRow("Talking style", self.talking)
        form.addRow("Format", fmt)
        self.voice = VoicePicker()
        form.addRow("Voice", self.voice)
        form.addRow("Every day at", self.time)
        form.addRow("Upload to", self.channel)
        form.addRow("", self.add_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.addWidget(QLabel("Schedules", objectName="h1"))
        root.addWidget(QLabel("A new AI-written video is created every day at the set time while the app is open. "
                              "Anything missed while it was closed runs when you open it.", objectName="muted",
                              wordWrap=True))
        root.addWidget(self.table, 1)
        root.addLayout(actions)
        root.addWidget(self.message)
        root.addWidget(card)

    def refresh(self):
        self.voice.reload()
        self.channel.clear()
        self.channel.addItem("Don't upload", None)
        with db.Session() as s:
            channels = {c.id: c.title for c in s.query(db.Channel)}
            for cid, title in channels.items():
                self.channel.addItem(title or "Channel", cid)
            rows = s.query(db.Schedule).order_by(db.Schedule.scheduled_time).all()
            self.table.setRowCount(len(rows))
            for r, sch in enumerate(rows):
                status = sch.status if not sch.last_error else f"error: {sch.last_error[:60]}"
                values = [sch.topic, story_ai.STYLES.get(sch.style, sch.style),
                          "Shorts" if sch.aspect_ratio == "9:16" else "16:9",
                          voices.display_name(sch.voice_sample) if sch.voice_sample else "Default",
                          sch.scheduled_time.strftime("%H:%M"), channels.get(sch.channel_id, "—"),
                          str(sch.last_run_at or "never"), status]
                for c, v in enumerate(values):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.UserRole, sch.id)
                    if c == len(COLUMNS) - 1 and sch.last_error:
                        item.setToolTip(sch.last_error)
                    self.table.setItem(r, c, item)

    def _selected(self):
        items = self.table.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _add(self):
        topic = self.topic.text().strip()
        if not topic:
            self.message.setText("Enter a topic first.")
            return
        t = self.time.time()
        with db.Session() as s:
            s.add(db.Schedule(topic=topic, style=self.style.currentData(), talking_style=self.talking.currentData(),
                              aspect_ratio="9:16" if self.shorts.isChecked() else "16:9",
                              scheduled_time=datetime.strptime(t.toString("HH:mm"), "%H:%M").time(),
                              channel_id=self.channel.currentData(), voice_sample=self.voice.value(),
                              status="active"))
            s.commit()
        self.topic.clear()
        self.message.setText("Schedule added.")
        self.refresh()

    def _toggle(self):
        sid = self._selected()
        if sid is None:
            return
        with db.Session() as s:
            sch = s.get(db.Schedule, sid)
            sch.status = "paused" if sch.status == "active" else "active"
            s.commit()
        self.refresh()

    def _delete(self):
        sid = self._selected()
        if sid is None:
            return
        with db.Session() as s:
            s.delete(s.get(db.Schedule, sid))
            s.commit()
        self.refresh()

    def _run_now(self):
        sid = self._selected()
        if sid is None:
            self.message.setText("Select a schedule first.")
            return
        self.run_btn.setEnabled(False)
        self.message.setText("Writing the story with AI…")

        def done(story_id):
            self.run_btn.setEnabled(True)
            self.message.setText(f"Story {story_id} created and queued for rendering.")
            self.bridge.submit_render(story_id)
            self.refresh()

        def failed(e):
            self.run_btn.setEnabled(True)
            self.message.setText(f"Failed: {e}")
            self.refresh()

        run_async(scheduler.run_schedule, settings.load(), db.Session, sid, datetime.now(),
                  on_done=done, on_error=failed)
