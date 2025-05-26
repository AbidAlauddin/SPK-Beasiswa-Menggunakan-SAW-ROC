# SAW ROC Flask

Aplikasi Sistem Pendukung Keputusan menggunakan metode **SAW (Simple Additive Weighting)** dengan pendekatan **ROC (Rank Order Centroid)**. Dibangun menggunakan framework **Flask (Python)** dan database SQLite.

## 🔍 Fitur

- CRUD Kriteria dan Alternatif
- Bobot otomatis menggunakan metode ROC
- Perhitungan keputusan menggunakan metode SAW
- Tampilan antarmuka berbasis HTML/CSS dengan Bootstrap
- Tabel hasil keputusan yang tersorting
- Penyimpanan hasil ke dalam database

## 🖼️ Preview Tampilan

### Dashboard
![Dashboard Preview](preview/dashboard.png)

### Form Kriteria
![Form Kriteria](preview/kriteria.png)

### Hasil Perhitungan
![Hasil SAW](preview/hasil.png)

> Letakkan gambar-gambar ini di folder `static/preview/` dan sesuaikan path-nya jika berbeda.

## 🚀 Cara Menjalankan Aplikasi

### 1. Clone repositori

```bash
git clone https://github.com/username/saw-roc-flask.git
cd saw-roc-flask
