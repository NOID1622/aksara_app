from PyQt6.QtCore import QThread, pyqtSignal
from core.pipeline import jalankan_pipeline


class PipelineWorker(QThread):
    """Jalankan pipeline segmentasi di thread terpisah agar UI tidak freeze."""

    progress = pyqtSignal(int)      # 0–100
    finished = pyqtSignal(dict)     # hasil pipeline
    error    = pyqtSignal(str)      # pesan error jika gagal

    def __init__(self, path: str, threshold: int):
        super().__init__()
        self.path      = path
        self.threshold = threshold

    def run(self):
        try:
            hasil = jalankan_pipeline(
                self.path,
                threshold=self.threshold,
                progress_cb=lambda n: self.progress.emit(n),
            )
            self.finished.emit(hasil)
        except Exception as e:
            self.error.emit(str(e))
