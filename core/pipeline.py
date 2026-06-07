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
    with open(path, "rb") as f:
        png_data = f.read()

    pos = 8
    lebar = tinggi = 0
    bit_depth = color_type = 0
    idat_data = b''

    while pos < len(png_data):
        panjang    = struct.unpack(">I", png_data[pos:pos+4])[0]; pos += 4
        tipe_chunk = png_data[pos:pos+4];                         pos += 4
        isi_chunk  = png_data[pos:pos+panjang];                   pos += panjang
        pos += 4  # CRC

        if tipe_chunk == b'IHDR':
            lebar      = struct.unpack(">I", isi_chunk[0:4])[0]
            tinggi     = struct.unpack(">I", isi_chunk[4:8])[0]
            bit_depth  = isi_chunk[8]
            color_type = isi_chunk[9]
        elif tipe_chunk == b'IDAT':
            idat_data += isi_chunk
        elif tipe_chunk == b'IEND':
            break

    # Tentukan jumlah channel: RGB=3, RGBA=4, Grayscale=1, Grayscale+Alpha=2
    if color_type == 2:    ch = 3  # RGB
    elif color_type == 6:  ch = 4  # RGBA
    elif color_type == 0:  ch = 1  # Grayscale
    elif color_type == 4:  ch = 2  # Grayscale + Alpha
    else:                  ch = 3  # fallback

    rawdata    = zlib.decompress(idat_data)
    pixel      = []
    pos_baca   = 0
    baris_atas = [0] * (lebar * ch)

    for y in range(tinggi):
        tipe_filter = rawdata[pos_baca]; pos_baca += 1
        rekon = []

        for x in range(lebar * ch):
            nilai     = rawdata[pos_baca]; pos_baca += 1
            kiri      = rekon[x - ch]      if x >= ch else 0
            atas      = baris_atas[x]
            kiri_atas = baris_atas[x - ch] if x >= ch else 0

            if tipe_filter == 0:
                hasil = nilai
            elif tipe_filter == 1:
                hasil = nilai + kiri
            elif tipe_filter == 2:
                hasil = nilai + atas
            elif tipe_filter == 3:
                hasil = nilai + ((kiri + atas) // 2)
            elif tipe_filter == 4:
                p  = kiri + atas - kiri_atas
                ja = abs(p - kiri)
                jb = abs(p - atas)
                jc = abs(p - kiri_atas)
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

        # Ambil hanya R, G, B — abaikan alpha jika ada
        baris_pixel = []
        for i in range(0, lebar * ch, ch):
            if ch >= 3:
                baris_pixel.append((rekon[i], rekon[i+1], rekon[i+2]))
            else:
                # Grayscale → jadikan RGB
                baris_pixel.append((rekon[i], rekon[i], rekon[i]))
        pixel.append(baris_pixel)

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
    return [[1 if g < threshold else 0 for g in baris] for baris in gray]


# ─────────────────────────────────────────────
# TAHAP 2  (dari 2.py) : Flood-fill hapus noise
# ─────────────────────────────────────────────

def hapus_noise_tepi(biner, lebar, tinggi):
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


def crop_konten(biner, lebar, tinggi, threshold=5):
    """
    Crop gambar ke area konten saja menggunakan proyeksi baris + kolom.
    Ambil blok terbesar saja (dari 2.py baru).
    """
    row_smoothed = smooth([sum(biner[y]) for y in range(tinggi)])
    inside = False
    row_blocks = []

    for y in range(tinggi):
        if row_smoothed[y] > threshold and not inside:
            start_y = y
            inside  = True
        elif row_smoothed[y] <= threshold and inside:
            row_blocks.append((start_y, y - 1))
            inside = False
    if inside:
        row_blocks.append((start_y, tinggi - 1))

    if not row_blocks:
        return biner, lebar, tinggi, 0, 0

    crop_atas, crop_bawah = max(row_blocks, key=lambda b: b[1] - b[0])

    col_smoothed = smooth([
        sum(biner[y][x] for y in range(crop_atas, crop_bawah + 1))
        for x in range(lebar)
    ])
    inside = False
    col_blocks = []

    for x in range(lebar):
        if col_smoothed[x] > threshold and not inside:
            start_x = x
            inside  = True
        elif col_smoothed[x] <= threshold and inside:
            col_blocks.append((start_x, x - 1))
            inside = False
    if inside:
        col_blocks.append((start_x, lebar - 1))

    if not col_blocks:
        return biner, lebar, tinggi, 0, 0

    crop_kiri, crop_kanan = max(col_blocks, key=lambda b: b[1] - b[0])

    crop_w = crop_kanan  - crop_kiri  + 1
    crop_h = crop_bawah  - crop_atas  + 1

    cropped = [biner[y][crop_kiri:crop_kanan + 1]
               for y in range(crop_atas, crop_bawah + 1)]

    return cropped, crop_w, crop_h, crop_kiri, crop_atas
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

    lapor(60)
    # ── BARU: crop ke area konten ──
    biner_bersih, lebar, tinggi, off_x, off_y = crop_konten(
        biner_bersih, lebar, tinggi
    )

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
        "offset":       (off_x, off_y),   # ← posisi crop relatif ke gambar asli
    }