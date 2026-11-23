# asah2026-a26-cs045-baso-aci-pos
Capstone Project Asah 2026 - Sistem Sinkronisasi Pesanan dan Pemantauan Stok Kedai Baso Aci Classic Cileungsi

# Sistem Sinkronisasi Pesanan dan Pemantauan Stok Bahan Utama Dapur-Kasir
**Capstone Project Asah 2026 — Tim Doa Mamah (ID: A26-CS045)**  
**Mitra UMKM:** Kedai Baso Aci Classic Cileungsi (Pemilik: Ibu Intan Pransiska)

---

## 1. Latar Belakang & Permasalahan yang Diselesaikan
Kedai Baso Aci Classic Cileungsi menghadapi dua kendala operasional saat jam sibuk (*rush hour*):
1. **Pencatatan Pesanan Manual:** Komunikasi pesanan antara kasir dan dapur masih menggunakan kertas sehingga rentan terlambat atau hilang.
2. **Kehabisan Stok Mendadak:** Pemantauan stok bahan utama masih manual sehingga stok sering habis tanpa peringatan dini.

**Peran Model AI & Solusi:**
Aplikasi web ini menyinkronkan pesanan kasir–dapur secara *real-time* sekaligus mengurangi stok bahan baku secara otomatis berdasarkan takaran resep dalam satuan terkecil (`pcs`). Model *Machine Learning* bertugas memprediksi estimasi waktu habisnya bahan utama (*Early Warning*) berdasarkan laju penjualan, sementara **Gemini API** menghasilkan saran menu alternatif bagi kasir ketika stok menipis serta ringkasan stok harian.

---

## 2. Anggota Tim (A26-CS045)
| ID Peserta | Nama Lengkap | Learning Path | Peran Utama |
| :--- | :--- | :--- | :--- |
| `fs009b6y1047` | Muh Rafid Radhitya Ananta | Front End & Back End (FS) | UI/UX, Front-End Kasir-Dapur, Integrasi API |
| `fs009b6y1763` | Wahyu Azhim Mughni | Front End & Back End (FS) | Back-End Express, Database, Validasi Schema (Joi) |
| `ds009b6y0289` | Aurelio Abi Nugroho | Data Science (DS) | Generator Data Sintetis, Analisis Bisnis, Kamus Data |
| `ds009b6y0501` | Eka Rezky Setiawarno | Data Science (DS) | Data Wrangling, Validasi Dataset, Dasbor Streamlit |
| `ae009b6y0919` | Ludfi Aditya Harahap | AI Engineers (AE) | Modeling Prediksi Stok, FastAPI Serving, Gemini API |
| `ae009b6y1905` | Maulana Dzaky Putra Irawan | AI Engineers (AE) | Preprocessing, Komparasi Model, Prompt & Fallback Gen AI |

---

## 3. Sumber Data, API, & Library yang Digunakan
* **Data Primer UMKM:** Daftar menu, takaran resep per porsi, dan stok awal bahan baku diperoleh langsung dari Kedai Baso Aci Classic Cileungsi atas izin pemilik UMKM (seluruh satuan dikonversi ke `pcs`).
* **Dataset Latih (Data Sintetis):** Data transaksi historis disusun secara sintetis (*dummy*) menggunakan Python (`Pandas`, `NumPy`) oleh tim Data Science karena kendala privasi data transaksi internal UMKM. Pola transaksi dikalibrasi mengikuti karakteristik jam sibuk (*rush hour*), akhir pekan (*weekend*), dan takaran resep asli kedai. Detail struktur kolom tersedia di `data-science/data/data_dictionary.md`.
* **API & Layanan Eksternal:** Google Gemini API (via Google AI Studio) untuk fitur rekomendasi menu pengganti dan ringkasan harian.
* **Tech Stack Utama:**
  * *Front-End:* Vite, React, Axios, Tailwind CSS
  * *Back-End:* Node.js, Express.js, Joi, PostgreSQL/Supabase
  * *AI & Data:* Python, Scikit-Learn, FastAPI, Streamlit

---

## 4. Evaluasi & Perbandingan Model AI (Early Warning Stok)
*(Catatan: Isi angka metrik di bawah ini setelah proses training di Minggu 2 selesai)*

| Nama Model / Konfigurasi | Metrik 1 (MAE) | Metrik 2 (RMSE) | Waktu Inferensi | Status |
| :--- | :---: | :---: | :---: | :--- |
| Model 1 (misal: Linear / Ridge Regression) | `0.00` | `0.00` | `0 ms` | Kandidat |
| Model 2 (misal: Random Forest / XGBoost Regressor) | `0.00` | `0.00` | `0 ms` | **Model Terpilih** |

**Alasan Pemilihan Model Terbaik:**  
*(Jelaskan alasan pemilihan berdasarkan nilai error terkecil pada data uji, kestabilan prediksi pada lonjakan pesanan jam sibuk, serta kecepatan respons saat di-deploy menggunakan FastAPI).*

---

## 5. Cara Menjalankan Proyek Secara Lokal
1. **Clone repositori:**
   ```bash
   git clone [https://github.com/aditharahap/asah2026-a26-cs045-baso-aci-pos.git](https://github.com/aditharahap/asah2026-a26-cs045-baso-aci-pos.git)
   cd asah2026-a26-cs045-baso-aci-pos


Salin konfigurasi environment:
   cp .env.example .env


Jalankan masing-masing layanan:

Back-End (backend/): npm install && npm run dev

Front-End (frontend/): npm install && npm run dev

AI Service (ai-service/): pip install -r requirements.txt && uvicorn main:app --reload

Dasbor DS (data-science/dashboard/): streamlit run app.py