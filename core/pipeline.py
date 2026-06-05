"""
Pipeline segmentasi aksara — dibuat dari kode asli pengguna (1.py, 2.py, 3.py).
Semua logika dipertahankan, hanya dikemas ulang menjadi fungsi/kelas.
"""

import struct
import zlib


# ─────────────────────────────────────────────
# TAHAP 1  (dari 1.py) : Decode PNG → biner
# ─────────────────────────────────────────────

def baca_png(path: str):
    """
    Baca file PNG mentah tanpa library eksternal.
    Kembalikan (pixel_rgb, lebar, tinggi).
    pixel_rgb[y][x] = (r, g, b)
    """
    with open(path, "rb") as f:
        png_data = f.read()

    pos = 8
    lebar = tinggi = 0
    idat_data = b''

    while pos < len(png_data):
        panjang    = struct.unpack(">I", png_data[pos:pos+4])[0]; pos += 4
        tipe_chunk = png_data[pos:pos+4];                         pos += 4
        isi_chunk  = png_data[pos:pos+panjang];                   pos += panjang
        pos += 4  # CRC

        if tipe_chunk == b'IHDR':
            lebar  = struct.unpack(">I", isi_chunk[0:4])[0]
            tinggi = struct.unpack(">I", isi_chunk[4:8])[0]
        elif tipe_chunk == b'IDAT':
            idat_data += isi_chunk
        elif tipe_chunk == b'IEND':
            break

    rawdata = zlib.decompress(idat_data)

    pixel      = []
    pos_baca   = 0
    baris_atas = [0] * (lebar * 3)

    for y in range(tinggi):
        tipe_filter = rawdata[pos_baca]; pos_baca += 1
        rekon = []

        for x in range(lebar * 3):
            nilai     = rawdata[pos_baca]; pos_baca += 1
            kiri      = rekon[x - 3]      if x >= 3 else 0
            atas      = baris_atas[x]
            kiri_atas = baris_atas[x - 3] if x >= 3 else 0

            if tipe_filter == 0:
                hasil = nilai
            elif tipe_filter == 1:
                hasil = nilai + kiri
            elif tipe_filter == 2:
                hasil = nilai + atas
            elif tipe_filter == 3:
                hasil = nilai + ((kiri + atas) // 2)
            elif tipe_filter == 4:
                p       = kiri + atas - kiri_atas
                ja      = abs(p - kiri)
                jb      = abs(p - atas)
                jc      = abs(p - kiri_atas)
                if ja <= jb and ja <= jc:
                    predictor = kiri
                elif jb <= jc:
                    predictor = atas
                else:
                    predictor = kiri_atas
                hasil = nilai + predictor
            else:
                raise ValueError(f"Filter PNG tidak dikenal: {tipe_filter}")

            rekon.append(hasil % 256)

        baris_atas = rekon[:]
        pixel.append([(rekon[i], rekon[i+1], rekon[i+2]) for i in range(0, len(rekon), 3)])

    return pixel, lebar, tinggi


def ke_grayscale(pixel, lebar, tinggi):
    """Konversi pixel RGB ke grayscale (rata-rata aritmatik)."""
    gray = []
    for y in range(tinggi):
        baris = []
        for x in range(lebar):
            r, g, b = pixel[y][x]
            baris.append((r + g + b) // 3)
        gray.append(baris)
    return gray


def ke_biner(gray, lebar, tinggi, threshold=170):
    """Binerisasi: piksel < threshold → 1 (tinta), sisanya → 0 (latar)."""
    return [[1 if g < threshold else 0 for g in baris] for baris in gray]


# ─────────────────────────────────────────────
# TAHAP 2  (dari 2.py) : Flood-fill hapus noise
# ─────────────────────────────────────────────

def hapus_noise_tepi(biner, lebar, tinggi):
    """
    Flood-fill dari seluruh tepi gambar untuk menghapus
    komponen yang menyentuh bingkai (noise border).
    """
    # Salin agar tidak merusak data asli
    b = [row[:] for row in biner]
    check = [[False] * lebar for _ in range(tinggi)]

    def flood_fill(start_x, start_y):
        stack = [(start_x, start_y)]
        while stack:
            x, y = stack.pop()
            if x < 0 or x >= lebar or y < 0 or y >= tinggi:
                continue
            if check[y][x]:
                continue
            check[y][x] = True
            if b[y][x] == 0:
                continue
            b[y][x] = 0
            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))

    for y in range(tinggi):
        if b[y][0]         == 1: flood_fill(0,         y)
        if b[y][lebar - 1] == 1: flood_fill(lebar - 1, y)
    for x in range(lebar):
        if b[0][x]          == 1: flood_fill(x, 0)
        if b[tinggi - 1][x] == 1: flood_fill(x, tinggi - 1)

    return b


# ─────────────────────────────────────────────
# TAHAP 3  (dari 3.py) : Proyeksi & potong baris
# ─────────────────────────────────────────────

def smooth(proj, window=11):
    """Moving-average sederhana untuk memperhalus proyeksi."""
    half   = window // 2
    result = []
    for i in range(len(proj)):
        s = max(0, i - half)
        e = min(len(proj), i + half + 1)
        result.append(sum(proj[s:e]) / (e - s))
    return result


def proyeksi_horizontal(biner, tinggi):
    return [sum(biner[y]) for y in range(tinggi)]


def deteksi_cuts(biner, lebar, tinggi):
    """
    Deteksi garis pemotong antar baris aksara menggunakan
    proyeksi horizontal + peak detection.
    Kembalikan list titik potong (y) dan smoothed projection.
    """
    proyeksi = proyeksi_horizontal(biner, tinggi)
    smoothed = smooth(proyeksi)

    peaks = []
    for y in range(10, tinggi - 10):
        if smoothed[y] < 20:
            continue
        if all(smoothed[j] <= smoothed[y] for j in range(y - 10, y + 11) if j != y):
            peaks.append(y)

    filtered = []
    prev = -999
    for y in peaks:
        if y - prev > 30:
            filtered.append(y)
            prev = y
        elif smoothed[y] > smoothed[filtered[-1]]:
            filtered[-1] = y

    cuts = [0]
    for i in range(len(filtered) - 1):
        cuts.append((filtered[i] + filtered[i + 1]) // 2)
    cuts.append(tinggi)

    return cuts, smoothed


def potong_baris(biner, lebar, tinggi, cuts):
    """
    Potong biner menjadi segmen baris berdasarkan cuts.
    Kembalikan list dict: {index, atas, bawah, biner_crop, lebar, tinggi}
    """
    baris_list = []
    for i in range(len(cuts) - 1):
        s = cuts[i]
        e = cuts[i + 1]
        tinggi_baris = e - s

        pad   = max(5, int(tinggi_baris * 0.25))
        atas  = max(0, s - pad)
        bawah = min(tinggi, e + pad)

        crop = [biner[y][:] for y in range(atas, bawah)]
        baris_list.append({
            "index":       i,
            "atas":        atas,
            "bawah":       bawah,
            "biner_crop":  crop,
            "lebar":       lebar,
            "tinggi":      bawah - atas,
        })

    return baris_list


# ─────────────────────────────────────────────
# Fungsi utama : jalankan seluruh pipeline
# ─────────────────────────────────────────────

def jalankan_pipeline(path_gambar: str, threshold: int = 170, progress_cb=None):
    """
    Jalankan pipeline lengkap dari path PNG.
    progress_cb(persen: int) dipanggil setiap tahap.

    Kembalikan dict:
    {
        gray, biner_bersih, lebar, tinggi,
        cuts, smoothed, baris_list, pixel_rgb
    }
    """
    def lapor(n):
        if progress_cb:
            progress_cb(n)

    lapor(5)
    pixel, lebar, tinggi = baca_png(path_gambar)

    lapor(20)
    gray = ke_grayscale(pixel, lebar, tinggi)

    lapor(35)
    biner = ke_biner(gray, lebar, tinggi, threshold)

    lapor(50)
    biner_bersih = hapus_noise_tepi(biner, lebar, tinggi)

    lapor(65)
    cuts, smoothed = deteksi_cuts(biner_bersih, lebar, tinggi)

    lapor(80)
    baris_list = potong_baris(biner_bersih, lebar, tinggi, cuts)

    lapor(100)
    return {
        "pixel_rgb":    pixel,
        "gray":         gray,
        "biner_bersih": biner_bersih,
        "lebar":        lebar,
        "tinggi":       tinggi,
        "cuts":         cuts,
        "smoothed":     smoothed,
        "baris_list":   baris_list,
    }
