import os
from utils import resource_path
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QWidget as _W
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QToolBar, QFileDialog, QStatusBar,
    QLabel, QMessageBox, QSizePolicy, QPushButton
)
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtCore import Qt

from ui.image_viewer import ImageViewer, biner_ke_qimage, rgb_ke_qimage, gray_ke_qimage
from ui.settings_panel import SettingsPanel
from ui.result_gallery import ResultGallery
from core.worker import PipelineWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowIcon(QIcon("icon.svg"))
        self.setWindowIcon(
            QIcon(
                resource_path("icon.svg")
            )
        )
        self.setWindowTitle("Segmentasi Aksara")
        self.resize(1200, 800)
        self._hasil = None
        self._path  = None

        self.setStyleSheet("""
            QMainWindow { background: #14103A; }
            QToolBar {
                background: #1c1640;
                border-bottom: 1px solid #443357;
                spacing: 4px; padding: 4px 8px;
            }
            QToolButton {
                background: transparent; color: #c9b8e8;
                border: 1px solid transparent; border-radius: 5px;
                padding: 4px 10px; font-size: 12px;
            }
            QToolButton:hover   { background: #2e2050; border-color: #443357; }
            QToolButton:pressed { background: #443357; }
            QStatusBar { background: #1c1640; color: #7a6a90; font-size: 11px; }
            QSplitter::handle { background: #443357; }
        """)

        self._build_ui()
        self._build_toolbar()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Buka gambar aksara untuk memulai")

    # ── UI ────────────────────────────────────

    def _build_ui(self):
        splitter_v = QSplitter(Qt.Orientation.Vertical)
        splitter_v.setHandleWidth(3)

        # Baris atas: viewer + settings
        top = QSplitter(Qt.Orientation.Horizontal)
        top.setHandleWidth(3)

        self.viewer   = ImageViewer()
        self.settings = SettingsPanel()
        self.settings.run_requested.connect(self._jalankan)
        self.settings.ekspor_btn.clicked.connect(self._ekspor_ppm)

        top.addWidget(self.viewer)
        top.addWidget(self.settings)
        top.setSizes([900, 260])

        # Baris bawah: galeri hasil
        self.gallery = ResultGallery()
        self.gallery.baris_dipilih.connect(self._pilih_baris)

        splitter_v.addWidget(top)
        splitter_v.addWidget(self.gallery)
        splitter_v.setSizes([550, 200])

        self.setCentralWidget(splitter_v)

    def _build_toolbar(self):
        tb = QToolBar()
        tb.setIconSize(QSize(20, 20))
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(tb)
        
        def aksi_icon(icon_path, slot, tip=""):
            a = QAction(
                QIcon(resource_path(icon_path)),
                "",
                self
            )
            a.triggered.connect(slot)
            tb.addAction(a)
            a.setToolTip(tip)
            return a
        def aksi(label, slot, tip=""):
            a = QAction(label, self)
            a.triggered.connect(slot)
            tb.addAction(a)
            a.setToolTip(tip)
            return a

        aksi_icon("icons/folder.png", self._buka,"Buka file PNG gambar aksara")
        tb.addSeparator()
        self._act_zoom_in  = aksi_icon("icons/zoom-in.png", self.viewer.zoom_in, "Zoom in")
        self._act_zoom_out = aksi_icon("icons/zoom_out.png", self.viewer.zoom_out, "Zoom out")
        self._act_fit      = aksi_icon("icons/width.png",  self.viewer.zoom_fit, "Sesuaikan ke layar")
        tb.addSeparator()

        # Mode tampilan
        aksi_icon("icons/back.png",      self._tampil_asli,    "Tampilkan gambar asli RGB")
        aksi_icon("icons/grayscale.png", self._tampil_gray,    "Tampilkan grayscale")
        aksi_icon("icons/coding.png",    self._tampil_biner,   "Tampilkan citra biner")
        aksi_icon("icons/scissors.png",     self._tampil_cuts,    "Tampilkan garis pemotong baris")

        # Separator + info file
        tb.addSeparator()
        self._lbl_file = QLabel("  —")
        self._lbl_file.setStyleSheet("color: #7a6a90; font-size: 11px;")
        # Spacer untuk dorong ke kanan
        from PyQt6.QtWidgets import QWidget as _W
        spacer = _W()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        tb.addWidget(spacer)

        # Tombol about
        btn_about = QPushButton("ℹ")
        btn_about.setToolTip("Tentang Aplikasi")
        btn_about.setFixedSize(28, 28)
        btn_about.setStyleSheet("""
            QPushButton { 
                background: transparent; color: #7a6a90;
                border: none; font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { color: #FFCA5A; background: #2e2050; }
        """)
        btn_about.clicked.connect(self._tampil_about)
        tb.addWidget(btn_about)
        tb.addWidget(self._lbl_file)

    # ── Buka file ─────────────────────────────
    

    def _buka(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Buka Gambar Aksara", "",
            "PNG (*.png)"
        )
        if not path:
            return
        self._path  = path
        self._hasil = None
        self.settings.set_progress(0)
        self.settings.set_info(f"{os.path.basename(path)}")
        self.settings.aktifkan_run(True)
        self.settings.aktifkan_ekspor(False)
        self._lbl_file.setText(f"  {os.path.basename(path)}")

        # Preview gambar langsung pakai QPixmap (cepat)
        from PyQt6.QtGui import QPixmap
        pix = QPixmap(path)
        if not pix.isNull():
            self.viewer._scene.clear()
            self.viewer._scene.addPixmap(pix)
            from PyQt6.QtCore import QRectF
            self.viewer._scene.setSceneRect(QRectF(pix.rect()))
            self.viewer.fitInView(self.viewer._scene.sceneRect(),
                                  Qt.AspectRatioMode.KeepAspectRatio)

        self.statusBar().showMessage(f"Dibuka: {path}")

    # ── Jalankan pipeline ─────────────────────

    def _jalankan(self, threshold: int):
        if not self._path:
            return
        self.settings.aktifkan_run(False)
        self.statusBar().showMessage("Memproses pipeline segmentasi…")

        self._worker = PipelineWorker(self._path, threshold)
        self._worker.progress.connect(self.settings.set_progress)
        self._worker.finished.connect(self._selesai)
        self._worker.error.connect(self._error)
        self._worker.start()

    def _selesai(self, hasil: dict):
        self._hasil = hasil
        n = len(hasil["baris_list"])
        self.settings.aktifkan_run(True)
        self.settings.aktifkan_ekspor(True)
        self.settings.set_info(
            f"✔ {n} baris ditemukan\n"
            f"Ukuran: {hasil['lebar']} × {hasil['tinggi']} px"
        )
        self.gallery.muat_baris(hasil["baris_list"])
        self._tampil_cuts()
        self.statusBar().showMessage(
            f"Selesai — {n} baris tersegmentasi dari {os.path.basename(self._path)}"
        )

    def _error(self, pesan: str):
        self.settings.aktifkan_run(True)
        self.statusBar().showMessage(f"Error: {pesan}")
        QMessageBox.critical(self, "Error Pipeline", pesan)

    # ── Mode tampilan ─────────────────────────

    def _tampil_asli(self):
        if not self._hasil:
            return
        h = self._hasil
        qimg = rgb_ke_qimage(h["pixel_rgb"], h["lebar"], h["tinggi"])
        self.viewer.tampilkan_qimage(qimg)

    def _tampil_gray(self):
        if not self._hasil:
            return
        h = self._hasil
        qimg = gray_ke_qimage(h["gray"], h["lebar"], h["tinggi"])
        self.viewer.tampilkan_qimage(qimg)

    def _tampil_biner(self):
        if not self._hasil:
            return
        h = self._hasil
        qimg = biner_ke_qimage(h["biner_bersih"], h["lebar"], h["tinggi"])
        self.viewer.tampilkan_qimage(qimg)

    def _tampil_cuts(self):
        if not self._hasil:
            return
        h = self._hasil
        self.viewer.tampilkan_dengan_cuts(
            h["biner_bersih"], h["lebar"], h["tinggi"], h["cuts"]
        )

    # ── Pilih baris dari galeri ───────────────

    def _pilih_baris(self, index: int):
        self.gallery.sorot(index)
        if not self._hasil:
            return
        b = self._hasil["baris_list"][index]
        self.statusBar().showMessage(
            f"Baris {index + 1}: y={b['atas']}–{b['bawah']}, "
            f"ukuran {b['lebar']} × {b['tinggi']} px"
        )

    # ── Ekspor .ppm ───────────────────────────

    def _ekspor_ppm(self):
        if not self._hasil:
            return
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Ekspor")
        if not folder:
            return

        baris_list = self._hasil["baris_list"]
        for b in baris_list:
            nama = os.path.join(folder, f"line_{b['index']}.ppm")
            lebar  = b["lebar"]
            tinggi = b["tinggi"]
            with open(nama, "w") as f:
                f.write(f"P3\n{lebar} {tinggi}\n255\n")
                for y in range(tinggi):
                    for x in range(lebar):
                        c = 0 if b["biner_crop"][y][x] == 1 else 255
                        f.write(f"{c} {c} {c} ")
                    f.write("\n")

        QMessageBox.information(
            self, "Ekspor Selesai",
            f"{len(baris_list)} file .ppm disimpan ke:\n{folder}"
        )
        self.statusBar().showMessage(f"Diekspor {len(baris_list)} file ke {folder}")
        
    def _tampil_about(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame

        dialog = QDialog(self)
        dialog.setWindowTitle("Tentang Aplikasi")
        dialog.setFixedSize(320, 300)
        dialog.setStyleSheet("""
            QDialog { background: #14103A; }
            QLabel  { color: #c9b8e8; }
        """)

        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(24, 24, 24, 24)

        judul = QLabel("Segmentasi Aksara")
        judul.setStyleSheet("color: #FFCA5A; font-size: 16px; font-weight: bold;")
        lay.addWidget(judul)

        versi = QLabel("Versi 1.0.0")
        versi.setStyleSheet("color: #443357; font-size: 11px;")
        lay.addWidget(versi)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #443357;")
        lay.addWidget(sep)

        for teks in [
            "👤 github:NOID1622,dewaahr,MingPunyaGit",
            "UNIVERSITAS KRISTEN DUTA WACANA",
            "Mei 2026",
        ]:
            lbl = QLabel(teks)
            lbl.setStyleSheet("color: #c9b8e8; font-size: 12px;text-align: center;")
            lay.addWidget(lbl)

        lay.addStretch()

        deskripsi = QLabel(
            "Aplikasi segmentasi baris aksara dari gambar\n"
            "Tugas akhir kelas Digital Humanitas."
        )
        deskripsi.setWordWrap(True)
        deskripsi.setStyleSheet("color: #7a6a90; font-size: 11px; text-align: center;")
        lay.addWidget(deskripsi)

        dialog.exec()