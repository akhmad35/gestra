from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Latihan(Base):
    """Model untuk soal/latihan yang dibuat guru"""
    __tablename__ = "latihan"

    id = Column(Integer, primary_key=True, index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id"), index=True)
    guru_id = Column(Integer, ForeignKey("users.id"), index=True)
    judul = Column(String, index=True)
    pertanyaan = Column(Text)
    tipe_soal = Column(String, default="essay")  # "essay", "pilihan_ganda", "isian", "handwriting_huruf", "handwriting_kata", "tebak_gambar"
    
    # Tambahan untuk integrasi sistem kelas
    metode_pembuatan = Column(String, default="manual")  # "manual", "random"
    dataset_type = Column(String, nullable=True)  # "huruf", "kata", "hewan", etc.
    jumlah_soal = Column(Integer, default=5)
    durasi_menit = Column(Integer, default=0) # 0 = tanpa batas
    waktu_mulai = Column(DateTime, nullable=True)
    waktu_selesai = Column(DateTime, nullable=True)
    status = Column(String, default="draft")  # "draft", "aktif", "selesai"
    soal_tergenerate = Column(Text, nullable=True)  # JSON list of questions
    
    # Tambahan untuk fitur Retry, Timer per Soal, dan Hasil
    izinkan_retry = Column(Boolean, default=False)
    max_attempt = Column(Integer, default=1)  # -1 = unlimited
    mode_timer = Column(String, default="total")  # "total", "per_soal"
    durasi_per_soal = Column(Integer, default=30)  # dalam detik
    izinkan_lihat_hasil = Column(Boolean, default=True)
    
    pilihan_jawaban = Column(Text, nullable=True)  # JSON format: {"A": "...", "B": "...", ...}
    jawaban_kunci = Column(Text, nullable=True)  # Jawaban yang benar
    tingkat_kesulitan = Column(String, default="mudah")  # "mudah", "sedang", "sulit"
    dibuat_pada = Column(DateTime, default=datetime.utcnow)
    diupdate_pada = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    kelas = relationship("Kelas")
    guru = relationship("User")
    jawaban_siswa = relationship("Jawaban", back_populates="latihan", cascade="all, delete-orphan")


class Jawaban(Base):
    """Model untuk jawaban siswa"""
    __tablename__ = "jawaban"

    id = Column(Integer, primary_key=True, index=True)
    latihan_id = Column(Integer, ForeignKey("latihan.id"), index=True)
    siswa_id = Column(Integer, ForeignKey("users.id"), index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id"), index=True)
    jawaban = Column(Text)
    benar = Column(Boolean, default=False)
    nilai = Column(Integer, default=0)  # 0-100
    attempts_count = Column(Integer, default=1)
    dikumpulkan_pada = Column(DateTime, default=datetime.utcnow)
    dikoreksi_pada = Column(DateTime, nullable=True)
    
    # Relationships
    latihan = relationship("Latihan", back_populates="jawaban_siswa")
    siswa = relationship("User")
    kelas = relationship("Kelas")
