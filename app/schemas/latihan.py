from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===== LATIHAN SCHEMAS =====
class LatihanBase(BaseModel):
    judul: str
    pertanyaan: str
    tipe_soal: str = "essay"
    tingkat_kesulitan: str = "mudah"


class LatihanCreate(LatihanBase):
    kelas_id: int
    pilihan_jawaban: Optional[str] = None
    jawaban_kunci: Optional[str] = None


class LatihanUpdate(BaseModel):
    judul: Optional[str] = None
    pertanyaan: Optional[str] = None
    tipe_soal: Optional[str] = None
    tingkat_kesulitan: Optional[str] = None
    pilihan_jawaban: Optional[str] = None
    jawaban_kunci: Optional[str] = None


class LatihanResponse(LatihanBase):
    id: int
    kelas_id: int
    guru_id: int
    dibuat_pada: datetime
    diupdate_pada: datetime

    class Config:
        from_attributes = True


# ===== JAWABAN SCHEMAS =====
class JawabanBase(BaseModel):
    jawaban: str


class JawabanCreate(JawabanBase):
    latihan_id: int


class JawabanUpdate(BaseModel):
    jawaban: Optional[str] = None
    benar: Optional[bool] = None
    nilai: Optional[int] = None


class JawabanResponse(JawabanBase):
    id: int
    latihan_id: int
    siswa_id: int
    kelas_id: int
    benar: bool
    nilai: int
    dikumpulkan_pada: datetime
    dikoreksi_pada: Optional[datetime] = None

    class Config:
        from_attributes = True
