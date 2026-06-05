from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QLabel,
    QVBoxLayout, QSizePolicy, QFrame
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal


def biner_ke_qimage_kecil(biner_crop, lebar, tinggi, max_w=300, max_h=80):
    """Buat QImage dari crop biner, scale agar muat di thumbnail."""
    skala = min(max_w / max(lebar, 1), max_h / max(tinggi, 1), 1.0)
    w = max(1, int(lebar * skala))
    h = max(1, int(tinggi * skala))

    img = QImage(w, h, QImage.Format.Format_RGB32)
    for py in range(h):
        sy = int(py / skala)
        sy = min(sy, tinggi - 1)
        for px in range(w):
            sx = int(px / skala)
            sx = min(sx, lebar - 1)
            v = 0 if biner_crop[sy][sx] == 1 else 255
            img.setPixel(px, py, (v << 16) | (v << 8) | v)
    return img


class BarisThumbnail(QFrame):
    diklik = pyqtSignal(int)

    def __init__(self, index: int, biner_crop, lebar, tinggi):
        super().__init__()
        self.index = index
        self.setStyleSheet("""
            QFrame {
                background: #1c1640;
                border: 1px solid #443357;
                border-radius: 6px;
            }
            QFrame:hover { border: 1px solid #F4603A; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # Label nomor
        lbl_no = QLabel(f"Baris {index + 1}")
        lbl_no.setStyleSheet("color: #7a6a90; font-size: 10px; border: none;")
        layout.addWidget(lbl_no)

        # Thumbnail gambar
        qimg = biner_ke_qimage_kecil(biner_crop, lebar, tinggi)
        pix_lbl = QLabel()
        pix_lbl.setPixmap(QPixmap.fromImage(qimg))
        pix_lbl.setStyleSheet("border: none;")
        layout.addWidget(pix_lbl)

        # Ukuran
        lbl_sz = QLabel(f"{lebar} × {tinggi} px")
        lbl_sz.setStyleSheet("color: #5a4a70; font-size: 10px; border: none;")
        layout.addWidget(lbl_sz)

    def mousePressEvent(self, _):
        self.diklik.emit(self.index)


class ResultGallery(QScrollArea):
    baris_dipilih = pyqtSignal(int)   # index baris

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("""
            QScrollArea { background: #14103A; border: none; }
            QScrollBar:vertical {
                background: #14103A; width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #443357; border-radius: 4px;
            }
        """)
        self.setMinimumHeight(160)

        container = QWidget()
        container.setStyleSheet("background: #14103A;")
        self._grid = QGridLayout(container)
        self._grid.setContentsMargins(10, 10, 10, 10)
        self._grid.setSpacing(10)

        self._placeholder = QLabel("Hasil segmentasi baris akan muncul di sini")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #3a2a50; font-size: 12px;")
        self._grid.addWidget(self._placeholder, 0, 0)

        self.setWidget(container)
        self._items = []

    def muat_baris(self, baris_list: list):
        # Hapus semua widget lama
        for item in self._items:
            self._grid.removeWidget(item)
            item.deleteLater()
        self._items = []

        if self._placeholder:
            self._placeholder.hide()

        cols = 3
        for i, b in enumerate(baris_list):
            thumb = BarisThumbnail(
                b["index"], b["biner_crop"], b["lebar"], b["tinggi"]
            )
            thumb.diklik.connect(self.baris_dipilih)
            row, col = divmod(i, cols)
            self._grid.addWidget(thumb, row, col)
            self._items.append(thumb)

    def sorot(self, index: int):
        for item in self._items:
            aktif = item.index == index
            item.setStyleSheet("""
                QFrame {
                    background: #1c1640;
                    border: 1px solid %s;
                    border-radius: 6px;
                }
            """ % ("#FFCA5A" if aktif else "#443357"))
