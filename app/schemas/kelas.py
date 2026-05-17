from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KelasBase(BaseModel):
    nama_kelas: str
    deskripsi: Optional[str] = None
    kode_kelas: str


class KelasCreate(KelasBase):
    pass


class KelasResponse(KelasBase):
    id: int
    guru_id: int
    dibuat_pada: datetime

    class Config:
        from_attributes = True


class KelasDetail(KelasResponse):
    pass


class EnrollmentResponse(BaseModel):
    id: int
    siswa_id: int
    bergabung_pada: datetime

    class Config:
        from_attributes = True
