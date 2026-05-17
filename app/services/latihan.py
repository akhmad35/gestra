from sqlalchemy.orm import Session
from app.models.latihan import Latihan, Jawaban
from app.schemas.latihan import LatihanCreate, LatihanUpdate, JawabanCreate, JawabanUpdate


# ===== LATIHAN SERVICES =====

def create_latihan(db: Session, latihan: LatihanCreate, guru_id: int):
    """Buat latihan baru"""
    db_latihan = Latihan(
        kelas_id=latihan.kelas_id,
        guru_id=guru_id,
        judul=latihan.judul,
        pertanyaan=latihan.pertanyaan,
        tipe_soal=latihan.tipe_soal,
        tingkat_kesulitan=latihan.tingkat_kesulitan,
        metode_pembuatan=latihan.metode_pembuatan,
        dataset_type=latihan.dataset_type,
        jumlah_soal=latihan.jumlah_soal,
        durasi_menit=latihan.durasi_menit,
        waktu_mulai=latihan.waktu_mulai,
        waktu_selesai=latihan.waktu_selesai,
        status=latihan.status,
        soal_tergenerate=latihan.soal_tergenerate,
        pilihan_jawaban=latihan.pilihan_jawaban,
        jawaban_kunci=latihan.jawaban_kunci,
        izinkan_retry=latihan.izinkan_retry,
        max_attempt=latihan.max_attempt,
        mode_timer=latihan.mode_timer,
        durasi_per_soal=latihan.durasi_per_soal,
        izinkan_lihat_hasil=latihan.izinkan_lihat_hasil
    )
    db.add(db_latihan)
    db.commit()
    db.refresh(db_latihan)
    return db_latihan


def get_latihan_by_id(db: Session, latihan_id: int):
    """Ambil latihan berdasarkan ID"""
    return db.query(Latihan).filter(Latihan.id == latihan_id).first()


def get_latihan_by_kelas(db: Session, kelas_id: int):
    """Ambil semua latihan di kelas tertentu"""
    return db.query(Latihan).filter(Latihan.kelas_id == kelas_id).all()


def get_latihan_by_guru(db: Session, guru_id: int):
    """Ambil semua latihan yang dibuat guru"""
    return db.query(Latihan).filter(Latihan.guru_id == guru_id).all()


def update_latihan(db: Session, latihan_id: int, latihan_update: LatihanUpdate):
    """Update latihan"""
    db_latihan = get_latihan_by_id(db, latihan_id)
    if not db_latihan:
        return None
    
    update_data = latihan_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_latihan, key, value)
    
    db.add(db_latihan)
    db.commit()
    db.refresh(db_latihan)
    return db_latihan


def delete_latihan(db: Session, latihan_id: int):
    """Delete latihan"""
    db_latihan = get_latihan_by_id(db, latihan_id)
    if db_latihan:
        db.delete(db_latihan)
        db.commit()
        return True
    return False


# ===== JAWABAN SERVICES =====

def submit_jawaban(db: Session, jawaban: JawabanCreate, siswa_id: int, kelas_id: int):
    """Submit jawaban dari siswa (manual/text)"""
    # Check apakah sudah submit sebelumnya
    existing = db.query(Jawaban).filter(
        (Jawaban.latihan_id == jawaban.latihan_id) &
        (Jawaban.siswa_id == siswa_id)
    ).first()
    
    if existing:
        # Update jawaban sebelumnya
        existing.jawaban = jawaban.jawaban
        existing.attempts_count += 1
        existing.dikumpulkan_pada = datetime.utcnow()
        db.add(existing)
    else:
        # Buat jawaban baru
        db_jawaban = Jawaban(
            latihan_id=jawaban.latihan_id,
            siswa_id=siswa_id,
            kelas_id=kelas_id,
            jawaban=jawaban.jawaban,
            attempts_count=1
        )
        db.add(db_jawaban)
    
    db.commit()
    return get_jawaban_by_id(db, existing.id if existing else db_jawaban.id)


def submit_jawaban_otomatis(db: Session, latihan_id: int, siswa_id: int, kelas_id: int, jawaban: str, nilai: int, benar: bool):
    """Submit jawaban yang langsung dinilai (dari canvas/kuis)"""
    existing = db.query(Jawaban).filter(
        (Jawaban.latihan_id == latihan_id) &
        (Jawaban.siswa_id == siswa_id)
    ).first()
    
    if existing:
        existing.jawaban = jawaban
        existing.nilai = nilai
        existing.benar = benar
        existing.attempts_count += 1
        existing.dikoreksi_pada = datetime.utcnow()
        existing.dikumpulkan_pada = datetime.utcnow()
        db.add(existing)
    else:
        db_jawaban = Jawaban(
            latihan_id=latihan_id,
            siswa_id=siswa_id,
            kelas_id=kelas_id,
            jawaban=jawaban,
            nilai=nilai,
            benar=benar,
            attempts_count=1,
            dikoreksi_pada=datetime.utcnow()
        )
        db.add(db_jawaban)
    
    db.commit()
    return True


def get_jawaban_by_id(db: Session, jawaban_id: int):
    """Ambil jawaban berdasarkan ID"""
    return db.query(Jawaban).filter(Jawaban.id == jawaban_id).first()


def get_jawaban_siswa(db: Session, latihan_id: int, siswa_id: int):
    """Ambil jawaban siswa untuk latihan tertentu"""
    return db.query(Jawaban).filter(
        (Jawaban.latihan_id == latihan_id) &
        (Jawaban.siswa_id == siswa_id)
    ).first()


def get_jawaban_by_latihan(db: Session, latihan_id: int):
    """Ambil semua jawaban untuk latihan tertentu"""
    return db.query(Jawaban).filter(Jawaban.latihan_id == latihan_id).all()


def get_jawaban_by_siswa(db: Session, siswa_id: int, kelas_id: int):
    """Ambil semua jawaban siswa di kelas tertentu"""
    return db.query(Jawaban).filter(
        (Jawaban.siswa_id == siswa_id) &
        (Jawaban.kelas_id == kelas_id)
    ).all()


def grade_jawaban(db: Session, jawaban_id: int, benar: bool, nilai: int):
    """Grade jawaban siswa"""
    db_jawaban = get_jawaban_by_id(db, jawaban_id)
    if not db_jawaban:
        return None
    
    db_jawaban.benar = benar
    db_jawaban.nilai = nilai
    db_jawaban.dikoreksi_pada = datetime.utcnow()
    
    db.add(db_jawaban)
    db.commit()
    db.refresh(db_jawaban)
    return db_jawaban


def get_stat_jawaban_kelas(db: Session, kelas_id: int):
    """Get statistik jawaban di kelas"""
    jawaban_list = db.query(Jawaban).filter(Jawaban.kelas_id == kelas_id).all()
    
    total = len(jawaban_list)
    benar = len([j for j in jawaban_list if j.benar])
    rata_nilai = sum([j.nilai for j in jawaban_list]) / total if total > 0 else 0
    
    return {
        "total": total,
        "benar": benar,
        "rata_nilai": rata_nilai
    }


def get_all_jawaban_by_siswa(db: Session, siswa_id: int):
    """Ambil semua jawaban siswa dari semua kelas"""
    return db.query(Jawaban).filter(Jawaban.siswa_id == siswa_id).order_by(Jawaban.dikumpulkan_pada.desc()).all()


from datetime import datetime
