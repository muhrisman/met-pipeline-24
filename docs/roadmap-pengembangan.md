# Roadmap Pengembangan MET-Pipeline

## Ruang Lingkup

Pipeline ini bertanggung jawab untuk **evaluasi kualitas data SIPSN** — mulai dari penarikan data, validasi, hingga menghasilkan skor kualitas. Output pipeline ini akan digunakan oleh tim lain untuk pemodelan emisi metana, ekonomi sirkuler, dan peta emisi.

**Cakupan pipeline ini:**
- Penarikan data dari API SIPSN dan file Excel
- Validasi dan evaluasi kualitas data (kelengkapan, cakupan, report rate, outlier)
- Analisis lanjutan (clustering, PCA, regresi spasial)
- Menghasilkan skor kualitas tertimbang per dataset

**Di luar cakupan:** Kalkulator emisi, peta emisi metana, pemodelan ekonomi sirkuler (ditangani tim lain).

---

## Kondisi Saat Ini

Pipeline ini memiliki **3 modul kualitas** (`completeness`, `coverage`, `entity_completeness`) dan **4 modul I/O** (`excel_loader`, `csv_loader`, `reference_loader`, `normalization`). Total 251 baris kode di `src/`.

Namun, berdasarkan dokumentasi analisis (`analysis-scope.md`, `data-quality-metrics.md`), banyak fitur yang sudah direncanakan tapi **belum diimplementasi** sebagai modul yang reusable.

---

## Modul yang Perlu Dikembangkan

### Tahap 1: Keamanan & Infrastruktur Dasar

| Item | File | Keterangan |
|------|------|------------|
| Tambahkan `.env` ke `.gitignore` | `.gitignore` | Kredensial API saat ini terekspos di git |
| Lengkapi `pyproject.toml` | `pyproject.toml` | Tambahkan dependencies: pandas, scikit-learn, scipy, requests, python-dotenv, openpyxl |
| Buat folder `tests/` | `tests/` | Unit test untuk semua modul yang ada |
| Satukan logika normalisasi | `src/met_pipeline/io/normalization.py` | Ada 2 implementasi berbeda di `normalization.py` dan `reference_loader.py` yang menghasilkan output berbeda |

### Tahap 2: Modul Kualitas Data (Tambahan)

| Modul | File | Keterangan |
|-------|------|------------|
| Deteksi Outlier | `src/met_pipeline/quality/outlier.py` | Pindahkan logika Isolation Forest dari notebook ke modul reusable |
| Report Rate | `src/met_pipeline/quality/report_rate.py` | Hitung tingkat partisipasi pelaporan per daerah |
| Scoring | `src/met_pipeline/quality/scoring.py` | Gabungkan metrik kualitas menjadi skor tertimbang (lihat formula di bawah) |
| Plausibility Check | `src/met_pipeline/quality/plausibility.py` | Validasi logika data (mis. total komposisi = 100%) |

#### Formula Scoring per Dataset

| Dataset | Formula |
|---------|---------|
| Timbulan | `skor = (report_rate / completeness) * 0.6 + outlier * 0.4` |
| Sumber | `skor = report_rate * 0.3 + completeness * 0.4 + outlier * 0.3` |
| Komposisi | `skor = report_rate * 0.4 + completeness * 0.3 + outlier * 0.3` |

Formula ini harus diimplementasikan di `quality/scoring.py` dengan bobot yang dapat dikonfigurasi.

### Tahap 3: Modul Analisis

| Modul | File | Keterangan |
|-------|------|------------|
| Clustering | `src/met_pipeline/analysis/clustering.py` | K-Means clustering (saat ini hanya di notebook) |
| PCA | `src/met_pipeline/analysis/pca.py` | Principal Component Analysis untuk interpretasi |
| Korelasi | `src/met_pipeline/analysis/correlation.py` | Analisis korelasi antar variabel |
| Time Series | `src/met_pipeline/analysis/timeseries.py` | Analisis tren dan pola tahunan |
| Statistik Deskriptif | `src/met_pipeline/analysis/descriptive.py` | Ringkasan statistik otomatis |

### Tahap 4: API & Integrasi

| Modul | File | Keterangan |
|-------|------|------------|
| API Client | `src/met_pipeline/api/client.py` | Klien API SIPSN yang reusable (saat ini tersebar di notebook) |
| Schema Validasi | `src/met_pipeline/api/schemas.py` | Validasi format response API |

### Tahap 5: Analisis Spasial & Orkestrasi

| Modul | File | Keterangan |
|-------|------|------------|
| Regresi Spasial | `src/met_pipeline/spatial/regression.py` | OLS & GWR (sesuai analysis-scope.md) |
| Pipeline Runner | `src/met_pipeline/pipeline/orchestrator.py` | Script utama untuk menjalankan seluruh pipeline secara berurutan |
| CI/CD | `.github/workflows/` | Automated testing & linting |

---

## Struktur Target

```
src/met_pipeline/
├── quality/
│   ├── completeness.py        [ada]
│   ├── coverage.py            [ada]
│   ├── entity_completeness.py [ada]
│   ├── outlier.py             [perlu dibuat]
│   ├── report_rate.py         [perlu dibuat]
│   ├── scoring.py             [perlu dibuat]
│   └── plausibility.py        [perlu dibuat]
├── io/
│   ├── excel_loader.py        [ada]
│   ├── csv_loader.py          [ada]
│   ├── reference_loader.py    [ada]
│   └── normalization.py       [ada, perlu diperbaiki]
├── analysis/                   [perlu dibuat]
│   ├── clustering.py
│   ├── pca.py
│   ├── correlation.py
│   ├── timeseries.py
│   └── descriptive.py
├── spatial/                    [perlu dibuat]
│   └── regression.py
├── api/                        [perlu dibuat]
│   ├── client.py
│   └── schemas.py
└── pipeline/                   [perlu dibuat]
    └── orchestrator.py
```

---

## Dependensi Data

Berikut hubungan antara **data yang dibutuhkan** dan **modul yang membutuhkannya**:

| Data | Modul yang Membutuhkan |
|------|----------------------|
| Timbulan Sampah | completeness, coverage, outlier, report_rate, scoring, timeseries |
| Komposisi Sampah | completeness, coverage, clustering, pca, plausibility |
| Sumber Sampah | completeness, coverage, clustering, correlation |
| Capaian Pengelolaan | completeness, coverage, scoring |
| Data Fasilitas (TPA/TPS3R/Bank Sampah/Komposting/Sumber Energi/Sektor Informal) | outlier, descriptive, spatial regression |
| Data Populasi | normalisasi per kapita, spatial regression |
| Referensi Kabupaten/Kota | coverage, entity_completeness, report_rate |

---

## Catatan

- Modul yang bertanda **[ada]** sudah diimplementasi di `src/met_pipeline/`
- Logika untuk **outlier detection** (Isolation Forest) dan **clustering** (K-Means) sudah ada di notebook, perlu dipindahkan ke `src/` sebagai modul reusable
- Lihat `docs/permintaan-data-api.md` untuk detail data yang perlu diminta ke penyedia API
