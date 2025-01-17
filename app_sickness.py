from flask import Flask, request, render_template
import pandas as pd
import time
import logging
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Load dataset penyakit dari server
penyakit_data = pd.read_csv('penyakit.csv')  # Pastikan file penyakit.csv ada di direktori yang sama dengan app.py

# Fungsi untuk mencocokkan gejala pasien dengan penyakit
def match_gejala(pasien, penyakit_data):
    # Ambil gejala pasien dari kolom kedua sampai terakhir
    gejala_pasien = pasien[1:].to_dict()  # Mengubah menjadi dictionary untuk mempermudah akses
    
    for _, penyakit in penyakit_data.iterrows():
        # Ambil gejala penyakit dari kolom kedua sampai terakhir
        gejala_penyakit = penyakit[1:].to_dict()  # Mengubah menjadi dictionary
        
        # Periksa apakah semua gejala pasien cocok dengan gejala penyakit
        match = all(gejala_pasien[gejala] == gejala_penyakit.get(gejala, None) for gejala in gejala_pasien)
        
        if match:
            return penyakit['penyakit']
    
    return "Sakit Brutal"  # Ubah "Tidak Terdeteksi" menjadi "Sakit Brutal"

# Fungsi diagnosis secara paralel
def diagnose_parallel(data_pasien, penyakit_data):
    results_list = []
    
    # Gunakan ThreadPoolExecutor untuk paralelisasi
    with ThreadPoolExecutor() as executor:
        # Memetakan fungsi match_gejala untuk setiap pasien menggunakan executor
        results_list = list(executor.map(lambda pasien: match_gejala(pasien[1], penyakit_data), data_pasien.iterrows()))
        
    return results_list

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pasien_file = request.files.get('pasien_file')

        if pasien_file:
            # Baca dataset pasien
            data_pasien = pd.read_csv(pasien_file)

            # Diagnosa penyakit
            start_time = time.time()
            hasil_diagnosis = diagnose_parallel(data_pasien, penyakit_data)
            end_time = time.time()
            elapsed_time_ms = (end_time - start_time) * 1000  # Menghitung waktu dalam milidetik

            # Analisis hasil
            summary = pd.DataFrame({'Penyakit': hasil_diagnosis})
            statistik = summary['Penyakit'].value_counts()

            # Tambahkan "Sakit Brutal" ke statistik jika tidak ada
            if "Sakit Brutal" not in statistik:
                statistik["Sakit Brutal"] = 0

            # Penyakit paling sering terjadi (dari yang terdeteksi), kecuali Sakit Brutal
            statistik_no_brutal = statistik[statistik.index != "Sakit Brutal"]
            most_common = statistik_no_brutal.idxmax() if not statistik_no_brutal.empty else "Sakit Brutal"

            # Total dataset
            total_dataset = len(data_pasien)

            return render_template(
                'result.html',
                statistik=statistik.to_dict(),
                most_common=most_common,
                elapsed_time=f"{elapsed_time_ms:.2f} ms",  # Menampilkan waktu dalam milidetik
                total_dataset=total_dataset  # Menampilkan total dataset
            )
        else:
            return "Silakan upload file data pasien."
    return render_template('index.html')

app.run(debug=True)
