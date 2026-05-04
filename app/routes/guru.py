from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.kelas import get_kelas_by_id, get_all_kelas
from app.services.latihan import (
    create_latihan,
    get_latihan_by_kelas,
    get_latihan_by_id,
    update_latihan,
    delete_latihan,
    get_jawaban_by_latihan,
    grade_jawaban,
    get_stat_jawaban_kelas
)
from app.schemas.latihan import LatihanCreate, LatihanUpdate

router = APIRouter(prefix="/guru", tags=["Guru"])
templates = Jinja2Templates(directory="app/templates")


# ===== DASHBOARD GURU =====
@router.get("/dashboard", response_class=HTMLResponse)
async def guru_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard guru"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    # Ambil semua kelas yang dibuat guru
    from app.models.kelas import Kelas
    kelas_list = db.query(Kelas).filter(Kelas.guru_id == user.id).all()
    
    # Hitung statistik
    total_kelas = len(kelas_list)
    total_siswa = sum([len(k.enrollments) for k in kelas_list])
    
    # Ambil semua latihan
    from app.models.latihan import Latihan
    latihan_list = db.query(Latihan).filter(Latihan.guru_id == user.id).all()
    total_latihan = len(latihan_list)
    
    return templates.TemplateResponse(
        request=request,
        name="guru/dashboard.html",
        context={
            "user": user,
            "kelas_list": kelas_list,
            "total_kelas": total_kelas,
            "total_siswa": total_siswa,
            "total_latihan": total_latihan
        }
    )


# ===== MANAGE KELAS (GURU) =====
@router.get("/kelas/buat", response_class=HTMLResponse)
async def buat_kelas_page(request: Request, db: Session = Depends(get_db)):
    """Halaman buat kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/buat-kelas.html",
        context={"user": user}
    )


@router.post("/kelas/buat")
async def create_kelas_guru(
    request: Request,
    nama_kelas: str = Form(...),
    deskripsi: str = Form(...),
    db: Session = Depends(get_db)
):
    """Buat kelas baru (guru)"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    from app.services.kelas import create_kelas
    from app.schemas.kelas import KelasCreate
    
    kelas_data = KelasCreate(
        nama_kelas=nama_kelas,
        deskripsi=deskripsi,
        kode_kelas=""  # Will be generated
    )
    
    kelas = create_kelas(db, kelas_data, user.id)
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas.id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/kelas/{kelas_id}/detail", response_class=HTMLResponse)
async def detail_kelas_guru(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Detail kelas (guru view)"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Kelas tidak ditemukan"}
        )
    
    # Ambil latihan di kelas ini
    latihan_list = get_latihan_by_kelas(db, kelas_id)
    
    # Ambil siswa di kelas
    siswa_list = kelas.enrollments
    
    return templates.TemplateResponse(
        request=request,
        name="guru/detail-kelas.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan_list": latihan_list,
            "siswa_list": siswa_list
        }
    )


@router.get("/kelas/{kelas_id}/edit", response_class=HTMLResponse)
async def edit_kelas_page(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman edit kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/edit-kelas.html",
        context={"user": user, "kelas": kelas}
    )


@router.post("/kelas/{kelas_id}/edit")
async def update_kelas_guru(
    request: Request,
    kelas_id: int,
    nama_kelas: str = Form(...),
    deskripsi: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    kelas.nama_kelas = nama_kelas
    kelas.deskripsi = deskripsi
    db.add(kelas)
    db.commit()
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/kelas/{kelas_id}/delete")
async def delete_kelas_guru(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Delete kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    db.delete(kelas)
    db.commit()
    
    return RedirectResponse(url="/guru/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# ===== MANAGE LATIHAN (GURU) =====
@router.get("/latihan/buat/{kelas_id}", response_class=HTMLResponse)
async def buat_latihan_page(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman buat latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/buat-latihan.html",
        context={"user": user, "kelas": kelas}
    )


@router.post("/latihan/buat/{kelas_id}")
async def create_latihan_guru(
    request: Request,
    kelas_id: int,
    judul: str = Form(...),
    pertanyaan: str = Form(...),
    tipe_soal: str = Form(...),
    tingkat_kesulitan: str = Form(...),
    db: Session = Depends(get_db)
):
    """Buat latihan baru"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    latihan_data = LatihanCreate(
        kelas_id=kelas_id,
        judul=judul,
        pertanyaan=pertanyaan,
        tipe_soal=tipe_soal,
        tingkat_kesulitan=tingkat_kesulitan
    )
    
    latihan = create_latihan(db, latihan_data, user.id)
    
    return RedirectResponse(
        url=f"/guru/latihan/{latihan.id}/edit",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/latihan/{latihan_id}/edit", response_class=HTMLResponse)
async def edit_latihan_page(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Halaman edit latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/edit-latihan.html",
        context={"user": user, "latihan": latihan}
    )


@router.post("/latihan/{latihan_id}/update")
async def update_latihan_guru(
    request: Request,
    latihan_id: int,
    judul: str = Form(...),
    pertanyaan: str = Form(...),
    tipe_soal: str = Form(...),
    tingkat_kesulitan: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    latihan_update = LatihanUpdate(
        judul=judul,
        pertanyaan=pertanyaan,
        tipe_soal=tipe_soal,
        tingkat_kesulitan=tingkat_kesulitan
    )
    
    update_latihan(db, latihan_id, latihan_update)
    
    return RedirectResponse(
        url=f"/guru/kelas/{latihan.kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/latihan/{latihan_id}/delete")
async def delete_latihan_guru(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Delete latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    kelas_id = latihan.kelas_id
    delete_latihan(db, latihan_id)
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ===== LIHAT JAWABAN SISWA (GURU) =====
@router.get("/latihan/{latihan_id}/jawaban", response_class=HTMLResponse)
async def lihat_jawaban_latihan(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Lihat semua jawaban untuk latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    jawaban_list = get_jawaban_by_latihan(db, latihan_id)
    
    return templates.TemplateResponse(
        request=request,
        name="guru/jawaban-latihan.html",
        context={
            "user": user,
            "latihan": latihan,
            "jawaban_list": jawaban_list
        }
    )
