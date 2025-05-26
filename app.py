from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Ranking dan tipe kriteria (updated dengan field baru)
kriteria_ranks = {
    "IPK": 1,
    "Penghasilan": 2,
    "Tanggungan": 3,
    "Prestasi": 4,
    "Semester": 5,
    "Organisasi": 6
}

kriteria_types = {
    "IPK": "benefit",
    "Penghasilan": "cost",
    "Tanggungan": "cost",
    "Prestasi": "benefit",
    "Semester": "benefit",  # Semester 4 adalah yang terbaik
    "Organisasi": "benefit"  # Aktif organisasi lebih baik
}

CSV_FILE = "hasil.csv"

# Fungsi ROC
def hitung_bobot_ROC(ranks):
    sorted_criteria = sorted(ranks.items(), key=lambda x: x[1])
    n = len(ranks)
    roc_weights = {}
    for i, (kriteria, _) in enumerate(sorted_criteria):
        weight = sum([1 / (j + 1) for j in range(i, n)]) / n
        roc_weights[kriteria] = round(weight, 4)
    return roc_weights

# Fungsi khusus untuk menghitung nilai semester
def hitung_nilai_semester(semester):
    """
    Semester 4 = nilai tertinggi (1.0)
    Semakin jauh dari semester 4, semakin rendah nilainya
    """
    if semester == 4:
        return 1.0
    else:
        # Hitung jarak dari semester 4, lalu buat nilai inverse
        jarak = abs(semester - 4)
        # Nilai maksimal jarak adalah 4 (dari semester 8 ke 4 atau dari semester 1 ke 4)
        # Gunakan formula: 1 - (jarak / 4) * 0.6 agar tidak sampai 0
        nilai = 1.0 - (jarak / 4.0) * 0.6
        return max(nilai, 0.4)  # Minimal 0.4

# Fungsi Normalisasi SAW (updated untuk handle semester dan organisasi)
def normalisasi_saw(df, kriteria_types):
    norm_df = df.copy()
    
    for col, tipe in kriteria_types.items():
        if col == "Semester":
            # Normalisasi khusus untuk semester
            norm_df[col] = df[col].apply(hitung_nilai_semester)
        elif col == "Organisasi":
            # Normalisasi untuk organisasi: Ya=1, Tidak=0.5
            norm_df[col] = df[col].apply(lambda x: 1.0 if x == "Ya" else 0.5)
        elif tipe == "benefit":
            norm_df[col] = df[col] / df[col].max()
        elif tipe == "cost":
            norm_df[col] = df[col].min() / df[col]
    
    return norm_df

# Hitung skor SAW
def hitung_skor(df, bobot):
    return df[list(bobot.keys())].dot(pd.Series(bobot))

@app.route("/", methods=["GET", "POST"])
def index():
    hasil = []
    hasil_perhitungan = []
    show_popup = False
    edit_data = None

    # Jika ada file CSV, tampilkan data sebelumnya (tanpa skor untuk tabel utama)
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE)
        
        # Tambahkan kolom baru jika belum ada (untuk kompatibilitas data lama)
        if 'Semester' not in df_existing.columns:
            df_existing['Semester'] = 4  # Default semester 4 (nilai optimal)
        if 'Organisasi' not in df_existing.columns:
            df_existing['Organisasi'] = 'Tidak'  # Default tidak aktif organisasi
            
        # Simpan kembali dengan kolom baru
        df_existing.to_csv(CSV_FILE, index=False)
        
        # Hapus kolom Skor untuk tampilan tabel utama
        if 'Skor' in df_existing.columns:
            df_display = df_existing.drop('Skor', axis=1)
        else:
            df_display = df_existing
        
        # Tambahkan index untuk keperluan edit/delete
        df_display_with_index = df_display.reset_index()
        hasil = df_display_with_index.to_dict(orient="records")

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "simpan":
            # Ambil data dari form (updated dengan field baru)
            nama = request.form.getlist("nama")
            ipk = list(map(float, request.form.getlist("ipk")))
            penghasilan = list(map(int, request.form.getlist("penghasilan")))
            tanggungan = list(map(int, request.form.getlist("tanggungan")))
            prestasi = list(map(int, request.form.getlist("prestasi")))
            semester = list(map(int, request.form.getlist("semester")))
            organisasi = request.form.getlist("organisasi")

            # Filter data yang tidak kosong
            data_baru = []
            for i in range(len(nama)):
                if nama[i].strip():  # Hanya ambil data dengan nama yang tidak kosong
                    data_baru.append({
                        "Nama": nama[i],
                        "IPK": ipk[i],
                        "Penghasilan": penghasilan[i],
                        "Tanggungan": tanggungan[i],
                        "Prestasi": prestasi[i],
                        "Semester": semester[i],
                        "Organisasi": organisasi[i]
                    })

            if data_baru:
                # Simpan data baru ke CSV (tanpa skor)
                df_baru = pd.DataFrame(data_baru)
                
                if os.path.exists(CSV_FILE):
                    # Cek duplikasi berdasarkan nama
                    df_existing = pd.read_csv(CSV_FILE)
                    
                    # Tambahkan kolom baru jika belum ada (untuk kompatibilitas data lama)
                    if 'Semester' not in df_existing.columns:
                        df_existing['Semester'] = 4  # Default semester 4
                    if 'Organisasi' not in df_existing.columns:
                        df_existing['Organisasi'] = 'Tidak'  # Default tidak aktif
                        
                    # Hapus kolom Skor untuk perbandingan
                    if 'Skor' in df_existing.columns:
                        df_existing = df_existing.drop('Skor', axis=1)
                    
                    nama_existing = df_existing['Nama'].tolist()
                    
                    # Filter data yang belum ada
                    data_unik = [row for row in data_baru if row['Nama'] not in nama_existing]
                    
                    if data_unik:
                        df_unik = pd.DataFrame(data_unik)
                        df_unik.to_csv(CSV_FILE, mode='a', header=False, index=False)
                    else:
                        # Update file dengan kolom baru jika diperlukan
                        df_existing.to_csv(CSV_FILE, index=False)
                else:
                    df_baru.to_csv(CSV_FILE, index=False)
                
                # Redirect untuk mencegah duplikasi saat refresh
                return redirect(url_for('index'))
                
        elif action == "proses":
            # Proses HANYA data yang sudah tersimpan di CSV
            if os.path.exists(CSV_FILE):
                df_existing = pd.read_csv(CSV_FILE)
                
                # Tambahkan kolom baru jika belum ada (untuk kompatibilitas data lama)
                if 'Semester' not in df_existing.columns:
                    df_existing['Semester'] = 4  # Default semester 4
                if 'Organisasi' not in df_existing.columns:
                    df_existing['Organisasi'] = 'Tidak'  # Default tidak aktif
                
                # Hapus kolom Skor jika ada untuk perhitungan ulang
                if 'Skor' in df_existing.columns:
                    df_existing = df_existing.drop('Skor', axis=1)
                
                # Cek apakah ada data untuk diproses
                if len(df_existing) > 0:
                    # Pastikan semua kolom kriteria ada
                    required_columns = list(kriteria_types.keys())
                    missing_columns = [col for col in required_columns if col not in df_existing.columns]
                    
                    if missing_columns:
                        # Tambahkan kolom yang hilang dengan nilai default
                        for col in missing_columns:
                            if col == 'Semester':
                                df_existing[col] = 4
                            elif col == 'Organisasi':
                                df_existing[col] = 'Tidak'
                    
                    # Hitung bobot ROC
                    bobot = hitung_bobot_ROC(kriteria_ranks)
                    
                    # Normalisasi SAW
                    norm_df = normalisasi_saw(df_existing[kriteria_types.keys()], kriteria_types)
                    
                    # Hitung skor
                    df_existing["Skor"] = hitung_skor(norm_df, bobot)
                    
                    # Urutkan berdasarkan skor tertinggi
                    df_existing = df_existing.sort_values('Skor', ascending=False)
                    
                    # Simpan hasil untuk pop-up (TIDAK menyimpan ke CSV)
                    hasil_perhitungan = df_existing.to_dict(orient="records")
                    show_popup = True
                    
                    # Tetap tampilkan data utama tanpa skor dengan index
                    df_display = df_existing.drop('Skor', axis=1)
                    df_display_with_index = df_display.reset_index(drop=True)
                    hasil = df_display_with_index.to_dict(orient="records")
                    
        elif action == "delete":
            # Hapus data berdasarkan index yang dipilih
            selected_indices = request.form.getlist("selected_rows")
            if selected_indices and os.path.exists(CSV_FILE):
                df_existing = pd.read_csv(CSV_FILE)
                
                # Hapus kolom Skor jika ada
                if 'Skor' in df_existing.columns:
                    df_existing = df_existing.drop('Skor', axis=1)
                
                # Convert indices to int dan urutkan dari besar ke kecil untuk menghindari index shift
                indices_to_delete = sorted([int(idx) for idx in selected_indices], reverse=True)
                
                # Hapus baris yang dipilih
                for idx in indices_to_delete:
                    if 0 <= idx < len(df_existing):
                        df_existing = df_existing.drop(df_existing.index[idx]).reset_index(drop=True)
                
                # Simpan kembali ke CSV
                if len(df_existing) > 0:
                    df_existing.to_csv(CSV_FILE, index=False)
                else:
                    # Jika tidak ada data tersisa, hapus file
                    os.remove(CSV_FILE)
                
                return redirect(url_for('index'))
                
        elif action == "get_edit_data":
            # Ambil data untuk edit berdasarkan index
            selected_index = request.form.get("selected_row")
            if selected_index and os.path.exists(CSV_FILE):
                df_existing = pd.read_csv(CSV_FILE)
                
                # Hapus kolom Skor jika ada
                if 'Skor' in df_existing.columns:
                    df_existing = df_existing.drop('Skor', axis=1)
                
                idx = int(selected_index)
                if 0 <= idx < len(df_existing):
                    edit_data = df_existing.iloc[idx].to_dict()
                    edit_data['index'] = idx
                    
                    # Reload data untuk ditampilkan
                    df_display_with_index = df_existing.reset_index()
                    hasil = df_display_with_index.to_dict(orient="records")
                    
        elif action == "update":
            # Update data berdasarkan index
            edit_index = int(request.form.get("edit_index"))
            if os.path.exists(CSV_FILE):
                df_existing = pd.read_csv(CSV_FILE)
                
                # Hapus kolom Skor jika ada
                if 'Skor' in df_existing.columns:
                    df_existing = df_existing.drop('Skor', axis=1)
                
                if 0 <= edit_index < len(df_existing):
                    # Update data
                    df_existing.loc[edit_index, 'Nama'] = request.form.get("edit_nama")
                    df_existing.loc[edit_index, 'IPK'] = float(request.form.get("edit_ipk"))
                    df_existing.loc[edit_index, 'Penghasilan'] = int(request.form.get("edit_penghasilan"))
                    df_existing.loc[edit_index, 'Tanggungan'] = int(request.form.get("edit_tanggungan"))
                    df_existing.loc[edit_index, 'Prestasi'] = int(request.form.get("edit_prestasi"))
                    df_existing.loc[edit_index, 'Semester'] = int(request.form.get("edit_semester"))
                    df_existing.loc[edit_index, 'Organisasi'] = request.form.get("edit_organisasi")
                    
                    # Simpan kembali ke CSV
                    df_existing.to_csv(CSV_FILE, index=False)
                    
                return redirect(url_for('index'))

    return render_template("index.html", 
                         hasil=hasil, 
                         hasil_perhitungan=hasil_perhitungan, 
                         show_popup=show_popup,
                         edit_data=edit_data)

@app.route("/reset")
def reset():
    # Hapus file CSV untuk reset data
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)