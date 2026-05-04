"""
Script untuk membuat data kelas dan guru dummy untuk testing
Jalankan: python -m app.seed_data
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.kelas import Kelas
from app.services.auth import get_password_hash


def seed_data():
    """Seed database dengan data dummy"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_guru = db.query(User).filter(User.email == "guru@gestra.com").first()
        if existing_guru:
            print("Data sudah ada, skip seeding...")
            return
        
        # 1. Buat guru dummy
        guru1 = User(
            nama="Ibu Siti",
            email="guru@gestra.com",
            password=get_password_hash("password123"),
            role="guru"
        )
        db.add(guru1)
        db.flush()  # Flush untuk mendapatkan ID
        
        # 2. Buat kelas-kelas dummy
        kelas_data = [
            {
                "nama_kelas": "Bahasa Indonesia Dasar",
                "deskripsi": "Pelajari dasar-dasar bahasa Indonesia termasuk tata bahasa, kosakata, dan kemampuan membaca serta menulis yang fundamental.",
                "guru_id": guru1.id,
                "kode_kelas": "BID001"
            },
            {
                "nama_kelas": "Membaca dan Menulis Kreatif",
                "deskripsi": "Kelas interaktif untuk mengembangkan keterampilan membaca pemahaman dan menulis cerita kreatif dengan aplikasi GESTRA.",
                "guru_id": guru1.id,
                "kode_kelas": "MNK001"
            },
            {
                "nama_kelas": "Literasi Digital",
                "deskripsi": "Belajar menggunakan teknologi untuk meningkatkan kemampuan membaca dan menulis di era digital.",
                "guru_id": guru1.id,
                "kode_kelas": "LDG001"
            },
            {
                "nama_kelas": "Pemahaman Teks Lanjutan",
                "deskripsi": "Tingkatkan kemampuan menganalisis teks kompleks dan memahami makna tersirat dalam bacaan.",
                "guru_id": guru1.id,
                "kode_kelas": "PTL001"
            }
        ]
        
        for kelas_info in kelas_data:
            kelas = Kelas(
                nama_kelas=kelas_info["nama_kelas"],
                deskripsi=kelas_info["deskripsi"],
                guru_id=kelas_info["guru_id"],
                kode_kelas=kelas_info["kode_kelas"]
            )
            db.add(kelas)
        
        db.commit()
        print("✅ Data seed berhasil ditambahkan!")
        print(f"   - 1 Guru: {guru1.nama} ({guru1.email})")
        print(f"   - 4 Kelas")
        print("\nKode kelas yang bisa digunakan untuk bergabung:")
        for kelas_info in kelas_data:
            print(f"  - {kelas_info['kode_kelas']}: {kelas_info['nama_kelas']}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error saat seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
