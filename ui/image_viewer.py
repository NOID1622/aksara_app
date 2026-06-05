from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt6.QtGui import (
    QPen, QColor, QPixmap, QImage, QPainter
)
from PyQt6.QtCore import Qt, QRectF
import struct


def biner_ke_qimage(biner, lebar, tinggi):
    """Konversi matriks biner ke QImage (grayscale 8-bit)."""
    img = QImage(lebar, tinggi, QImage.Format.Format_RGB32)
    for y in range(tinggi):
        for x in range(lebar):
            v = 0 if biner[y][x] == 1 else 255
            img.setPixel(x, y, (v << 16) | (v << 8) | v)
    return img


def gray_ke_qimage(gray, lebar, tinggi):
    """Konversi matriks grayscale ke QImage."""
    img = QImage(lebar, tinggi, QImage.Format.Format_RGB32)
    for y in range(tinggi):
        for x in range(lebar):
            v = gray[y][x]
            img.setPixel(x, y, (v << 16) | (v << 8) | v)
    return img


def rgb_ke_qimage(pixel, lebar, tinggi):
    """Konversi matriks pixel RGB ke QImage."""
    img = QImage(lebar, tinggi, QImage.Format.Format_RGB32)
    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = pixel[y][x]
            img.setPixel(x, y, (r << 16) | (g << 8) | b)
    return img


class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundRole(self.backgroundRole())
        self.setStyleSheet("background: #0e0b2a; border: none;")
        self._line_items = []
        self._pixmap_item = None

    # ── tampilkan gambar ─────────────────────

    def tampilkan_qimage(self, qimg: QImage):
        self._scene.clear()
        self._line_items = []
        pix = QPixmap.fromImage(qimg)
        self._pixmap_item = self._scene.addPixmap(pix)
        self._scene.setSceneRect(QRectF(pix.rect()))
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def tampilkan_dengan_cuts(self, biner, lebar, tinggi, cuts):
        """
        Tampilkan citra biner + garis merah pada setiap titik potong.
        """
        qimg = biner_ke_qimage(biner, lebar, tinggi)
        self.tampilkan_qimage(qimg)

        pen = QPen(QColor("#FFCA5A"), 0)
        pen.setCosmetic(True)
        for y in cuts[1:-1]:
            item = self._scene.addLine(0, y, lebar, y, pen)
            self._line_items.append(item)

    # ── zoom ─────────────────────────────────

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(1 / 1.25, 1 / 1.25)

    def zoom_fit(self):
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
