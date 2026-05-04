# 📚 DATABASE SCHEMA & REFERENCE

Dokumentasi lengkap struktur database dan relasi antar table untuk sistem GESTRA.

---

## 🗄️ Database Overview

**Type**: SQLite (untuk development)  
**File**: `gestra.db` (di root project)  
**ORM**: SQLAlchemy  

---

## 📋 Table Specifications

### 1. `users` - Tabel User/Akun

**Purpose**: Menyimpan data akun user (siswa & guru)

**Columns**:
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nama            VARCHAR NOT NULL,
    email           VARCHAR UNIQUE NOT NULL INDEX,
    password        VARCHAR NOT NULL,
    role            VARCHAR DEFAULT 'siswa'
);
```

**Fields Detail**:
| Field | Type | Constraints | Deskripsi |
|-------|------|-------------|-----------|
| `id` | INTEGER | PRIMARY KEY, AUTO | ID unik user |
| `nama` | VARCHAR | NOT NULL | Nama lengkap user |
| `email` | VARCHAR | UNIQUE, INDEX | Email unik untuk login |
| `password` | VARCHAR | NOT NULL | Password di-hash bcrypt |
| `role` | VARCHAR | DEFAULT 'siswa' | Role: 'siswa' atau 'guru' |

**Sample Data**:
```
id | nama         | email              | password (hashed)        | role
1  | Ibu Siti     | guru@gestra.com    | $2b$12$xxxxxxxx...      | guru
2  | Budi Santoso | budi@test.com      | $2b$12$yyyyyyyy...      | siswa
```

---

### 2. `kelas` - Tabel Kelas

**Purpose**: Menyimpan data kelas/course

**Columns**:
```sql
CREATE TABLE kelas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_kelas      VARCHAR NOT NULL INDEX,
    deskripsi       TEXT,
    guru_id         INTEGER NOT NULL FOREIGN KEY REFERENCES users(id),
    kode_kelas      VARCHAR UNIQUE NOT NULL INDEX,
    dibuat_pada     DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Fields Detail**:
| Field | Type | Constraints | Deskripsi |
|-------|------|-------------|-----------|
| `id` | INTEGER | PRIMARY KEY, AUTO | ID unik kelas |
| `nama_kelas` | VARCHAR | NOT NULL, INDEX | Nama kelas |
| `deskripsi` | TEXT | - | Deskripsi/info kelas |
| `guru_id` | INTEGER | FOREIGN KEY | Reference ke users.id (guru) |
| `kode_kelas` | VARCHAR | UNIQUE, INDEX | Kode unik untuk bergabung |
| `dibuat_pada` | DATETIME | DEFAULT NOW | Timestamp pembuatan |

**Sample Data**:
```
id | nama_kelas                  | guru_id | kode_kelas | dibuat_pada
1  | Bahasa Indonesia Dasar      | 1       | BID001     | 2026-05-04
2  | Membaca dan Menulis Kreatif | 1       | MNK001     | 2026-05-04
3  | Literasi Digital            | 1       | LDG001     | 2026-05-04
4  | Pemahaman Teks Lanjutan     | 1       | PTL001     | 2026-05-04
```

---

### 3. `enrollments` - Tabel Enrollment (Siswa di Kelas)

**Purpose**: Relasi many-to-many antara siswa dan kelas (tracking siapa bergabung ke kelas apa)

**Columns**:
```sql
CREATE TABLE enrollments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kelas_id        INTEGER NOT NULL FOREIGN KEY REFERENCES kelas(id),
    siswa_id        INTEGER NOT NULL FOREIGN KEY REFERENCES users(id),
    bergabung_pada  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Fields Detail**:
| Field | Type | Constraints | Deskripsi |
|-------|------|-------------|-----------|
| `id` | INTEGER | PRIMARY KEY, AUTO | ID unik enrollment |
| `kelas_id` | INTEGER | FOREIGN KEY | Reference ke kelas.id |
| `siswa_id` | INTEGER | FOREIGN KEY | Reference ke users.id (siswa) |
| `bergabung_pada` | DATETIME | DEFAULT NOW | Timestamp bergabung |

**Sample Data**:
```
id | kelas_id | siswa_id | bergabung_pada
1  | 1        | 2        | 2026-05-04 14:30:00
2  | 2        | 2        | 2026-05-04 14:32:00
```

---

## 🔗 Relasi Database

### Entity Relationship Diagram (ERD)

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ nama            │
│ email (UNIQUE)  │
│ password        │
│ role            │
└─────────────────┘
         ▲
         │ 1 (guru)
         │
         │ N
┌─────────────────────┐
│      kelas          │
├─────────────────────┤
│ id (PK)             │
│ nama_kelas          │
│ deskripsi           │
│ guru_id (FK)────────┼──→ users.id
│ kode_kelas (UNIQUE) │
│ dibuat_pada         │
└─────────────────────┘
         ▲
         │ N
         │
    enrollments (join table)
         │
         │ M
         ▼
┌──────────────────────┐
│      users           │
│    (as siswa)        │
├──────────────────────┤
│ id (PK)              │
│ nama                 │
│ email (UNIQUE)       │
│ password             │
│ role = 'siswa'       │
└──────────────────────┘
```

### Relasi Descriptions

1. **One Guru to Many Kelas** (1:N)
   - 1 guru dapat membuat/mengajar multiple kelas
   - FK: `kelas.guru_id` → `users.id`

2. **Many Students to Many Classes** (M:N)
   - Banyak siswa dapat bergabung ke banyak kelas
   - Join table: `enrollments`
   - Composite: `(kelas_id, siswa_id)` should be unique

3. **One Class to Many Enrollments** (1:N)
   - 1 kelas dapat memiliki multiple siswa yang bergabung
   - FK: `enrollments.kelas_id` → `kelas.id`

---

## 🔍 Query Examples

### Find semua kelas yang diikuti siswa ID 2
```python
enrollments = db.query(Enrollment).filter(
    Enrollment.siswa_id == 2
).all()

kelas_ids = [e.kelas_id for e in enrollments]
kelas = db.query(Kelas).filter(Kelas.id.in_(kelas_ids)).all()
```

**Or (more efficient)**:
```python
kelas = db.query(Kelas).join(Enrollment).filter(
    Enrollment.siswa_id == 2
).all()
```

### Find semua siswa di kelas ID 1
```python
enrollments = db.query(Enrollment).filter(
    Enrollment.kelas_id == 1
).all()

siswa_ids = [e.siswa_id for e in enrollments]
siswa = db.query(User).filter(User.id.in_(siswa_ids)).all()
```

### Find kelas dengan kode 'BID001'
```python
kelas = db.query(Kelas).filter(
    Kelas.kode_kelas == 'BID001'
).first()
```

### Check apakah siswa 2 sudah bergabung ke kelas 1
```python
enrollment = db.query(Enrollment).filter(
    (Enrollment.siswa_id == 2) & (Enrollment.kelas_id == 1)
).first()

if enrollment:
    print("Sudah bergabung")
else:
    print("Belum bergabung")
```

---

## 📊 Data Integrity Constraints

### Primary Keys
- Setiap table memiliki `id` sebagai primary key
- Auto-increment dari database

### Foreign Keys
- `kelas.guru_id` → `users.id` (CASCADE DELETE)
- `enrollments.kelas_id` → `kelas.id` (CASCADE DELETE)
- `enrollments.siswa_id` → `users.id` (CASCADE DELETE)

### Unique Constraints
- `users.email` - Email harus unik (prevent duplikat akun)
- `kelas.kode_kelas` - Kode kelas harus unik
- `enrollments(kelas_id, siswa_id)` - Siswa tidak boleh bergabung 2x ke kelas yang sama

### NOT NULL Constraints
- `users.nama` - Nama harus diisi
- `users.email` - Email harus diisi
- `users.password` - Password harus diisi
- `kelas.nama_kelas` - Nama kelas harus diisi
- `kelas.guru_id` - Guru harus ditentukan
- `kelas.kode_kelas` - Kode kelas harus diisi

---

## 🔐 Security Considerations

### Password Storage
```python
# Password di-hash dengan bcrypt
from passlib.context import CryptContext
crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password saat simpan
hashed_pwd = crypt_context.hash(plain_password)

# Verify saat login
is_valid = crypt_context.verify(plain_password, hashed_pwd)
```

### Email Validation
```python
# Email di-validasi menggunakan Pydantic EmailStr
from pydantic import EmailStr

# Format email harus valid
email: EmailStr
```

### Session Management
```python
# User email disimpan di cookie setelah login
response.set_cookie(key="user_email", value=user.email)

# Diverifikasi di setiap request yang protected
user = get_user_by_email(db, request.cookies.get("user_email"))
```

---

## 📈 Performance Tips

### Indexing
- Kolom yang sering di-query harus di-index:
  - `users.email` ✅ (indexed)
  - `kelas.nama_kelas` ✅ (indexed)
  - `kelas.kode_kelas` ✅ (indexed - UNIQUE)

### Query Optimization
```python
# ❌ AVOID: N+1 query problem
for enrollment in enrollments:
    kelas = db.query(Kelas).filter(Kelas.id == enrollment.kelas_id).first()

# ✅ GOOD: Single query dengan join
kelas_list = db.query(Kelas).join(Enrollment).filter(
    Enrollment.siswa_id == siswa_id
).all()
```

### Eager Loading
```python
# SQLAlchemy relationships dengan lazy loading
from sqlalchemy.orm import joinedload

kelas = db.query(Kelas).options(
    joinedload(Kelas.guru),
    joinedload(Kelas.enrollments)
).first()
```

---

## 🔄 Migration Strategy

Untuk menambah fitur baru, berikut strategi perubahan database:

### Example: Tambah kolom `status` ke kelas

**1. Update Model** (`app/models/kelas.py`):
```python
class Kelas(Base):
    # ... existing columns ...
    status = Column(String, default="active")  # NEW
```

**2. Delete & Reseed**:
```bash
del gestra.db
py -m app.seed_data
```

**3. Update service jika perlu**:
```python
# Filter only active classes
kelas = db.query(Kelas).filter(Kelas.status == "active").all()
```

**4. Update template jika perlu**:
```html
{% if kelas.status == "active" %}
    <button>Bergabung</button>
{% endif %}
```

### For Production Use Alembic:
```bash
# Install
pip install alembic

# Init
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add status to kelas"

# Apply migration
alembic upgrade head
```

---

## 📋 Backup & Restore

### Backup Database
```bash
# SQLite - simple copy
copy gestra.db gestra.db.backup

# Or export to CSV
python -c "
import sqlite3
conn = sqlite3.connect('gestra.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
print(cursor.fetchall())
"
```

### Restore Database
```bash
# Restore dari backup
copy gestra.db.backup gestra.db
```

---

## 🧪 Testing Database Queries

### SQLite CLI
```bash
# Open database
sqlite3 gestra.db

# List tables
.tables

# Describe table
.schema users

# Query
SELECT * FROM users;
SELECT * FROM kelas;
SELECT * FROM enrollments;

# Exit
.quit
```

### Python Script
```python
from app.database import SessionLocal
from app.models.user import User
from app.models.kelas import Kelas, Enrollment

db = SessionLocal()

# Query users
users = db.query(User).all()
for user in users:
    print(f"{user.id}: {user.nama} ({user.email}) - {user.role}")

# Query kelas
kelas = db.query(Kelas).all()
for k in kelas:
    print(f"{k.id}: {k.nama_kelas} - {k.kode_kelas}")

# Query enrollments
enrollments = db.query(Enrollment).all()
for e in enrollments:
    print(f"Student {e.siswa_id} joined Class {e.kelas_id}")

db.close()
```

---

## 📞 Database Troubleshooting

### Issue: Duplicate Key Error
**Cause**: Email atau kode kelas sudah ada  
**Solution**: Use unique email/kode atau delete & reseed

### Issue: Foreign Key Constraint Fail
**Cause**: Reference ke record yang tidak ada  
**Solution**: Check guru_id atau kelas_id ada di parent table

### Issue: Database Locked
**Cause**: Multiple connections ke SQLite  
**Solution**: Close semua connections, restart server

---

*Database Schema Documentation - GESTRA v1.0*  
*Last Updated: 4 Mei 2026*
