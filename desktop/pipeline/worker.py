"""The long-lived worker process: holds the voice model, runs one job at a time, emits events.

UI side uses WorkerHandle; nothing here imports Qt."""
import itertools
import multiprocessing as mp
import os
import queue
import traceback

from desktop.core import db, settings


def worker_main(job_q, event_q, data_dir: str) -> None:
    os.environ["VC_DATA_DIR"] = str(data_dir)
    from desktop.pipeline import jobs, voice
    db.reset_engine()
    db.init_db()
    emit = event_q.put
    emit({"type": "worker_ready", "pid": os.getpid()})
    while True:
        job = job_q.get()
        if job is None:
            break
        job_id, kind, kw = job["job_id"], job["kind"], job["kwargs"]
        emit({"type": "job_started", "job_id": job_id, "kind": kind, **kw})
        try:
            cfg = settings.load()  # re-read each job so Settings changes apply without restart
            engine = voice.get_engine(cfg)  # cheap: the voice model itself stays loaded
            if kind == "render_story":
                jobs.render_story(db.Session, kw["story_id"], emit, cfg, engine)
            elif kind == "redo_scene":
                jobs.redo_scene(db.Session, kw["scene_id"], kw.get("from_stage", "image"), emit, cfg, engine)
            else:
                raise ValueError(f"unknown job kind: {kind}")
        except Exception as e:
            emit({"type": "job_error", "job_id": job_id, "error": f"{type(e).__name__}: {e}",
                  "traceback": traceback.format_exc()})
        emit({"type": "job_done", "job_id": job_id})


class WorkerHandle:
    """Owns the worker process and its two queues."""

    def __init__(self, data_dir):
        self.data_dir = str(data_dir)
        self._ctx = mp.get_context("spawn")
        self._ids = itertools.count(1)
        self.proc = None

    def start(self) -> None:
        self.job_q = self._ctx.Queue()
        self.event_q = self._ctx.Queue()
        self.proc = self._ctx.Process(target=worker_main, args=(self.job_q, self.event_q, self.data_dir),
                                      daemon=True, name="vc-worker")
        self.proc.start()

    def submit(self, kind: str, **kwargs) -> int:
        job_id = next(self._ids)
        self.job_q.put({"job_id": job_id, "kind": kind, "kwargs": kwargs})
        return job_id

    def events(self) -> list[dict]:
        out = []
        while True:
            try:
                out.append(self.event_q.get_nowait())
            except queue.Empty:
                return out

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.is_alive()

    def stop(self, timeout: float = 10) -> None:
        if not self.proc:
            return
        if self.proc.is_alive():
            self.job_q.put(None)
            self.proc.join(timeout)
        if self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(5)

    def restart(self) -> None:
        self.stop(timeout=2)
        self.start()


def recover_interrupted(Session) -> int:
    """After a crash or quit mid-render: stories 'rendering' -> failed/interrupted, running stages -> pending."""
    with Session() as s:
        stuck = s.query(db.Story).filter(db.Story.status.in_(["rendering", "queued"])).all()
        for st in stuck:
            st.status, st.error = "failed", "interrupted"
        for sc in s.query(db.Scene).all():
            for stage in db.STAGES:
                if getattr(sc, f"{stage}_status") == "running":
                    setattr(sc, f"{stage}_status", "pending")
        s.commit()
        return len(stuck)
