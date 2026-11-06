"""Connects the worker process to Qt: polls its event queue and re-emits events as signals."""
from PySide6.QtCore import QObject, QTimer, Signal

from desktop.core import db
from desktop.pipeline.worker import WorkerHandle, recover_interrupted


class WorkerBridge(QObject):
    event = Signal(dict)
    storyChanged = Signal(int)
    sceneChanged = Signal(int, int)       # story_id, scene_id
    stateChanged = Signal(str)            # starting | loading | idle | busy | crashed
    workerCrashed = Signal(str)

    def __init__(self, data_dir, parent=None):
        super().__init__(parent)
        self.handle = WorkerHandle(data_dir)
        self.state = "stopped"
        self.current_story = None
        self._pending = 0
        self._poll = QTimer(self, interval=100, timeout=self._drain)
        self._watch = QTimer(self, interval=2000, timeout=self._check_alive)

    def _set_state(self, state):
        if state != self.state:
            self.state = state
            self.stateChanged.emit(state)

    def start(self):
        self.handle.start()
        self._set_state("starting")
        self._poll.start()
        self._watch.start()

    def stop(self):
        self._poll.stop()
        self._watch.stop()
        self.handle.stop()
        self._set_state("stopped")

    @property
    def busy(self) -> bool:
        return self._pending > 0

    def _submit(self, kind, target_story, **kw):
        with db.Session() as s:
            st = s.get(db.Story, target_story)
            if st and st.status != "rendering":
                st.status = "queued"
                s.commit()
        self._pending += 1
        self.handle.submit(kind, **kw)
        self.storyChanged.emit(target_story)
        if self.state == "idle":
            self._set_state("busy")

    def submit_render(self, story_id: int):
        self._submit("render_story", story_id, story_id=story_id)

    def submit_redo(self, story_id: int, scene_id: int, from_stage: str):
        self._submit("redo_scene", story_id, scene_id=scene_id, from_stage=from_stage)

    def _drain(self):
        for ev in self.handle.events():
            t = ev.get("type")
            if t == "worker_ready":
                self._set_state("busy" if self._pending else "idle")
            elif t == "job_started":
                self._set_state("busy")
            elif t == "job_done":
                self._pending = max(0, self._pending - 1)
                if not self._pending:
                    self.current_story = None
                    self._set_state("idle")
            elif t == "story":
                self.current_story = ev["story_id"]
                self.storyChanged.emit(ev["story_id"])
            elif t == "stage":
                self.sceneChanged.emit(ev["story_id"], ev["scene_id"])
            elif t in ("assemble", "job_error") and ev.get("story_id"):
                self.storyChanged.emit(ev["story_id"])
            self.event.emit(ev)

    def _check_alive(self):
        if self.state in ("stopped", "starting") or self.handle.is_alive():
            return
        story = self.current_story
        recover_interrupted(db.Session)
        self._pending = 0
        self.current_story = None
        self._set_state("crashed")
        self.workerCrashed.emit(f"The render worker stopped unexpectedly (exit code {self.handle.proc.exitcode}). Restarted it.")
        self.handle.restart()
        self._set_state("starting")
        if story:
            self.storyChanged.emit(story)
