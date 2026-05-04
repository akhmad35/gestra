# PANDUAN FITUR AUTENTIKASI DAN KELAS GESTRA

## 🚀 Fitur yang Baru Ditambahkan

### 1. Autentikasi User (Register & Login)
- **Register**: User baru dapat membuat akun dengan email dan password
- **Login**: User dapat login dengan email dan password yang terdaftar
- **Logout**: User dapat logout dari sistem
- **Pemilihan Role**: Setelah register, user memilih role (saat ini hanya "siswa")

### 2. Manajemen Kelas (Khusus Siswa)
Fitur berikut tersedia untuk siswa yang sudah login:

#### a. Daftar Kelas (`/kelas/daftar`)
- Melihat semua kelas yang tersedia
- Melihat kode kelas
- Bergabung dengan kelas (dengan tombol atau kode kelas)
- Indikator jika sudah bergabung dengan kelas

#### b. Detail Kelas (`/kelas/{kelas_id}/detail`)
- Melihat informasi lengkap kelas
- Nama dan deskripsi kelas
- Nama guru pengampu
- Jumlah siswa yang bergabung
- Tanggal kelas dibuat
- Status bergabung siswa
- Tombol bergabung jika belum bergabung

#### c. Bergabung Kelas
**Cara 1: Melalui Tombol**
- Klik "Bergabung" pada halaman detail kelas

**Cara 2: Melalui Kode Kelas**
- Masukkan kode kelas di form "Bergabung Dengan Kode Kelas"
- Sistem akan otomatis mengarahkan ke detail kelas

---

## 📋 Struktur Database

### Tabel: users
```
- id (Primary Key)
- nama (String)
- email (String, Unique)
- password (String, Hashed)
- role (String: "siswa" atau "guru", default: "siswa")
```

### Tabel: kelas
```
- id (Primary Key)
- nama_kelas (String)
- deskripsi (Text)
- guru_id (Foreign Key -> users.id)
- kode_kelas (String, Unique)
- dibuat_pada (DateTime)
```

### Tabel: enrollments
```
- id (Primary Key)
- kelas_id (Foreign Key -> kelas.id)
- siswa_id (Foreign Key -> users.id)
- bergabung_pada (DateTime)
```

---

## 🔧 Setup & Instalasi

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Data (Opsional)
Untuk menambahkan data kelas dummy untuk testing:
```bash
python -m app.seed_data
```

Data yang ditambahkan:
- 1 Guru: Ibu Siti (guru@gestra.com / password123)
- 4 Kelas dengan kode yang berbeda

### 3. Jalankan Server
```bash
python -m uvicorn app.main:app --reload
```

Server akan berjalan di: `http://localhost:8000`

---

## 📝 Alur Penggunaan

### Untuk User Baru (Register)
1. Kunjungi `/register`
2. Isi form dengan nama, email, dan password
3. Klik tombol "Daftar"
4. Pilih role (siswa)
5. Akan otomatis login dan diarahkan ke beranda

### Untuk User yang Sudah Terdaftar (Login)
1. Kunjungi `/login`
2. Masukkan email dan password
3. Klik tombol "Masuk"
4. Akan diarahkan ke beranda

### Untuk Mengakses Kelas
1. Dari beranda, klik menu "Kelas" di navbar
2. Lihat daftar semua kelas
3. Pilih kelas yang ingin diikuti
4. Klik "Bergabung" atau gunakan kode kelas
5. Setelah bergabung, bisa melihat detail kelas

---

## 📁 Struktur File Baru

```
app/
├── models/
│   └── kelas.py          # Model: Kelas, Enrollment
├── routes/
│   └── kelas.py          # Route: endpoints kelas
├── schemas/
│   └── kelas.py          # Schema: KelasCreate, KelasResponse
├── services/
│   └── kelas.py          # Service: business logic kelas
├── static/css/
│   └── kelas.css         # Styling untuk halaman kelas
├── templates/
│   ├── daftar-kelas.html      # Halaman daftar kelas
│   ├── detail-kelas.html      # Halaman detail kelas
│   └── error.html             # Halaman error
└── seed_data.py          # Script untuk seed data
```

---

## 🔐 Keamanan

- ✅ Password di-hash menggunakan bcrypt
- ✅ Session menggunakan cookies (dapat ditingkatkan dengan JWT)
- ✅ Validasi input dengan Pydantic schemas
- ✅ User authentication check di setiap endpoint

---

## 🚧 Fitur untuk Pengembangan Selanjutnya

Berikut ini adalah fitur yang bisa dikembangkan ke depannya:

### 1. Fitur Guru
- [ ] Halaman untuk membuat kelas baru
- [ ] Edit/delete kelas
- [ ] Melihat daftar siswa di kelas
- [ ] Mengelola materi pembelajaran
- [ ] Membuat tugas dan kuis

### 2. Fitur Siswa Lanjutan
- [ ] Materi pembelajaran interaktif
- [ ] Tugas dan submission
- [ ] Quiz dengan scoring
- [ ] Diskusi/forum
- [ ] Notifikasi

### 3. Keamanan & Authentication
- [ ] JWT tokens (lebih aman dari cookies)
- [ ] Email verification untuk register
- [ ] Password reset
- [ ] Two-factor authentication (2FA)
- [ ] Rate limiting

### 4. UI/UX
- [ ] Dark mode
- [ ] Responsive design improvement
- [ ] Progressive Web App (PWA)
- [ ] Mobile app

### 5. Analytics & Reporting
- [ ] Laporan progress siswa
- [ ] Statistik penggunaan platform
- [ ] Grade tracking

---

## 📞 Endpoint Reference

### Authentication
- `GET /login` - Halaman login
- `POST /login` - Submit login
- `GET /register` - Halaman register
- `POST /register` - Submit register
- `GET /pilih-peran` - Halaman pilih role
- `POST /pilih-peran` - Submit pilih role
- `GET /logout` - Logout

### Kelas
- `GET /kelas/daftar` - Daftar semua kelas
- `GET /kelas/{kelas_id}/detail` - Detail kelas
- `POST /kelas/{kelas_id}/bergabung` - Bergabung kelas
- `POST /kelas/bergabung-kode` - Bergabung dengan kode

---

## 🐛 Troubleshooting

### Error: "Kode kelas tidak ditemukan"
- Pastikan kode kelas diketik dengan benar (case-insensitive)
- Cek apakah kelas dengan kode tersebut ada di database

### Error: "Email sudah terdaftar"
- Email sudah digunakan untuk akun lain
- Gunakan email yang berbeda atau gunakan fitur "lupa password"

### Error: "Belum ada kelas yang tersedia"
- Jalankan script seed_data untuk menambah data kelas dummy
- Atau admin/guru perlu membuat kelas baru

---

## 📄 Lisensi

Proyek ini adalah bagian dari Komputer Cerdas - Semester 6

---

Dibuat dengan ❤️ untuk platform pembelajaran GESTRA
