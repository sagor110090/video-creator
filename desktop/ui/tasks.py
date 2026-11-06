"""Run blocking calls (network, AI) off the GUI thread; callbacks are delivered on the GUI thread."""
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

_live = set()  # keep task objects alive until they finish


class _Signals(QObject):
    done = Signal(object)
    error = Signal(object)
    finished = Signal()


class Task(QRunnable):
    def __init__(self, fn, args, kwargs):
        super().__init__()
        self.setAutoDelete(False)
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.signals = _Signals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.done.emit(result)
        finally:
            self.signals.finished.emit()


def run_async(fn, *args, on_done=None, on_error=None, **kwargs) -> Task:
    task = Task(fn, args, kwargs)
    if on_done:
        task.signals.done.connect(on_done)
    if on_error:
        task.signals.error.connect(on_error)
    _live.add(task)
    task.signals.finished.connect(lambda: _live.discard(task))
    QThreadPool.globalInstance().start(task)
    return task
