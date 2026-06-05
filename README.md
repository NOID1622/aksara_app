# Segmentasi Aksara — Aplikasi PyQt6

Aplikasi GUI untuk segmentasi baris aksara dari gambar manuskrip PNG.
Seluruh pipeline dibangun dari nol tanpa OpenCV/Pillow.

## Struktur Proyek

```
aksara_app/
├── main.py                  ← Jalankan ini
├── core/
│   ├── pipeline.py          ← Semua logika dari 1.py, 2.py, 3.py
│   └── worker.py            ← QThread background
└── ui/
    ├── main_window.py       ← Jendela utama
    ├── image_viewer.py      ← Tampilan gambar + zoom
    ├── settings_panel.py    ← Panel kontrol kanan
    └── result_gallery.py    ← Grid thumbnail baris
```

## Instalasi

```bash
pip install PyQt6
```

Tidak butuh OpenCV, Pillow, atau NumPy — murni Python + PyQt6.

## Cara Pakai

```bash
cd aksara_app
python main.py
```

1. Klik **📂 Buka Gambar** → pilih file PNG
2. Atur **Threshold** (default 170) di panel kanan
3. Klik **▶ Jalankan Segmentasi**
4. Lihat hasil baris di galeri bawah
5. Klik baris untuk sorot & lihat detail
6. Gunakan tombol di toolbar untuk ganti mode tampilan:
   - **Asli** → RGB asli
   - **Grayscale** → hasil konversi
   - **Biner** → setelah threshold + flood-fill
   - **Cuts** → biner + garis merah pemotong baris
7. Klik **💾 Ekspor** untuk simpan tiap baris sebagai `.ppm`

## Parameter

| Parameter | Fungsi | Default |
|---|---|---|
| Threshold | Batas binerisasi (piksel < nilai = tinta) | 170 |
| Window smoothing | Lebar moving-average proyeksi | 11 |
| Min. tinggi peak | Nilai minimum proyeksi dianggap baris | 20 |

## Asal Kode

Pipeline langsung dari kode pengguna:
- `1.py` → decode PNG raw + grayscale + binerisasi
- `2.py` → flood-fill hapus noise tepi
- `3.py` → proyeksi horizontal + potong baris


file build berada di dist folder

edit file

try to build again with:
python -m PyInstaller --onefile --windowed --name "SegmentasiAksara" --icon=icons/app.ico --add-data "icons;icons" --add-data "icon.svg;." main.py