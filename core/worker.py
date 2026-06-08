from PyQt6.QtCore import QThread, pyqtSignal
from core.pipeline import jalankan_pipeline
import traceback    

class PipelineWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, path, threshold, window, jarak_min, min_peak):
        super().__init__()
        self.path      = path
        self.threshold = threshold
        self.window    = window
        self.jarak_min = jarak_min
        self.min_peak  = min_peak

    def run(self):
        try:
            hasil = jalankan_pipeline(
                self.path,
                threshold=self.threshold,
                window=self.window,
                jarak_min=self.jarak_min,
                min_peak=self.min_peak,
                progress_cb=lambda n: self.progress.emit(n),
            )
            self.finished.emit(hasil)
        except Exception as e:
            self.error.emit(traceback.format_exc())