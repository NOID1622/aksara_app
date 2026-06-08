import struct
import zlib



# 1.py) 

def baca_png(path: str):
    with open(path, "rb") as f:
        png_data = f.read()

    pos = 8
    lebar = tinggi = 0
    bit_depth = color_type = 0
    idat_data = b''
    plte = []

    while pos < len(png_data):
        panjang    = struct.unpack(">I", png_data[pos:pos+4])[0]; pos += 4
        tipe_chunk = png_data[pos:pos+4];                         pos += 4
        isi_chunk  = png_data[pos:pos+panjang];                   pos += panjang
        pos += 4

        if tipe_chunk == b'IHDR':
            lebar      = struct.unpack(">I", isi_chunk[0:4])[0]
            tinggi     = struct.unpack(">I", isi_chunk[4:8])[0]
            bit_depth  = isi_chunk[8]
            color_type = isi_chunk[9]
        elif tipe_chunk == b'PLTE':
            for i in range(0, len(isi_chunk), 3):
                plte.append((isi_chunk[i], isi_chunk[i+1], isi_chunk[i+2]))
        elif tipe_chunk == b'IDAT':
            idat_data += isi_chunk
        elif tipe_chunk == b'IEND':
            break

    if color_type == 0:   ch = 1
    elif color_type == 2: ch = 3
    elif color_type == 3: ch = 1
    elif color_type == 4: ch = 2
    elif color_type == 6: ch = 4
    else:                 ch = 3

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
                p       = kiri + atas - kiri_atas
                jarak_a = abs(p - kiri)
                jarak_b = abs(p - atas)
                jarak_c = abs(p - kiri_atas)
                if jarak_a <= jarak_b and jarak_a <= jarak_c:
                    predictor = kiri
                elif jarak_b <= jarak_c:
                    predictor = atas
                else:
                    predictor = kiri_atas
                hasil = nilai + predictor
            else:
                raise ValueError(f"Filter PNG tidak dikenal: {tipe_filter}")

            rekon.append(hasil % 256)

        baris_atas = rekon[:]
        baris_pixel = []

        for i in range(0, lebar * ch, ch):
            if color_type == 3:
                baris_pixel.append(plte[rekon[i]])
            elif color_type == 0 or color_type == 4:
                g = rekon[i]
                baris_pixel.append((g, g, g))
            elif color_type == 6:
                baris_pixel.append((rekon[i], rekon[i+1], rekon[i+2]))
            else:
                baris_pixel.append((rekon[i], rekon[i+1], rekon[i+2]))

        pixel.append(baris_pixel)

    return pixel, lebar, tinggi


def ke_grayscale(pixel, lebar, tinggi):
    
    gray = []
    for y in range(tinggi):
        baris = []
        for x in range(lebar):
            r, g, b = pixel[y][x]
            baris.append((r + g + b) // 3)
        gray.append(baris)
    return gray


def ke_biner(gray, lebar, tinggi, threshold=200):
    return [[1 if g < threshold else 0 for g in baris] for baris in gray]


# 2.py


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

    cropped = [biner[y][crop_kiri:crop_kanan + 1]
           for y in range(crop_atas, crop_bawah + 1)]

    crop_h = len(cropped)
    crop_w = len(cropped[0]) if crop_h > 0 else 0

    return cropped, crop_w, crop_h, crop_kiri, crop_atas


def smooth(proj, window=11):
    half   = window // 2
    result = []
    for i in range(len(proj)):
        s = max(0, i - half)
        e = min(len(proj), i + half + 1)
        result.append(sum(proj[s:e]) / (e - s))
    return result


def proyeksi_horizontal(biner, tinggi):
    tinggi_aktual = len(biner)
    return [sum(biner[y]) for y in range(min(tinggi, tinggi_aktual))]


def deteksi_cuts(biner, tinggi, lebar, window=11, jarak_min=30, min_peak=20):
    proyeksi = proyeksi_horizontal(biner, tinggi)
    smoothed = smooth(proyeksi, window=window)

    peaks = []
    for y in range(10, tinggi - 10):
        if smoothed[y] < min_peak:
            continue
        if all(smoothed[j] <= smoothed[y] for j in range(y-10, y+11) if j != y):
            peaks.append(y)

    filtered = []
    prev = -999
    for y in peaks:
        if y - prev > jarak_min:
            filtered.append(y)
            prev = y
        elif smoothed[y] > smoothed[filtered[-1]]:
            filtered[-1] = y

    cuts = [0]
    for i in range(len(filtered) - 1):
        cuts.append((filtered[i] + filtered[i + 1]) // 2)
    cuts.append(tinggi)

    return cuts, smoothed

def cari_komponen(biner, tinggi, lebar):
    label   = [[-1] * lebar for _ in range(tinggi)]
    komponen = []
    id_komp  = 0

    for y in range(tinggi):
        for x in range(lebar):
            if biner[y][x] == 1 and label[y][x] == -1:
                anggota = []
                stack   = [(y, x)]

                while len(stack) > 0:
                    cy, cx = stack.pop()

                    if cx < 0 or cx >= lebar:
                        continue
                    if cy < 0 or cy >= tinggi:
                        continue
                    if label[cy][cx] != -1:
                        continue
                    if biner[cy][cx] == 0:
                        continue

                    label[cy][cx] = id_komp
                    anggota.append((cy, cx))

                    stack.append((cy, cx + 1))
                    stack.append((cy, cx - 1))
                    stack.append((cy + 1, cx))
                    stack.append((cy - 1, cx))

                komponen.append(anggota)
                id_komp += 1

    return komponen

# def potong_baris(biner, lebar, tinggi, cuts):
#     """
#     Potong biner menjadi segmen baris berdasarkan cuts.
#     Kembalikan list dict: {index, atas, bawah, biner_crop, lebar, tinggi}
#     """
#     baris_list = []
#     for i in range(len(cuts) - 1):
#         s = cuts[i]
#         e = cuts[i + 1]
#         tinggi_baris = e - s

#         pad   = max(5, int(tinggi_baris * 0.25))
#         atas  = max(0, s - pad)
#         bawah = min(tinggi, e + pad)

#         crop = [biner[y][:] for y in range(atas, bawah)]
#         baris_list.append({
#             "index":       i,
#             "atas":        atas,
#             "bawah":       bawah,
#             "biner_crop":  crop,
#             "lebar":       lebar,
#             "tinggi":      bawah - atas,
#         })

#     return baris_list

def bersihkan_baris(biner_crop, lebar, tinggi_crop, mulai, selesai, atas):
    komponen = cari_komponen(biner_crop, tinggi_crop, lebar)

    biner_bersih      = [[0] * lebar for _ in range(tinggi_crop)]
    zona_atas         = mulai - atas
    tengah            = tinggi_crop // 2
    batas_dekat_atas  = zona_atas // 2
    batas_dekat_bawah = tinggi_crop - 1 - batas_dekat_atas

    for komp in komponen:
        y_min  = min(cy for cy, cx in komp)
        y_maks = max(cy for cy, cx in komp)

        dekat_tengah         = y_min <= tengah and y_maks >= tengah
        menyentuh_sisi_atas  = y_min == 0
        menyentuh_sisi_bawah = y_maks == tinggi_crop - 1
        dekat_atas           = y_min <= batas_dekat_atas
        dekat_bawah          = y_maks >= batas_dekat_bawah

        buang = False

        if menyentuh_sisi_atas and not dekat_tengah:
            buang = True
        if menyentuh_sisi_bawah and not dekat_tengah:
            buang = True
        if dekat_atas and not dekat_tengah:
            buang = True
        if dekat_bawah and not dekat_tengah:
            buang = True

        if buang:
            continue

        for cy, cx in komp:
            biner_bersih[cy][cx] = 1

    return biner_bersih


def potong_baris(biner, lebar, tinggi, cuts):
    baris_list = []

    for i in range(len(cuts) - 1):
        mulai        = cuts[i]
        selesai      = cuts[i + 1]
        tinggi_baris = selesai - mulai

        pad         = max(10, int(tinggi_baris * 0.25))
        atas        = max(0, mulai - pad)
        bawah       = min(tinggi, selesai + pad)
        tinggi_crop = bawah - atas

        biner_crop = [biner[y][:] for y in range(atas, bawah)]
        biner_crop = bersihkan_baris(biner_crop, lebar, tinggi_crop, mulai, selesai, atas)

        baris_list.append({
            "index":      i,
            "atas":       atas,
            "bawah":      bawah,
            "biner_crop": biner_crop,
            "lebar":      lebar,
            "tinggi":     tinggi_crop,
        })

    return baris_list

def jalankan_pipeline(path_gambar: str, threshold: int = 200, window: int = 11, jarak_min: int = 30, min_peak: int = 20, progress_cb=None):
    def lapor(n):
        if progress_cb:
            progress_cb(n)

    # === 1.py: baca PNG, grayscale, binerisasi ===
    lapor(5)
    pixel, lebar, tinggi = baca_png(path_gambar)

    lapor(15)
    gray = ke_grayscale(pixel, lebar, tinggi)

    lapor(25)
    biner = ke_biner(gray, lebar, tinggi, threshold)

    # === 2.py: hapus noise tepi (flood fill dari tepi), lalu crop ===
    lapor(40)
    biner = hapus_noise_tepi(biner, lebar, tinggi)

    lapor(55)
    hasil_crop = crop_konten(biner, lebar, tinggi)
    biner_crop, lebar_crop, tinggi_crop, off_x, off_y = hasil_crop

    if lebar_crop == 0 or tinggi_crop == 0 or len(biner_crop) == 0:
        raise ValueError(
            f"Gambar kosong setelah threshold={threshold}. "
            f"Coba turunkan nilai threshold."
        )

    # === 3.py: proyeksi, deteksi peak, potong baris ===
    lapor(65)
    cuts, smoothed = deteksi_cuts(biner_crop, tinggi_crop, lebar_crop, window=window, jarak_min=jarak_min, min_peak=min_peak)

    if len(cuts) < 2:
        raise ValueError(
            f"Tidak ada baris terdeteksi. "
            f"Coba turunkan threshold atau periksa gambar."
        )

    lapor(80)
    baris_list = potong_baris(biner_crop, lebar_crop, tinggi_crop, cuts)

    lapor(100)
    return {
        "pixel_rgb":    pixel,
        "gray":         gray,
        "biner_bersih": biner_crop,
        "lebar":        lebar_crop,
        "tinggi":       tinggi_crop,
        "cuts":         cuts,
        "smoothed":     smoothed,
        "baris_list":   baris_list,
        "offset":       (off_x, off_y),
    }