import secrets
import string
from sqlalchemy.orm import Session
from app.models.kelas import Kelas, Enrollment
from app.schemas.kelas import KelasCreate


def generate_kode_kelas():
    """Generate kode kelas unik (6 karakter alphanumeric)"""
    characters = string.ascii_uppercase + string.digits
    kode = ''.join(secrets.choice(characters) for _ in range(6))
    return kode


def get_all_kelas(db: Session):
    """Ambil semua kelas"""
    return db.query(Kelas).all()


def get_kelas_by_id(db: Session, kelas_id: int):
    """Ambil kelas berdasarkan ID"""
    return db.query(Kelas).filter(Kelas.id == kelas_id).first()


def get_kelas_by_kode(db: Session, kode_kelas: str):
    """Ambil kelas berdasarkan kode kelas"""
    return db.query(Kelas).filter(Kelas.kode_kelas == kode_kelas).first()


def create_kelas(db: Session, kelas: KelasCreate, guru_id: int):
    """Buat kelas baru"""
    kode = generate_kode_kelas()
    
    # Pastikan kode unik
    while db.query(Kelas).filter(Kelas.kode_kelas == kode).first():
        kode = generate_kode_kelas()
    
    db_kelas = Kelas(
        nama_kelas=kelas.nama_kelas,
        deskripsi=kelas.deskripsi,
        kode_kelas=kode,
        guru_id=guru_id
    )
    db.add(db_kelas)
    db.commit()
    db.refresh(db_kelas)
    return db_kelas


def get_kelas_by_siswa(db: Session, siswa_id: int):
    """Ambil semua kelas yang diikuti siswa"""
    return db.query(Kelas).join(Enrollment).filter(
        Enrollment.siswa_id == siswa_id
    ).all()


def siswa_bergabung_kelas(db: Session, kelas_id: int, siswa_id: int):
    """Siswa bergabung ke kelas"""
    # Check apakah sudah bergabung
    existing = db.query(Enrollment).filter(
        Enrollment.kelas_id == kelas_id,
        Enrollment.siswa_id == siswa_id
    ).first()
    
    if existing:
        return None  # Sudah bergabung
    
    enrollment = Enrollment(kelas_id=kelas_id, siswa_id=siswa_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def check_siswa_di_kelas(db: Session, kelas_id: int, siswa_id: int):
    """Cek apakah siswa sudah bergabung di kelas"""
    return db.query(Enrollment).filter(
        Enrollment.kelas_id == kelas_id,
        Enrollment.siswa_id == siswa_id
    ).first() is not None


def get_siswa_di_kelas(db: Session, kelas_id: int):
    """Ambil semua siswa di kelas"""
    return db.query(Enrollment).filter(Enrollment.kelas_id == kelas_id).all()


def keluar_kelas(db: Session, kelas_id: int, siswa_id: int):
    """Siswa keluar dari kelas"""
    enrollment = db.query(Enrollment).filter(
        Enrollment.kelas_id == kelas_id,
        Enrollment.siswa_id == siswa_id
    ).first()
    if enrollment:
        db.delete(enrollment)
        db.commit()
        return True
    return False

