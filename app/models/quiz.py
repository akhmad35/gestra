from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class QuizSession(Base):
    """Model untuk sesi kuis random/timer murid"""
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    siswa_id = Column(Integer, ForeignKey("users.id"), index=True)
    mode = Column(String, default="random")  # "random", "timer"
    total_soal = Column(Integer, default=10)
    benar_count = Column(Integer, default=0)
    salah_count = Column(Integer, default=0)
    skor_akhir = Column(Integer, default=0)
    waktu_mulai = Column(DateTime, default=datetime.utcnow)
    waktu_selesai = Column(DateTime, nullable=True)
    durasi_detik = Column(Integer, default=0)
    status = Column(String, default="ongoing")  # "ongoing", "finished"

    # Relationships
    siswa = relationship("User")
    details = relationship("QuizDetail", back_populates="session", cascade="all, delete-orphan")

class QuizDetail(Base):
    """Model untuk detail setiap soal dalam satu sesi kuis"""
    __tablename__ = "quiz_details"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("quiz_sessions.id"), index=True)
    nomor_soal = Column(Integer)
    target_char = Column(String)
    prediction = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    is_correct = Column(Boolean, default=False)
    waktu_jawab = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("QuizSession", back_populates="details")
