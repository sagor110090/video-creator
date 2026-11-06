"""Runs due schedules, uploads and publishes every minute while the app is open."""
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

from desktop.core import db, settings
from desktop.services import scheduler, youtube
from desktop.ui.tasks import run_async


class SchedulerRunner(QObject):
    message = Signal(str)          # short status for the status bar
    changed = Signal()             # something in the DB changed (refresh pages)

    def __init__(self, bridge, interval_ms=60_000, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.in_flight: set[tuple[str, int]] = set()
        self.timer = QTimer(self, interval=interval_ms, timeout=self.tick)

    def start(self):
        self.timer.start()
        QTimer.singleShot(3000, self.tick)   # catch up on anything missed while the app was closed

    def tick(self):
        now, cfg = datetime.now(), settings.load()
        for sid in scheduler.due_schedules(db.Session, now):
            self._run(("schedule", sid), scheduler.run_schedule, cfg, db.Session, sid, now,
                      done=lambda story_id: self.bridge.submit_render(story_id),
                      text="Schedule: writing today's story…")
        for story_id in scheduler.due_uploads(db.Session, now):
            self._run(("upload", story_id), youtube.upload, cfg, db.Session, story_id,
                      text=f"Uploading story {story_id} to YouTube…")
        for story_id in scheduler.due_publishes(db.Session, now):
            self._run(("publish", story_id), youtube.publish, cfg, db.Session, story_id,
                      text=f"Publishing story {story_id} on YouTube…")

    def _run(self, key, fn, *args, done=None, text=""):
        if key in self.in_flight:
            return
        self.in_flight.add(key)
        self.message.emit(text)

        def finished(result):
            self.in_flight.discard(key)
            if done:
                done(result)
            self.changed.emit()

        def failed(err):
            self.in_flight.discard(key)
            self.message.emit(f"{key[0].capitalize()} failed: {err}")
            self.changed.emit()

        run_async(fn, *args, on_done=finished, on_error=failed)
