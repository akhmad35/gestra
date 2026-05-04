from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Kelas(Base):
    __tablename__ = "kelas"

    id = Column(Integer, primary_key=True, index=True)
    nama_kelas = Column(String, index=True)
    deskripsi = Column(Text)
    guru_id = Column(Integer, ForeignKey("users.id"))
    kode_kelas = Column(String, unique=True, index=True)
    dibuat_pada = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    guru = relationship("User")
    enrollments = relationship("Enrollment", back_populates="kelas", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id"))
    siswa_id = Column(Integer, ForeignKey("users.id"))
    bergabung_pada = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    kelas = relationship("Kelas", back_populates="enrollments")
    siswa = relationship("User")
