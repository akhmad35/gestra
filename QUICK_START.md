# 🚀 QUICK START GUIDE - GESTRA

Panduan cepat untuk memulai aplikasi GESTRA dengan fitur autentikasi dan manajemen kelas.

---

## ⚡ 5 Menit Setup

### 1️⃣ Buka Terminal
```bash
cd "d:\semester 6\Visual Komputer Cerdas\projek\web_gestra_v2"
```

### 2️⃣ Jalankan Server
```bash
py -m uvicorn app.main:app --reload
```

**Output yang diharapkan:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 3️⃣ Buka Browser
Kunjungi: **http://localhost:8000**

✅ **Aplikasi siap digunakan!**

---

## 🎯 First Time Setup (Hanya di awal)

### Jalankan ini SEKALI untuk membuat data testing:
```bash
py -m app.seed_data
```

**Data yang dibuat:**
- 1 Guru: Ibu Siti
- 4 Kelas dengan kode unik

---

## 👤 Test Credentials

### Option 1: Login sebagai Guru
```
Email: guru@gestra.com
Password: password123
```

### Option 2: Register Akun Baru
1. Klik "Daftar Sekarang"
2. Isi form dengan data apapun
3. Password: minimal 6 karakter
4. Pilih role "Siswa"

---

## 📖 Alur Penggunaan

### Untuk Pertama Kali:
```
1. Buka http://localhost:8000
   ↓
2. Klik "Daftar Sekarang"
   ↓
3. Isi form register
   ↓
4. Pilih role "Siswa"
   ↓
5. Otomatis login ke beranda
   ↓
6. Klik "Kelas" di navbar
   ↓
7. Lihat daftar kelas & bergabung
```

### Untuk Login Ulang:
```
1. Buka http://localhost:8000/login
   ↓
2. Masukkan email & password
   ↓
3. Klik "Masuk"
   ↓
4. Akses semua fitur
```

---

## 🔧 Menu Fitur

| Fitur | URL | Deskripsi |
|-------|-----|----------|
| Login | `/login` | Masuk akun |
| Register | `/register` | Buat akun baru |
| Beranda | `/beranda` | Home page |
| **Daftar Kelas** | `/kelas/daftar` | ⭐ Lihat & bergabung kelas |
| **Detail Kelas** | `/kelas/{id}/detail` | ⭐ Info lengkap kelas |
| Profil | `/profil` | Profil user |

**⭐ = Fitur Baru**

---

## 💡 Tips & Trik

### Bergabung ke Kelas - 2 Cara

**Cara 1: Melalui Tombol**
1. Buka `/kelas/daftar`
2. Klik "Lihat Detail" pada kelas pilihan
3. Klik "Bergabung ke Kelas"

**Cara 2: Melalui Kode Kelas**
1. Buka `/kelas/daftar`
2. Masukkan kode kelas (contoh: `BID001`)
3. Klik "Bergabung"
4. Otomatis ke halaman detail kelas

### Kode Kelas yang Tersedia:
```
BID001 - Bahasa Indonesia Dasar
MNK001 - Membaca dan Menulis Kreatif
LDG001 - Literasi Digital
PTL001 - Pemahaman Teks Lanjutan
```

### Reset Database
```bash
# Hapus database
del gestra.db

# Buat ulang dengan data baru
py -m app.seed_data
```

---

## 🛑 Troubleshooting

### Server tidak jalan?
```bash
# Cek apakah port 8000 sudah digunakan
py -m uvicorn app.main:app --port 8001
```

### Module not found error?
```bash
# Install dependencies
pip install -r requirements.txt
```

### Database error?
```bash
# Reset database
del gestra.db
py -m app.seed_data
```

### Lupa password?
```
Fitur reset password belum tersedia.
Untuk testing, buat akun baru atau gunakan email yang sudah terdaftar.
```

---

## 📁 File Penting

| File | Fungsi |
|------|--------|
| `app/main.py` | Entry point aplikasi |
| `app/routes/kelas.py` | API routes untuk kelas |
| `app/services/kelas.py` | Business logic kelas |
| `app/templates/daftar-kelas.html` | Halaman daftar kelas |
| `app/templates/detail-kelas.html` | Halaman detail kelas |
| `app/static/css/kelas.css` | Styling kelas |
| `FITUR_KELAS.md` | Dokumentasi lengkap |
| `TESTING_RESULTS.md` | Hasil testing |

---

## 🎓 Learning Resources

### Untuk Memahami Kode:

1. **Struktur Database** → Buka `app/models/kelas.py`
2. **API Endpoints** → Buka `app/routes/kelas.py`
3. **Business Logic** → Buka `app/services/kelas.py`
4. **Frontend** → Buka folder `app/templates/`

### Dokumentasi Lengkap:
- 📖 `FITUR_KELAS.md` - Penjelasan fitur
- 📊 `TESTING_RESULTS.md` - Hasil testing
- 🔧 `IMPLEMENTATION_GUIDE.md` - Panduan implementasi

---

## ✅ Checklist - Verifikasi Semua Berfungsi

- [ ] Server berjalan tanpa error
- [ ] Bisa akses login page (`http://localhost:8000`)
- [ ] Bisa register akun baru
- [ ] Bisa login dengan akun yang dibuat
- [ ] Bisa melihat daftar kelas di `/kelas/daftar`
- [ ] Bisa melihat detail kelas
- [ ] Bisa bergabung ke kelas (tombol)
- [ ] Bisa bergabung ke kelas (kode)
- [ ] Status bergabung terupdate dengan benar
- [ ] Bisa logout
- [ ] Data persisten setelah logout & login ulang

Jika semua ✅ = **SIAP DIGUNAKAN!** 🎉

---

## 🚀 Next Steps

Setelah familiar dengan aplikasi:

1. **Explore Kode** - Pahami arsitektur & flow
2. **Baca Dokumentasi** - Lihat `FITUR_KELAS.md` & `IMPLEMENTATION_GUIDE.md`
3. **Develop Features** - Tambahkan fitur baru (materi, tugas, dll)
4. **Run Tests** - Verify semua berfungsi dengan baik
5. **Deploy** - Siapkan untuk production

---

## 📞 Pertanyaan?

- Check dokumentasi di folder ini
- Review code di `app/` directory
- Lihat testing results di `TESTING_RESULTS.md`

---

**Happy Coding! 🎉**

*Dibuat dengan ❤️ untuk GESTRA Platform*
