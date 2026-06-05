from utils import resource_path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QProgressBar, QFrame,
    QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QFontDatabase

class SettingsPanel(QWidget):
    run_requested = pyqtSignal(int)   # threshold value

    def __init__(self):
        super().__init__()
        QFontDatabase.addApplicationFont(
            resource_path(
                "fonts/Acuentre Personal Use Only.ttf"
            )
        )
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QWidget { background: #14103A; color: #f0ecff; }
            QLabel  { color: #c9b8e8; font-size: 12px; }
            QGroupBox {
                color: #FFCA5A; font-weight: bold; font-size: 12px;
                border: 1px solid #443357; border-radius: 8px;
                margin-top: 8px; padding: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton {
                background: #F4603A; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover   { background: #ff7a56; }
            QPushButton:pressed { background: #d94e2a; }
            QPushButton:disabled { background: #2e2050; color: #5a4a70; }
            QSlider::groove:horizontal {
                height: 4px; background: #2e2050; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -5px 0;
                background: #F4603A; border-radius: 7px;
            }
            QSlider::sub-page:horizontal { background: #F4603A; border-radius: 2px; }
            QProgressBar {
                border: 1px solid #443357; border-radius: 4px;
                background: #2e2050; height: 8px; text-align: center;
            }
            QProgressBar::chunk { background: #FFCA5A; border-radius: 4px; }
            QSpinBox {
                background: #2e2050; border: 1px solid #443357;
                border-radius: 4px; padding: 2px 6px; color: #f0ecff;
            }
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(14)

        # ── Judul ──
        title = QLabel("Segmentasi Aksara")
        title.setStyleSheet("font-family: 'Acuentre Personal Use Only';color: #FFCA5A; font-size: 36px; font-weight: bold;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #443357;")
        layout.addWidget(sep)

        # ── Preprocessing ──
        grp_pre = QGroupBox("Preprocessing")
        pre_lay = QVBoxLayout(grp_pre)
        pre_lay.setSpacing(8)

        self._threshold_val = QLabel("Threshold:  170")
        pre_lay.addWidget(self._threshold_val)

        self._threshold = QSlider(Qt.Orientation.Horizontal)
        self._threshold.setRange(50, 250)
        self._threshold.setValue(170)
        self._threshold.valueChanged.connect(
            lambda v: self._threshold_val.setText(f"Threshold:  {v}")
        )
        pre_lay.addWidget(self._threshold)
        layout.addWidget(grp_pre)

        # ── Proyeksi ──
        grp_proj = QGroupBox("Proyeksi Baris")
        proj_lay = QVBoxLayout(grp_proj)
        proj_lay.setSpacing(8)

        proj_lay.addWidget(QLabel("Window smoothing"))
        self._smooth_win = QSlider(Qt.Orientation.Horizontal)
        self._smooth_win.setRange(3, 31)
        self._smooth_win.setSingleStep(2)
        self._smooth_win.setValue(11)
        self._smooth_lbl = QLabel("11")
        self._smooth_win.valueChanged.connect(
            lambda v: self._smooth_lbl.setText(str(v))
        )
        row = QHBoxLayout()
        row.addWidget(self._smooth_win)
        row.addWidget(self._smooth_lbl)
        proj_lay.addLayout(row)

        proj_lay.addWidget(QLabel("Min. tinggi peak"))
        self._min_peak = QSlider(Qt.Orientation.Horizontal)
        self._min_peak.setRange(1, 100)
        self._min_peak.setValue(20)
        self._peak_lbl = QLabel("20")
        self._min_peak.valueChanged.connect(
            lambda v: self._peak_lbl.setText(str(v))
        )
        row2 = QHBoxLayout()
        row2.addWidget(self._min_peak)
        row2.addWidget(self._peak_lbl)
        proj_lay.addLayout(row2)

        layout.addWidget(grp_proj)

        # ── Tombol run ──
        self._run_btn = QPushButton("▶  Jalankan Segmentasi")
        self._run_btn.setEnabled(False)
        self._run_btn.clicked.connect(self._emit)
        layout.addWidget(self._run_btn)

        # ── Progress ──
        self._progress = QProgressBar()
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        # ── Status info ──
        self._info_lbl = QLabel("Belum ada gambar")
        self._info_lbl.setWordWrap(True)
        self._info_lbl.setStyleSheet("color: #7a6a90; font-size: 11px;")
        layout.addWidget(self._info_lbl)

        layout.addStretch()
        

        # ── Ekspor ──
        self._export_btn = QPushButton()
        self._export_btn.setIcon(
            QIcon(
                resource_path("icons/diskette.png")
            )
        )
        self._export_btn.setIconSize(QSize(18, 18))
        self._export_btn.setText("  Ekspor Baris (.ppm)")
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet(
            "QPushButton { background: #443357; color: #c9b8e8; border-radius: 6px; padding: 7px; }"
            "QPushButton:hover { background: #5a4470; }"
            "QPushButton:disabled { background: #14103A; color: #3a2a50; }"
        )
        layout.addWidget(self._export_btn)

    # ── Public API ──────────────────────────────

    def aktifkan_run(self, aktif: bool):
        self._run_btn.setEnabled(aktif)

    def aktifkan_ekspor(self, aktif: bool):
        self._export_btn.setEnabled(aktif)

    def set_progress(self, val: int):
        self._progress.setValue(val)

    def set_info(self, teks: str):
        self._info_lbl.setText(teks)

    def get_threshold(self) -> int:
        return self._threshold.value()

    def get_smooth_window(self) -> int:
        v = self._smooth_win.value()
        return v if v % 2 == 1 else v + 1

    def get_min_peak(self) -> int:
        return self._min_peak.value()

    @property
    def ekspor_btn(self):
        return self._export_btn

    def _emit(self):
        self.run_requested.emit(self._threshold.value())

# documentation

def _tampil_about(self):
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
    
    dialog = QDialog(self)
    dialog.setWindowTitle("Tentang Aplikasi")
    dialog.setFixedSize(320, 280)
    dialog.setStyleSheet("""
        QDialog { background: #14103A; }
        QLabel  { color: #c9b8e8; }
    """)

    lay = QVBoxLayout(dialog)
    lay.setSpacing(10)
    lay.setContentsMargins(24, 24, 24, 24)

    judul = QLabel("Segmentasi Aksara")
    judul.setStyleSheet("color: #FFCA5A; font-size: 16px; font-weight: bold; font-family: 'Acuentre';")
    lay.addWidget(judul)

    versi = QLabel("Versi 1.0.0")
    versi.setStyleSheet("color: #443357; font-size: 11px;")
    lay.addWidget(versi)

    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("color: #443357;")
    lay.addWidget(sep)

    for teks in [
        "👤 Nama Anda",
        "🏫 Universitas / Instansi",
        "📧 email@contoh.com",
        "📅 2025",
    ]:
        lbl = QLabel(teks)
        lbl.setStyleSheet("color: #c9b8e8; font-size: 12px;")
        lay.addWidget(lbl)

    lay.addStretch()

    deskripsi = QLabel(
        "Aplikasi segmentasi baris aksara dari gambar\n"
        "manuskrip PNG menggunakan pipeline murni Python."
    )
    deskripsi.setWordWrap(True)
    deskripsi.setStyleSheet("color: #7a6a90; font-size: 11px;")
    lay.addWidget(deskripsi)

    dialog.exec()