# Permintaan Data API SIPSN

## Latar Belakang

Tim kami sedang mengembangkan pipeline analisis kualitas data untuk data pengelolaan sampah nasional (SIPSN). Pipeline ini membutuhkan akses ke beberapa dataset melalui API SIPSN untuk menjalankan evaluasi kualitas data secara otomatis, termasuk analisis kelengkapan, cakupan, deteksi outlier, clustering, dan analisis spasial.

Saat ini, API key yang kami miliki hanya dapat mengakses **3 dari 4 endpoint** yang tersedia:

| Endpoint | Status Akses |
|----------|-------------|
| `provinsi` | Dapat diakses |
| `kabkota` | Dapat diakses |
| `tbl_fasilitas` | Dapat diakses |
| `fasilitas` (detail) | **Tidak dapat diakses** (401: permissions) |

Selain itu, terdapat beberapa dataset penting yang **belum tersedia** di API namun sangat dibutuhkan untuk analisis kami.

---

## 1. Permintaan Akses Endpoint yang Ada

### 1.1 Akses Endpoint `fasilitas` (Detail)

Kami membutuhkan akses ke endpoint detail fasilitas:

```
/v2/fasilitas/key/{KEY}/idp/{idp}/idd/{idd}/j/{jenis}/tahun/{tahun}/periode/{periode}
```

Saat ini endpoint ini mengembalikan error:
```json
{"status": false, "error": "This API key does not have enough permissions"}
```

**Kebutuhan:** Upgrade permission API key kami agar dapat mengakses data detail fasilitas (lokasi, kapasitas, status operasional).

---

## 2. Permintaan Endpoint/Data Baru

### 2.1 Capaian Pengelolaan Sampah — PRIORITAS TINGGI

**Mengapa dibutuhkan:**
- Evaluasi kinerja pengelolaan sampah per daerah
- Input untuk analisis cakupan dan completeness
- Cross-validation dengan data timbulan dan fasilitas

**Data yang dibutuhkan (level kabupaten/kota):**

| Kolom | Tipe Data | Keterangan |
|-------|-----------|------------|
| `tahun` | Integer | Tahun pelaporan |
| `periode` | Integer | Periode pelaporan |
| `id_propinsi` | String | ID provinsi |
| `nama_propinsi` | String | Nama provinsi |
| `id_kabkota` | String | ID kabupaten/kota |
| `nama_kabkota` | String | Nama kabupaten/kota |
| `pengurangan` | Numeric (ton/%) | Capaian pengurangan sampah |
| `penanganan` | Numeric (ton/%) | Capaian penanganan sampah |

**Cakupan tahun:** 2019 - 2024

---

### 2.2 Timbulan Sampah (Waste Generation) — PRIORITAS TINGGI

**Mengapa dibutuhkan:**
- Data utama untuk analisis kelengkapan dan cakupan
- Digunakan untuk deteksi outlier dan analisis tren tahunan
- Saat ini hanya tersedia dalam format Excel (offline)

**Data yang dibutuhkan (level kabupaten/kota):**

| Kolom | Tipe Data | Keterangan |
|-------|-----------|------------|
| `tahun` | Integer | Tahun pelaporan |
| `periode` | Integer | Periode pelaporan |
| `id_propinsi` | String | ID provinsi |
| `nama_propinsi` | String | Nama provinsi |
| `id_kabkota` | String | ID kabupaten/kota |
| `nama_kabkota` | String | Nama kabupaten/kota |
| `timbulan_harian` | Numeric (ton) | Timbulan sampah harian |
| `timbulan_tahunan` | Numeric (ton) | Timbulan sampah tahunan |

**Catatan:** Data yang dibutuhkan adalah data **agregat di level kabupaten/kota**, bukan level fasilitas.

**Cakupan tahun:** 2019 - 2024 (atau selengkap mungkin)

---

### 2.3 Komposisi Sampah (Waste Composition) — PRIORITAS TINGGI

**Mengapa dibutuhkan:**
- Digunakan untuk analisis clustering dan PCA (Principal Component Analysis)
- Evaluasi kelengkapan pelaporan per kategori komposisi
- Cross-validation dengan data sumber sampah

**Data yang dibutuhkan (level kabupaten/kota):**

| Kolom | Tipe Data | Keterangan |
|-------|-----------|------------|
| `tahun` | Integer | Tahun pelaporan |
| `periode` | Integer | Periode pelaporan |
| `id_propinsi` | String | ID provinsi |
| `nama_propinsi` | String | Nama provinsi |
| `id_kabkota` | String | ID kabupaten/kota |
| `nama_kabkota` | String | Nama kabupaten/kota |
| `sisa_makanan` | Numeric (ton/%) | Sisa makanan |
| `kayu_ranting` | Numeric (ton/%) | Kayu dan ranting |
| `kertas_karton` | Numeric (ton/%) | Kertas dan karton |
| `plastik` | Numeric (ton/%) | Plastik |
| `logam` | Numeric (ton/%) | Logam/metal |
| `kain` | Numeric (ton/%) | Kain/tekstil |
| `karet_kulit` | Numeric (ton/%) | Karet dan kulit |
| `kaca` | Numeric (ton/%) | Kaca |
| `lainnya` | Numeric (ton/%) | Lainnya |

**Cakupan tahun:** 2019 - 2024

---

### 2.4 Sumber Sampah (Waste Sources) — PRIORITAS TINGGI

**Mengapa dibutuhkan:**
- Analisis pola sumber sampah per daerah
- Cross-validation antara data timbulan dan sumber
- Input untuk clustering dan analisis korelasi

**Data yang dibutuhkan (level kabupaten/kota):**

| Kolom | Tipe Data | Keterangan |
|-------|-----------|------------|
| `tahun` | Integer | Tahun pelaporan |
| `periode` | Integer | Periode pelaporan |
| `id_propinsi` | String | ID provinsi |
| `nama_propinsi` | String | Nama provinsi |
| `id_kabkota` | String | ID kabupaten/kota |
| `nama_kabkota` | String | Nama kabupaten/kota |
| `rumah_tangga` | Numeric (ton/%) | Dari rumah tangga |
| `perkantoran` | Numeric (ton/%) | Dari perkantoran |
| `perniagaan` | Numeric (ton/%) | Dari perniagaan/komersial |
| `pasar` | Numeric (ton/%) | Dari pasar |
| `fasilitas_publik` | Numeric (ton/%) | Dari fasilitas publik |
| `lainnya` | Numeric (ton/%) | Dari sumber lainnya |

**Cakupan tahun:** 2019 - 2024

---

### 2.5 Anggaran Pengelolaan Sampah — PRIORITAS SEDANG

**Mengapa dibutuhkan:**
- Analisis efektivitas pengelolaan sampah berdasarkan anggaran daerah
- Input untuk clustering lanjutan (decision tree) bersama variabel ekonomi
- Prioritisasi kabupaten/kota untuk survey atau sampling

**Data yang dibutuhkan (level kabupaten/kota):**

| Kolom | Tipe Data | Keterangan |
|-------|-----------|------------|
| `tahun` | Integer | Tahun pelaporan |
| `periode` | Integer | Periode pelaporan |
| `id_propinsi` | String | ID provinsi |
| `nama_propinsi` | String | Nama provinsi |
| `id_kabkota` | String | ID kabupaten/kota |
| `nama_kabkota` | String | Nama kabupaten/kota |
| `anggaran` | Numeric (Rp) | Anggaran pengelolaan sampah |

**Cakupan tahun:** 2019 - 2024

---

### 2.6 Status Validasi Data — PRIORITAS SEDANG

**Mengapa dibutuhkan:**
- Membedakan data yang sudah divalidasi dan belum divalidasi
- Data yang belum divalidasi dapat dievaluasi oleh pipeline kami sebagai fitur tambahan
- Meningkatkan akurasi quality scoring

**Kebutuhan:** Informasi apakah API menyediakan field atau parameter untuk status validasi data per kabupaten/kota. Jika tersedia, mohon informasi cara mengaksesnya.

---

## 3. Ringkasan Permintaan

| No | Data | Prioritas | Status Saat Ini |
|----|------|-----------|-----------------|
| 1 | Akses endpoint `fasilitas` detail | Tinggi | API key tidak memiliki permission |
| 2 | Capaian Pengelolaan Sampah | Tinggi | Tidak ada endpoint di API |
| 3 | Timbulan Sampah (agregat kabupaten/kota) | Tinggi | Tidak ada endpoint di API |
| 4 | Komposisi Sampah | Tinggi | Tidak ada endpoint di API |
| 5 | Sumber Sampah | Tinggi | Tidak ada endpoint di API |
| 6 | Anggaran Pengelolaan Sampah | Sedang | Tidak ada endpoint di API |
| 7 | Status Validasi Data | Sedang | Perlu konfirmasi ketersediaan |

---

## 4. Catatan Teknis

- **Format response:** JSON (konsisten dengan endpoint yang sudah ada)
- **Konsistensi penamaan:** Mohon menggunakan `id_propinsi` dan `id_kabkota` yang konsisten dengan endpoint `provinsi` dan `kabkota` yang sudah ada, agar memudahkan join data
- **Pagination:** Untuk dataset besar, mohon disediakan pagination seperti pada `tbl_fasilitas` (`pg`, `lmt`, `total`)
- **Cakupan historis:** Data historis (2019-2024) sangat penting untuk analisis tren dan time series

---

## Kontak

Jika ada pertanyaan terkait permintaan ini, silakan hubungi tim kami.
