from PyQt6.QtCore import QThread, pyqtSignal


class VaultWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, func, *args, parent=None):
        super().__init__(parent)
        self._func = func
        self._args = args

    def run(self):
        try:
            result = self._func(*self._args, progress_cb=self.report)
            self.finished.emit(bool(result), "")
        except TypeError:
            result = self._func(*self._args)
            self.finished.emit(bool(result), "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def report(self, pct: int, msg: str):
        self.progress.emit(pct, msg)
